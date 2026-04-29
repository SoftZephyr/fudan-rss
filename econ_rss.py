import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta
import time
import random


def get_econ_content(session, detail_url):
    """进入详情页提取正文并清洗格式"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://econ.fudan.edu.cn/xwzx/tzgg.htm"
    }
    try:
        # 模拟真人阅读，随机延迟
        time.sleep(random.uniform(1.0, 2.0))
        res = session.get(detail_url, headers=headers, timeout=25)
        res.encoding = 'utf-8'  # 强制编码，防止乱码

        soup = BeautifulSoup(res.text, 'html.parser')

        # 根据你提供的源码，锁定最核心的正文容器
        content_div = soup.select_one('.zhengwen .v_news_content') or \
                      soup.select_one('.v_news_content') or \
                      soup.select_one('#vsb_content_500') or \
                      soup.select_one('.zhengwen')

        if content_div:
            # 1. 清理冗余标签和样式
            for s in content_div(['script', 'style']):
                s.decompose()

            # 移除所有标签自带的 style 属性，防止手机端显示问题
            for tag in content_div.find_all(True):
                if tag.has_attr('style'):
                    del tag['style']

            # 2. 修正链接与图片路径
            for tag in content_div.find_all(['img', 'a']):
                attr = 'src' if tag.name == 'img' else 'href'
                val = tag.get(attr)
                if val:
                    if val.startswith('/'):
                        tag[attr] = "https://econ.fudan.edu.cn" + val
                    elif val.startswith('..'):
                        # 递归清理路径中的 ../
                        clean_path = val.replace('../', '')
                        tag[attr] = "https://econ.fudan.edu.cn/" + clean_path

            return content_div.decode_contents()
    except Exception as e:
        print(f"Detail Error: {detail_url} -> {e}")
    return "点击原文链接查看正文详情。"


def generate_econ_rss():
    list_url = "https://econ.fudan.edu.cn/xwzx/tzgg.htm"
    beijing_tz = timezone(timedelta(hours=8))
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("--- 开始生成经济学院 RSS ---")
    try:
        res = session.get(list_url, headers=headers, timeout=20)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        items_data = []
        # 直接定位你截图中的 li.clearfix
        news_list = soup.select('li.clearfix')

        for li in news_list:
            a_tag = li.find('a')
            date_span = li.find('span', class_='date')

            if a_tag and date_span:
                href = a_tag.get('href')
                # 处理相对路径
                if href.startswith('../'):
                    full_link = "https://econ.fudan.edu.cn/" + href.replace('../', '')
                elif href.startswith('/'):
                    full_link = "https://econ.fudan.edu.cn" + href
                else:
                    full_link = href

                title = a_tag.text.strip()
                date_text = date_span.text.strip()

                items_data.append({
                    'title': title,
                    'link': full_link,
                    'date': date_text
                })

        # 日期升序排列（为了让 FeedGenerator 顺序添加后，最新的在最前）
        items_data.sort(key=lambda x: x['date'], reverse=False)

        fg = FeedGenerator()
        fg.id(list_url)
        fg.title('复旦经济学院 - 通知公告')
        fg.link(href=list_url, rel='alternate')
        fg.description('复旦大学经济学院通知公告实时订阅')
        fg.language('zh-CN')

        # 处理最近 15 条
        for item in items_data[-15:]:
            print(f"抓取正文中: {item['title']}")
            content = get_econ_content(session, item['link'])

            fe = fg.add_entry()
            fe.id(item['link'])
            fe.title(item['title'])
            fe.link(href=item['link'])
            fe.content(content, type='html')

            try:
                dt = datetime.strptime(item['date'], '%Y-%m-%d')
                fe.pubDate(dt.replace(hour=12, minute=0, tzinfo=beijing_tz))
            except:
                fe.pubDate(datetime.now(beijing_tz))

        # 保存文件
        fg.rss_file('fudan_econ.xml')
        print(f"--- 成功！已生成 fudan_econ.xml ---")

    except Exception as e:
        print(f"Main Error: {e}")


if __name__ == "__main__":
    generate_econ_rss()