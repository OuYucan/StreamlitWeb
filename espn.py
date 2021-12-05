import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
import re
import os
import warnings
try:
    from sqlalchemy import create_engine
    from bs4 import BeautifulSoup
    import requests
except ModuleNotFoundError:
    os.system("pip install sqlalchemy")
    os.system("pip install bs4")
    os.system("pip install requests")
finally:
    from sqlalchemy import create_engine
    from bs4 import BeautifulSoup
    import requests
    from api_espn_table import get_table
    from get_news_data import update_local_news


warnings.filterwarnings("ignore")

engine = create_engine(
    "mysql+pymysql://{}:{}@{}:{}/{}".format('henry_ou', 'Henry13579#', 'rm-bp1l17jtj994580o08o.mysql.rds.aliyuncs.com',
                                            '3306', 'web-data'))
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
}
session = requests.session()
html_dst = "resource/html"
if not os.path.exists(html_dst):
    os.makedirs(html_dst)


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


def WriteFile(filename, content):
    with open(filename, 'ab+') as f:
        if isinstance(content, str):
            content = bytes(content, encoding='utf-8')
        f.write(content)


# 设置网页
st.set_page_config(page_title="ESPN新闻大屏", page_icon="☀️", layout="wide")


@st.cache(allow_output_mutation=True)
def get_data_from_local():
    # 获取espn足球新闻
    # news = pd.read_sql_query("SELECT * from espn_soccer_news", con=engine)
    news = pd.read_json("soccer_news.json", orient="records")
    unique_news = news.drop_duplicates(subset=['key'])

    # 获取球队信息
    # teams = pd.read_sql("soccer_teams", con=engine)
    teams = pd.read_json("soccer_teams.json", orient="records")

    # 根据球队id和新闻id去重
    unique_teams = teams.drop_duplicates(subset=['key', 'id'])
    right_df = unique_news.loc[:, 'key img href summary'.split()]

    # 合并新闻和球队信息
    merge_team = pd.merge(left=unique_teams, right=right_df, on='key')
    merge_team['team'] = merge_team['team'].apply(lambda x: x.replace('-', ' ').title())
    return merge_team


data = get_data_from_local()

# 侧边栏
st.sidebar.header("请在这里筛选:")
if st.sidebar.button("更新本地新闻文件"):
    update_local_news()
    st.success("更新完成！")

today = datetime.today().date()
select_date = st.sidebar.date_input(
    "选择新闻的最早日期",
    value=today + timedelta(days=-14),
    max_value=today,
    help=f"新闻内容区间默认最近两周"
)

select_team = st.sidebar.multiselect(
    "选择球队:",
    options=data["team"].unique(),
    default=['Barcelona', 'Real Madrid', 'Bayern Munich', 'Manchester City',
             'Paris Saint Germain']
)

c1, c2 = st.sidebar.columns(2)
with c1:
    ps = c1.number_input(
        "每页显示新闻数",
        value=20,
        min_value=20,
        max_value=100,
        step=20,
        format="%d"
    )
    ps = int(ps)

with c2:
    pn = c2.number_input(
        "当前页数",
        min_value=1,
        value=1,
        max_value=10,
        format="%d"
    )
    pn = int(pn)

# 积分榜
country = {
    "英超": "eng",
    "法甲": "fra",
    "西甲": "esp",
    "德甲": "ger",
    "意甲": "ita",
}
with st.expander("显示积分榜"):
    selected = st.selectbox(
        "选择联赛积分榜",
        index=0,
        options=["英超", "法甲", "西甲", "德甲", "意甲", ]
    )
    df = get_table(country.get(selected))
    st.dataframe(df)

start_date = str(select_date)
# data['art_date'] = data['art_time'].apply(lambda x:str(x)[:10])
# select_teams = data.query('team == @select_team and art_date >= @start_date')
# 条件筛选
select_teams = data.query('team == @select_team and art_time >= @start_date')

# 按最新时间排序
select_teams.sort_values("art_time", ascending=False, inplace=True)

# 重置索引
select_teams.index = [i for i in range(select_teams.shape[0])]

# 合并新闻标签
select_teams['id'] = select_teams['id'].astype(str)
key_team = select_teams.loc[:, ['key', 'team', 'id']]
team_concat = key_team.groupby('key').apply(lambda x: " | ".join(x['team'])).to_dict()
id_concat = key_team.groupby('key').apply(lambda x: " | ".join(x['id'])).to_dict()  # 合并新闻id
select_teams['id'] = select_teams['key'].apply(lambda x: id_concat.get(x))  # 替换id和team
select_teams['team'] = select_teams['key'].apply(lambda x: team_concat.get(x))

# 删除重复新闻的key
select_teams.drop_duplicates(subset="key", inplace=True, keep='first')
st.sidebar.write(f"数据规模：{select_teams.shape}")

# 显示新闻
show_scale = select_teams.iloc[(pn - 1) * ps:pn * ps]  # 按页筛选
dict_list = list(show_scale.to_dict(orient='index').values())

for news_index, row in enumerate(dict_list, start=1 + (pn - 1) * ps):
    st.markdown('------')
    news_type = "story"
    if "/report" in row['href']:
        news_type = "game"
    elif "/video/" in row['href']:
        news_type = "video"
    icon = {
        "story": "📖",
        "game": "⚽",
        "video": "📺",
    }

    st.markdown(f"<h2>{icon.get(news_type, '📖')} {news_index}. <a href={row['href']}>{row['title']}</a></h2>",
                unsafe_allow_html=True)
    pic_col, detail_col = st.columns([1, 3])
    with pic_col:
        team = f"https://a1.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/{row['id']}.png" \
            f"&h=100&w=100"
        st.image(row['img'], )

    with detail_col:
        if row['summary']:
            st.markdown(f"<h3>{row['summary']}</h3>",
                        unsafe_allow_html=True)

        st.markdown(f"<span class='art_time'>{row['art_time']}</span> | "
                    f"<span class='team'>{row['team']} </span>", unsafe_allow_html=True)

    if news_type != "video":

        if st.button(f"{row['key']}", ):
            content = None
            with st.expander(f"{row['href']}"):
                content = get_html_content(row['href'], row['title'])
                st.markdown(content, unsafe_allow_html=True)
                WriteFile("history.txt", f"visit_time: {str(datetime.now())} | url: {row['href']}\n")

        # left_col, right_col = st.columns(2)
        if st.button("下载html", key=f"html_{row['key']}"):
            content = get_html_content(row['href'], row['title']) + "<hr>"
            WriteFile(os.path.join(html_dst, f"{datetime.now().date()}.html"), content)

        if st.button("收藏", key=f"like_{row['key']}",):
            WriteFile("like.txt", f"visit_time: {str(datetime.now())} | url: {row['href']}\n")

        # MainMenu {visibility: hidden;} header {visibility: hidden;}
# 隐藏streamlit默认格式信息
hide_st_style = """
            <style>
            footer {visibility: hidden;}
            a{text-decoration: none;}
            .team {color:#f63366; text-indent: 1em;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
