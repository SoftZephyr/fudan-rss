import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta


def generate_fudan_rss():
    list_url = "https://jwc.fudan.edu.cn/9397/list.htm"
    beijing_tz = timezone(timedelta(hours=8))

    # 定义“噪音”黑名单，如果标题包含这些词或者是这些特定标题，就跳过
    noise_titles = ["复旦大学书院教育", "更多", "返回首页", "联系我们"]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        res = requests.get(list_url, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')

        items_data = []
        seen_links = set()
        links = soup.select('a[href*="page.htm"]')

        for a in links:
            href = a.get('href')
            clean_link = ("https://jwc.fudan.edu.cn" + href if href.startswith('/') else href).split('?')[0]
            title = (a.get('title') or a.text).strip()

            # --- 过滤逻辑开始 ---
            # 1. 过滤掉黑名单中的标题
            if title in noise_titles:
                continue
            # 2. 过滤掉太短的标题
            if len(title) < 6:
                continue
            # 3. 如果链接里包含 c25337 (书院教育的特征)，也剔除掉
            if "c25337" in clean_link:
                continue
            # 4. 去重
            if clean_link in seen_links:
                continue
            # --- 过滤逻辑结束 ---

            seen_links.add(clean_link)

            date_text = ""
            row = a.find_parent('tr')
            if row:
                date_td = row.select_one('.ti')
                if date_td:
                    date_text = date_td.text.strip()

            items_data.append({
                'title': title,
                'link': clean_link,
                'date': date_text if date_text else datetime.now().strftime('%Y-%m-%d')
            })

        # 保持之前的正确排序：旧到新写入，使阅读器端呈现新到旧
        items_data.sort(key=lambda x: x['date'], reverse=False)

        fg = FeedGenerator()
        fg.id(list_url)
        fg.title('复旦教务处 - 工作动态')
        fg.link(href=list_url, rel='alternate')
        fg.description('教务处通知索引。')
        fg.language('zh-CN')

        for item in items_data:
            fe = fg.add_entry()
            fe.id(item['link'])
            fe.title(item['title'])
            fe.link(href=item['link'])
            fe.description(f"📅 发布日期：{item['date']}")

            dt = datetime.strptime(item['date'], '%Y-%m-%d')
            fe.pubDate(dt.replace(hour=12, minute=0, tzinfo=beijing_tz))

        fg.rss_file('fudan_jwc.xml')
        print("✅ 噪音已剔除，RSS 已更新。")

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    generate_fudan_rss()