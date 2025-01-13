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


if __name__ == '__main__':
    app.run_server(debug=True)
