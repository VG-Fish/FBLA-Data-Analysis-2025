import polars as pl
import plotly.express as px
import dash, json

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

time_order = """2005
2005-2007
Winter 2008-09
Summer 2009
Annual Average 2009
Winter 2009-10
Summer 2010
2-Year Summer Average 2009-2010
Annual Average 2010
2010
Winter 2010-11
Summer 2011
2009-2011
Annual Average 2011
2011
Winter 2011-12
Summer 2012
Annual Average 2012
Winter 2012-13
Summer 2013
Annual Average 2013
2013
Winter 2013-14
Summer 2014
2012-2014
Annual Average 2014
2014
Winter 2014-15
Summer 2015
Annual Average 2015
2015
Winter 2015-16
Summer 2016
Annual Average 2016
Winter 2016-17
Summer 2017
2015-2017
Annual Average 2017
Winter 2017-18
Summer 2018
Annual Average 2018
Winter 2018-19
Summer 2019
2017-2019
Annual Average 2019
2019
Winter 2019-20
Summer 2020
Annual Average 2020
Winter 2020-21
Summer 2021
Annual Average 2021
Winter 2021-22
Summer 2022
Annual Average 2022
""".splitlines()

time_mappings = {time_order[time]: time for time in range(len(time_order))}

# Add time_order column for sorting
sorted_data = data.with_columns(
    pl.col("Time Period").replace(time_mappings, return_dtype=pl.UInt8).alias("time_order")
).sort("time_order")

# Group by time period and location
trends = (sorted_data
    .group_by(["time_order", "Name", "Geo Place Name", "Time Period"])
    .agg([
        pl.col("Data Value").mean().alias("avg_value"),
        pl.col("Data Value").quantile(0.95).alias("peak_value")
    ])
    .sort("time_order")
)

# Calculate year-over-year changes
trends_analysis = (trends
    .sort(["time_order", "Name", "Geo Place Name", "Time Period"])
    .with_columns([
        pl.col("avg_value").diff().over(["Name", "Geo Place Name"]).alias("value_change"),
        pl.col("avg_value").pct_change().over(["Name", "Geo Place Name"]).alias("pct_change")
    ])
)

# Ensure x-axis categories are sorted in chronological order using time_order
def plot_trends(trends_data: pl.DataFrame, pollutant_name: str):
    # Filter the data for the given pollutant
    filtered = trends_data.filter(pl.col("Name") == pollutant_name)
    
    # Convert the filtered data to pandas
    df = filtered.to_pandas()

    # Ensure the data is sorted by 'time_order'
    df = df.sort_values('time_order')

    # Extract sorted 'Time Period' values based on 'time_order'
    time_periods = df.sort_values('time_order')['Time Period'].unique()

    # Create the line plot using Plotly
    fig = px.line(df, 
                  x="Time Period",
                  y="avg_value",
                  color="Geo Place Name",
                  title=f"Trends for {pollutant_name}")
    
    # Set custom sorting order for x-axis
    fig.update_layout(
        xaxis={
            'categoryorder': 'array',
            'categoryarray': time_periods
        },
        updatemenus=[
            {
                'buttons': [
                    {
                        'label': 'Select All',
                        'method': 'update',
                        'args': [{'visible': [True] * len(df['Geo Place Name'].unique())}]
                    },
                    {
                        'label': 'Deselect All',
                        'method': 'update',
                        'args': [{'visible': [False] * len(df['Geo Place Name'].unique())}]
                    }
                ],
                'direction': 'down',
                'showactive': False,
            }
        ]
    )
    
    # Rotate x-axis labels for readability
    fig.update_xaxes(tickangle=45)
    
    return fig

# List of pollutants to visualize
pollutants = [
    "Fine particles (PM 2.5)", "Ozone (O3)", "Nitrogen dioxide (NO2)",
    "Boiler Emissions- Total NOx Emissions", "Boiler Emissions- Total PM2.5 Emissions",
    "Boiler Emissions- Total SO2 Emissions"
]

# Generate figures for each pollutant
figures = []
for pollutant in pollutants:
    figures.append(plot_trends(trends_analysis, pollutant))

# Set up the Dash app
app = dash.Dash(__name__)

layout = dash.html.Div([
    dash.html.Div([
        dash.html.Div([
            dash.dcc.Graph(
                id=f"graph-{i}",
                figure=figures[i],
                style={"width": "50%", "display": "inline-block"}
            ),
            dash.dcc.Graph(
                id=f"graph-{i+1}",
                figure=figures[i+1] if i+1 < len(figures) else {},
                style={"width": "50%", "display": "inline-block"}
            )
        ])
        for i in range(0, len(figures), 2)
    ], style={"height": "100vh", "overflowY": "scroll"})
])
app.layout = layout

if __name__ == "__main__":
    app.run_server(debug=True)