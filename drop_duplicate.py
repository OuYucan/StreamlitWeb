import pandas as pd
from sqlalchemy import create_engine
engine = create_engine(
    "mysql+pymysql://{}:{}@{}:{}/{}".format('henry_ou', 'Henry13579#',
                                            'rm-bp1l17jtj994580o08o.mysql.rds.aliyuncs.com',
                                            '3306', 'web-data'))

news_df = pd.read_sql("espn_soccer_news",con=engine)
print(news_df.shape)
news_df.drop_duplicates(subset=['key'],inplace=True)
news_df.sort_values(by='art_time', ascending=False, inplace=True)
print(news_df.shape)
print(news_df.head())
news_df.to_sql("espn_soccer_news",con=engine, index=False, if_exists='replace')


# =========================
teams_df = pd.read_sql("espn_soccer_teams",con=engine)
print(teams_df.shape)
teams_df.drop_duplicates(subset=['key','id'],inplace=True)
teams_df.sort_values(by='art_time', ascending=False, inplace=True)
print(teams_df.shape)
print(teams_df.head())
teams_df.to_sql("espn_soccer_teams",con=engine, index=False, if_exists='replace')

