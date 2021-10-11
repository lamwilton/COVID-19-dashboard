import numpy as np
import pandas as pd
import time
import os
from urllib.request import Request, urlopen

"""
# County data growth rate and 7day average

Pull data from https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/
Merge cases and deaths, then compute growth rate of cases and deaths as well as 7day moving averages for each county
Outputs combined_usafacts.csv
"""
if __name__ == "__main__":
    start_time = time.time()
    req = Request("https://static.usafacts.org/public/data/covid-19/covid_confirmed_usafacts.csv?_ga=2.214028119.1303181313.1633970518-2063448721.1633809607")
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    content = urlopen(req)

    # Read both csvs and inner join
    cases_df = pd.read_csv(content)
    cases_df = cases_df.melt(id_vars=["countyFIPS", "County Name", "State", "StateFIPS"],
                             var_name="Date",
                             value_name="Cases")

    req = Request("https://static.usafacts.org/public/data/covid-19/covid_deaths_usafacts.csv?_ga=2.214028119.1303181313.1633970518-2063448721.1633809607")
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    content = urlopen(req)
    deaths_df = pd.read_csv(content)
    deaths_df = deaths_df.melt(id_vars=["countyFIPS", "County Name", "State", "StateFIPS"],
                               var_name="Date",
                               value_name="Deaths")
    deaths_df = deaths_df[['countyFIPS', 'Date', 'Deaths']]

    main_df = pd.merge(cases_df, deaths_df, "inner", on=['countyFIPS', 'Date'])
    main_df = main_df.rename(columns={'County Name': 'County_Name', 'StateFIPS': 'stateFIPS'})

    # Get list of FIPS and drop 0
    fips = main_df.countyFIPS.unique()
    fips = fips[1:]

    # Compute cases growth and death growth rates and 7day average for each county
    # Suppress warnings
    pd.options.mode.chained_assignment = None

    for i in range(0, len(fips)):
        temp_df = main_df[main_df.countyFIPS == fips[i]]
        temp_df['dxdt'] = temp_df['Cases'].diff().fillna(0)
        temp_df['rate'] = temp_df['Cases'].pct_change().fillna(0)
        temp_df['rate7day'] = temp_df['rate'].rolling(window=7).mean().fillna(0)
        temp_df['dydt'] = temp_df['Deaths'].diff().fillna(0)
        temp_df['rate_deaths'] = temp_df['Deaths'].pct_change().fillna(0)
        temp_df['rate_deaths7day'] = temp_df['rate_deaths'].rolling(window=7).mean().fillna(0)
        temp_df = temp_df.replace(np.inf, 0)
        temp_df = temp_df[temp_df['Date'] >= '2020-08-01']  # Trim data by date because too large
        if i == 0:
            new_df = temp_df
        else:
            new_df = pd.concat([new_df, temp_df])


    new_df.to_csv(os.path.join("output", "combined_usafacts.csv"), index=False)
    print("Total time: " + str(time.time() - start_time))
