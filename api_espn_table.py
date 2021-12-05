import pandas as pd


def get_table(country, year=None) -> pd.DataFrame:
    # tables = pd.read_html("https://www.espn.com/soccer/standings/_/league/eng.1/season/2021")
    url = f"https://www.espn.com/soccer/standings/_/league/{country}.1/"
    if year:
        url += f"season/{year}"
    tables = pd.read_html(url)

    teams = tables[0]
    season = teams.columns[0]
    teams.columns = ['team']
    left_table = teams['team'].str.extract("(\d+)([A-Z]{3})(.*?)$")
    left_table.columns = ['rank', 'short_name', 'team']
    col_map = {"GP": "Games Played",
               "W": "Wins",
               "D": "Draws",
               "L": "Losses",
               "F": "Goals For",
               "A": "Goals Against",
               "GD": "Goal Difference",
               "P": "Points"}
    concat = pd.concat([left_table, tables[1]], axis=1)
    concat = concat.rename(col_map, axis=1)
    concat['season'] = season
    return concat
