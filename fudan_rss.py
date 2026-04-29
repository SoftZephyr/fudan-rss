import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta


def generate_fudan_rss():
    # 使用 9397 路径
    list_url = "https://jwc.fudan.edu.cn/9397/list.htm"
    beijing_tz = timezone(timedelta(hours=8))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://jwc.fudan.edu.cn/"
    }

    print(f"正在同步复旦教务处通知索引...")
    try:
        res = requests.get(list_url, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')

        items_data = []
        seen_links = set()

        # 获取所有带 page.htm 的详情链接
        links = soup.select('a[href*="page.htm"]')

        for a in links:
            href = a.get('href')
            full_link = "https://jwc.fudan.edu.cn" + href if href.startswith('/') else href
            # 1. 彻底清洗链接去重
            clean_link = full_link.split('?')[0]

            title = a.get('title') or a.text.strip()

            # 过滤杂质链接
            if len(title) < 6 or "javascript" in href:
                continue

            if clean_link not in seen_links:
                seen_links.add(clean_link)

                # 2. 提取日期
                date_text = ""
                row = a.find_parent('tr')
                if row:
                    date_td = row.select_one('.ti')
                    if date_td:
                        date_text = date_td.text.strip()

                if not date_text:
                    date_text = datetime.now().strftime('%Y-%m-%d')

                items_data.append({
                    'title': title,
                    'link': clean_link,
                    'date': date_text
                })

        # 【核心修正】: 强制按日期从“新到旧”排序
        # 这样写入 XML 时，4月29日的消息会排在文件最前面
        items_data.sort(key=lambda x: x['date'], reverse=True)

        fg = FeedGenerator()
        fg.id(list_url)
        fg.title('复旦教务处 - 动态提醒')
        fg.link(href=list_url, rel='alternate')
        fg.description('教务处通知索引。提示：部分正文需登录 UIS 查看。')
        fg.language('zh-CN')

        # 3. 按排好的顺序逐条写入（前 20 条）
        for item in items_data[:20]:
            fe = fg.add_entry()
            fe.id(item['link'])
            fe.title(item['title'])
            fe.link(href=item['link'])
            fe.description(f"📅 发布日期：{item['date']}<br/>⚠️ 查看详情需点击标题跳转。")

            try:
                dt = datetime.strptime(item['date'], '%Y-%m-%d')
                fe.pubDate(dt.replace(tzinfo=beijing_tz))
            except:
                fe.pubDate(datetime.now(beijing_tz))

        # 4. 生成文件
        fg.rss_file('fudan_jwc.xml')
        print(f"✅ RSS 任务已完成，最新条目已置顶。")

    except Exception as e:
        print(f"❌ 运行异常: {e}")


if __name__ == "__main__":
    generate_fudan_rss()