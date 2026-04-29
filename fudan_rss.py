import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta


def generate_fudan_rss():
    # 1. 配置目标 URL 和请求头
    url = "https://jwc.fudan.edu.cn/gzdt/list.htm"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # 2. 发送请求并解析网页
        print("正在抓取复旦教务处数据...")
        response = requests.get(url, headers=headers)
        response.encoding = response.apparent_encoding  # 自动处理中文编码

        soup = BeautifulSoup(response.text, 'html.parser')

        # 根据你提供的源码，通知条目在这些 table 标签中
        tables = soup.find_all('table', width="100%", cellspacing="0")

        # 3. 初始化 RSS 生成器
        fg = FeedGenerator()
        fg.id(url)
        fg.title('复旦教务处 - 工作动态')
        fg.author({'name': 'Fudan JWC RSS Bot'})
        fg.link(href=url, rel='alternate')
        fg.description('由 Python 脚本自动生成的复旦教务处工作动态订阅源')
        fg.language('zh-CN')

        # 4. 提取数据并填入 RSS
        seen_links = set()  # 用于去重
        beijing_tz = timezone(timedelta(hours=8))  # 定义东八区时区

        for table in tables:
            a_tag = table.find('a')
            date_td = table.find('td', class_='ti')

            if a_tag and date_td:
                # 提取链接并补全
                link = "https://jwc.fudan.edu.cn" + a_tag.get('href')

                # 去重逻辑：如果已经处理过这个链接，就跳过
                if link in seen_links:
                    continue
                seen_links.add(link)

                title = a_tag.get('title')
                date_str = date_td.text.strip()

                # 创建 RSS 条目
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title)
                fe.link(href=link)

                # 处理带时区的日期
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    fe.pubDate(dt.replace(tzinfo=beijing_tz))
                except ValueError:
                    # 如果日期格式解析失败，使用当前时间
                    fe.pubDate(datetime.now(beijing_tz))

        # 5. 生成 XML 文件
        output_file = 'fudan_jwc.xml'
        fg.rss_file(output_file)
        print(f"✅ 成功！已在当前目录生成: {output_file}")
        print(f"共处理 {len(seen_links)} 条通知。")

    except Exception as e:
        print(f"❌ 程序运行失败: {e}")


if __name__ == "__main__":
    generate_fudan_rss()