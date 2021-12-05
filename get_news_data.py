import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from sqlalchemy import create_engine
import pymysql

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
}

engine = create_engine(
    "mysql+pymysql://{}:{}@{}:{}/{}".format('henry_ou', 'Henry13579#',
                                            'rm-bp1l17jtj994580o08o.mysql.rds.aliyuncs.com',
                                            '3306', 'web-data'))
session = requests.session()


def get_soup(url):
    res = session.get(url=url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup


def get_html_content(url, title=None):
    """
    获取网页内容
    :param url: 链接
    :param title: 标题
    :return:
    """
    soup = get_soup(url)
    if "/report?gameId" in url:
        selectors = soup.select_one("#article-feed > div > article > div > "
                                    "div.article-body")
    else:
        selectors = soup.select_one("#article-feed > article:nth-child(1) > "
                                    "div > div.article-body")
    if not selectors:
        return ""

    content = [f"<h1>{title}</h1>"]
    for i in selectors:
        if i.name in ['ul', 'aside', 'hr', 'video9']:
            continue
        if i.name == 'div' and i.select_one("div.contentItem__contentWrapper"):
            children = str(i.findChildren())
            pattern = re.compile(u'data-srcset="(.*?)".*?(<h1.*?</h1>).*?(<p.*?</p>)')
            img1 = "<img src='{}' > \n{} {}".format(*pattern.search(children).groups())
            content.append(img1)
            continue
        content.append(str(i))
    return "\n".join(content)


def get_news():
    df = pd.read_sql("espn_soccer_news", con=engine)
    df.to_json("soccer_news.json", orient="records")


def get_teams():
    df = pd.read_sql("espn_soccer_teams", con=engine)
    df.to_json("soccer_teams.json", orient="records")


def get_teams3():
    db, cursor = get_db_cursor()
    values = query_rows(cursor, "SELECT * from espn_soccer_teams")
    values = query_rows(cursor, "select name from syscolumns where id=object_id('espn_soccer_teams') ")
    return values #pd.read_sql("espn_soccer_teams", con=engine)


def get_db_cursor():
    # 获取数据库的配置
    db_config = {
        "host": "rm-bp1l17jtj994580o08o.mysql.rds.aliyuncs.com",
        "port": 3306,
        "user": "henry_ou",
        "passwd": "Henry13579#",
        "database": "web-data",
        "charset": "utf8mb4"
    }
    # 创建与数据库的连接
    db = pymysql.connect(**db_config)
    # 创建游标对象cursor
    cursor = db.cursor()
    return db, cursor


def query_rows(cursor, sql):
    """
    查询语句获取多行数据
    :param sql:

    :return:
    """
    try:
        cursor.execute(sql)
        # 获取所有数据
        rows_all = cursor.fetchall()  # 获取多行数据
        return rows_all
    except Exception as e:
        pass
    finally:
        # 关闭游标
        cursor.close()


def update_local_news():
    get_news()
    get_teams()


if __name__ == '__main__':
    update_local_news()