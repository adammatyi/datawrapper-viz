import numpy as np
import pandas as pd
import ssl

import pycountry

ssl._create_default_https_context = ssl._create_stdlib_context


def get_country_code(country_name):
    try:
        return f":{pycountry.countries.search_fuzzy(country_name)[0].alpha_2.lower()}: {country_name}"
    except LookupError:
        return country_name


url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)_per_capita"
site = pd.read_html(url, index_col=0, na_values='—')
gdp_per_capita = site[1]
flat_columns = ['_'.join(col).strip() for col in gdp_per_capita.columns.values]
gdp_per_capita.columns = flat_columns
gdp_per_capita['gdp_latest'] = np.where(pd.to_numeric(gdp_per_capita.iloc[:, 0], errors='coerce').notna(),
                           pd.to_numeric(gdp_per_capita.iloc[:, 0], errors='coerce'),
                           gdp_per_capita.iloc[:, 2])
gdp_per_capita = gdp_per_capita[['gdp_latest']].copy()

url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(PPP)_per_capita"
site = pd.read_html(url, index_col=0, na_values='—')
gdp_at_ppp_per_capita = site[1]
gdp_at_ppp_per_capita.index = gdp_at_ppp_per_capita.index.str.replace('\u202f*', '')
flat_columns = ['_'.join(col).strip() for col in gdp_at_ppp_per_capita.columns.values]
gdp_at_ppp_per_capita.columns = flat_columns
gdp_at_ppp_per_capita['gdp_ppp_latest'] = np.where(pd.to_numeric(gdp_at_ppp_per_capita.iloc[:, 0], errors='coerce').notna(),
                           pd.to_numeric(gdp_at_ppp_per_capita.iloc[:, 0], errors='coerce'),
                           gdp_at_ppp_per_capita.iloc[:, 2])
gdp_at_ppp_per_capita = gdp_at_ppp_per_capita[['gdp_ppp_latest']].copy()

# https://worldpopulationreview.com/country-rankings/minimum-wage-by-country
url = "https://en.wikipedia.org/wiki/List_of_countries_by_minimum_wage"
site = pd.read_html(url, index_col=0, na_values='—')
min_wage = site[1]
flat_columns = ['_'.join(col).strip() for col in min_wage.columns.values]
min_wage.columns = flat_columns
min_wage = min_wage.iloc[:, [1,2,4,5]]
min_wage.columns = ["min_wage_ann_nominal", "min_wage_ann_ppp", "min_wage_h_nominal", "min_wage_h_ppp"]

url = "https://en.wikipedia.org/wiki/List_of_countries_by_average_wage"
site = pd.read_html(url, index_col=0, na_values='—')
avg_wage_oecd = site[0]
avg_wage_oecd.index = avg_wage_oecd.index.str.replace('\u202f*', '')
avg_wage_unece = site[1]
avg_wage_unece.index = avg_wage_unece.index.str.replace('\u202f*', '')
avg_wage_oecd['avg_wage_oecd'] = avg_wage_oecd.ffill(axis=1).iloc[:, -1]
avg_wage_oecd = avg_wage_oecd.iloc[:, [4]]
avg_wage_unece = avg_wage_unece.iloc[:, [0]]
avg_wage_unece.columns = ["avg_wage_unece"]


url = "https://en.wikipedia.org/wiki/Incentives_for_Olympic_medalists_by_country"
site = pd.read_html(url, index_col=0, na_values='—')
olympic_prize = site[1]
olympic_prize.index = olympic_prize.index.str.replace('Chinese Taipei (Taiwan)', 'Taiwan')
olympic_prize.index = olympic_prize.index.str.replace('Great Britain', 'United Kingdom')

for column in ["Gold", "Silver", "Bronze"]:
    try:
        olympic_prize[column] = olympic_prize[column].replace('[\$,]', '', regex=True)
        olympic_prize[column] = olympic_prize[column].replace('\(.*\)', '', regex=True)
        olympic_prize[column] = pd.to_numeric(olympic_prize[column], errors='coerce')
    except ValueError as ve:
        print(f"Failed to parse column {column}")
        print(ve)
        continue

merged = olympic_prize.join(gdp_per_capita, lsuffix='_prize', rsuffix='_gdp')
merged = merged.join(gdp_at_ppp_per_capita, lsuffix='_prize', rsuffix='_gdp_ppp')
merged = merged.join(min_wage, lsuffix='_prize', rsuffix='_min_wage')
merged = merged.join(avg_wage_oecd, lsuffix='_prize', rsuffix='_avg_wage_oecd')
merged = merged.join(avg_wage_unece, lsuffix='_prize', rsuffix='_avg_wage_unece')
for column in ["Gold", "Silver", "Bronze", 'gdp_latest', 'gdp_ppp_latest', "min_wage_ann_nominal", "min_wage_ann_ppp", "min_wage_h_nominal", "min_wage_h_ppp", 'avg_wage_oecd', "avg_wage_unece"]:
    try:
        merged[column] = merged[column].replace('[\$,]', '', regex=True)
        merged[column] = merged[column].replace('\(.*\)', '', regex=True).astype(float)
    except ValueError as ve:
        print(f"Failed to parse column {column}")
        print(ve)
        continue

merged["avg_wage_annual"] = merged['avg_wage_oecd'].combine_first(merged['avg_wage_unece'] * 12)
colum_names_formatted = ["Gold medal prize", "Silver medal prize", "Bronze medal prize", "Note", "GDP per capita (latest)", "GDP(PPP) per capita (latest)", "Annual minimum wage(USD)", "Annual minimum wage at PPP(USD)", "Hourly minimum wage(USD)", "Hourly minimum wage at PPP(USD)", "Annual average wage (OECD)", "Monthly average wage (UNECE)", "Annual average wage"]
merged.columns = colum_names_formatted

merged["Years of GDP per capita for gold prize"] = merged["Gold medal prize"] / merged["GDP per capita (latest)"]
merged["Years to work for gold prize on minimum wage"] = merged["Gold medal prize"] / merged["Annual minimum wage(USD)"]
merged["Years to work for gold prize on average wage"] = merged["Gold medal prize"] / merged["Annual average wage"]
merged.index = merged.index.str.replace('Turkey', 'Türkiye')
merged.index = merged.index.map(get_country_code)

merged.to_csv("merged_stats.csv")

url = "https://en.wikipedia.org/wiki/The_Economist_Democracy_Index"
site = pd.read_html(url, index_col=2, na_values='—', match="Norway", header=0, encoding='utf-8')
dem_index = site[1]
dem_index = dem_index.iloc[:, [2, 3, 5, 6, 7, 8, 9,]]
dem_index.columns = dem_index.columns.str.replace('\xad', '')

url = "https://en.wikipedia.org/wiki/List_of_countries_by_inequality-adjusted_Human_Development_Index"
site = pd.read_html(url, index_col=1, encoding='utf-8')
hdi = site[2]
hdi = hdi.iloc[:, [1, 2]]
hdi.columns = ["IHDI", "HDI"]

merged = olympic_prize.join(dem_index, lsuffix='', rsuffix='_dem_index')
merged = merged.join(hdi, lsuffix='', rsuffix='_hdi')
prize_col = merged.iloc[:, 0]
stats_cols = merged.iloc[:, -9:]
merged = pd.concat([prize_col, stats_cols], axis=1)
merged.to_csv("merged_dem_stats.csv")
