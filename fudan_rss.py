import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta
import time


def get_content(detail_url):
    """进入二级页面抓取正文"""
    try:
        res = requests.get(detail_url, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        # 寻找复旦教务处正文所在的 div，通常是 wp_articlecontent
        content_div = soup.find('div', class_='wp_articlecontent')
        if content_div:
            return str(content_div)  # 返回 HTML 字符串，保留排版
        return "点击原文查看详情"
    except:
        return "内容抓取失败"


def generate_fudan_rss():
    url = "https://jwc.fudan.edu.cn/gzdt/list.htm"
    headers = {"User-Agent": "Mozilla/5.0"}
    beijing_tz = timezone(timedelta(hours=8))

    response = requests.get(url, headers=headers)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table', width="100%", cellspacing="0")

    fg = FeedGenerator()
    fg.id(url)
    fg.title('复旦教务处 - 工作动态')
    fg.link(href=url, rel='alternate')
    fg.description('支持全文预览的复旦教务处订阅源')
    fg.language('zh-CN')

    seen_links = set()

    # 我们按网页顺序抓取，通常网页顶端是最新的
    for table in tables:
        a_tag = table.find('a')
        date_td = table.find('td', class_='ti')

        if a_tag and date_td:
            link = "https://jwc.fudan.edu.cn" + a_tag.get('href')
            if link in seen_links: continue
            seen_links.add(link)

            title = a_tag.get('title')
            date_str = date_td.text.strip()

            print(f"正在抓取全文: {title}...")
            # --- 关键改动：抓取正文 ---
            content = get_content(link)

            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            fe.content(content, type='html')  # 把抓到的 HTML 塞进 RSS

            dt = datetime.strptime(date_str, '%Y-%m-%d')
            fe.pubDate(dt.replace(tzinfo=beijing_tz))

            # 稍微停顿一下，防止抓取过快被服务器屏蔽
            time.sleep(0.5)

    fg.rss_file('fudan_jwc.xml')
    print("✅ 升级版 RSS 已生成")


if __name__ == "__main__":
    generate_fudan_rss()