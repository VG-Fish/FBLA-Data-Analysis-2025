import polars as pl
import plotly.express as px
import dash


# Load CSV
data = pl.read_csv("Air_Quality.csv")

# Cleaning up the data.
# NOTE: There are no nulls in the data.
data = data.with_columns([
    pl.col("Start_Date").str.to_date("%m/%d/%Y").alias("Start_Date"),
])

"""
All the unique 'names' we can find in the "Names" Column:

Annual vehicle miles traveled (trucks)
Annual vehicle miles traveled
Asthma emergency department visits due to PM2.5
Asthma hospitalizations due to Ozone
Boiler Emissions- Total NOx Emissions
Boiler Emissions- Total PM2.5 Emissions
Outdoor Air Toxics - Benzene
Outdoor Air Toxics - Formaldehyde
Boiler Emissions- Total SO2 Emissions
Annual vehicle miles traveled (cars)
Respiratory hospitalizations due to PM2.5 (age 20+)
Cardiovascular hospitalizations due to PM2.5 (age 40+)
Deaths due to PM2.5
Cardiac and respiratory deaths due to Ozone
Asthma emergency departments visits due to Ozone
Ozone (O3)
Nitrogen dioxide (NO2)
Fine particles (PM 2.5)
"""

time_mappings = {
    "2005": 0,
    "2005-2007": 1,
    "Winter 2008-09": 2,
    "Annual Average 2009": 3,
    "Summer 2009": 4,
    "Winter 2009-10": 5,
    "2009-2011": 6,
    "2-Year Summer Average 2009-2010": 7,
    "Annual Average 2010": 8,
    "Summer 2010": 9,
    "Winter 2010-11": 10,
    "2010": 11,
    "Annual Average 2011": 12,
    "Summer 2011": 13,
    "Winter 2011-12": 14,
    "2011": 15,
    "Annual Average 2012": 16,
    "Summer 2012": 17,
    "Winter 2012-13": 18,
    "2012-2014": 19,
    "Annual Average 2013": 20,
    "Summer 2013": 21,
    "Winter 2013-14": 22,
    "2013": 23,
    "Annual Average 2014": 24,
    "Summer 2014": 25,
    "Winter 2014-15": 26,
    "2014": 27,
    "Annual Average 2015": 28,
    "Summer 2015": 29,
    "Winter 2015-16": 30,
    "2015": 31,
    "2015-2017": 32,
    "Annual Average 2016": 33,
    "Summer 2016": 34,
    "Winter 2016-17": 35,
    "Annual Average 2017": 36,
    "Summer 2017": 37,
    "Winter 2017-18": 38,
    "2017-2019": 39,
    "Annual Average 2018": 40,
    "Summer 2018": 41,
    "Winter 2018-19": 42,
    "Annual Average 2019": 43,
    "Summer 2019": 44,
    "Winter 2019-20": 45,
    "Annual Average 2020": 46,
    "Summer 2020": 47,
    "Winter 2020-21": 48,
    "Annual Average 2021": 49,
    "Summer 2021": 50,
    "Winter 2021-22": 51,
    "Annual Average 2022": 52,
    "Summer 2022": 53,
}

# Group by time period and location
trends = data.group_by(["Name", "Geo Place Name", "Time Period"]).agg([
    pl.col("Data Value").mean().alias("avg_value"),
    pl.col("Data Value").quantile(0.95).alias("peak_value")
])

# Calculate year-over-year changes
trends_analysis = (trends
    .sort(['Name', 'Geo Place Name', 'Time Period'])
    .with_columns([
        pl.col('avg_value').diff().over(['Name', 'Geo Place Name']).alias('value_change'),
        pl.col('avg_value').pct_change().over(['Name', 'Geo Place Name']).alias('pct_change')
    ])
)

# Visualize trends
def plot_trends(trends_data: pl.DataFrame, pollutant_name: str):
    filtered = trends_data.filter(pl.col('Name') == pollutant_name).to_pandas()
    fig = px.line(filtered, 
                  x='Time Period',
                  y='avg_value',
                  color='Geo Place Name',
                  title=f'Trends for {pollutant_name}')
    return fig

pollutants = [
    "Fine particles (PM 2.5)", "Ozone (O3)", "Nitrogen dioxide (NO2)",
    "Boiler Emissions- Total NOx Emissions", "Boiler Emissions- Total PM2.5 Emissions",
    "Boiler Emissions- Total SO2 Emissions"
]

figures = []
for pollutant in pollutants:
    figures.append(plot_trends(trends_analysis, pollutant))

app = dash.Dash(__name__)

app.layout = dash.html.Div([
    dash.html.Div([
        dash.html.Div([
            dash.dcc.Graph(
                id=f'graph-{i}',
                figure=figures[i],
                style={'width': '50%', 'display': 'inline-block'}
            ),
            dash.dcc.Graph(
                id=f'graph-{i+1}',
                figure=figures[i+1] if i+1 < len(figures) else {},
                style={'width': '50%', 'display': 'inline-block'}
            )
        ])
        for i in range(0, len(figures), 2)
    ], style={'height': '100vh', 'overflowY': 'scroll'})
])


# if __name__ == '__main__':
#     app.run_server(debug=True)