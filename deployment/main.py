import polars as pl
import plotly.express as px
import dash, requests, json, plotly

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
    .group_by(["time_order", "Name", "Geo Place Name", "Time Period", "Measure Info"])
    .agg([
        pl.col("Data Value").mean().alias("avg_value"),
        pl.col("Data Value").quantile(0.95).alias("peak_value")
    ])
    .sort("time_order")
)

# Calculate year-over-year changes
trends_analysis = (trends
    .sort(["time_order", "Name", "Geo Place Name"])
    .with_columns([
        pl.col("avg_value").diff().over(["Name", "Geo Place Name"]).alias("value_change"),
        pl.col("avg_value").pct_change().over(["Name", "Geo Place Name"]).alias("pct_change")
    ])
)
ROLLING_MEAN = 13_800
# Plots trends and gets Gemini analysis
def plot(trends_data: pl.DataFrame, pollutant_name: str):
    gemini_data: pl.Series = trends_data.columns, trends_data["avg_value"].rolling_mean(window_size=ROLLING_MEAN).drop_nulls().round(2).to_list()

    fig = plot_trends(trends_data, pollutant_name)
    
    try:
        analysis = get_gemini_analysis(gemini_data, pollutant_name)
    except Exception as e:
        print(f"Error getting Gemini analysis: {e}")
        analysis = "Analysis unavailable"

    return (fig, analysis)

# Getting Gemini's analysis
def get_gemini_analysis(trends_data, pollutant_name: str):
    GEMINI_URL = f"""
    https://nova-motors-server.vercel.app/gemini?prompt=
Here's some data from an air quality dataset for New York City (it's the rolling mean of {ROLLING_MEAN} for avg_value)
for this pollutant: {pollutant_name}. The data: {trends_data[1]}. Provide easy-to-understand analysis. Be brief, honest, and precise. 
Assume the standard units for each pollutant. Provide some recommendations. ASSUME NO FURTHER INFORMATION; DON'T MENTION WANTING FURTHER INFORMATION. 
DON'T USE MARKDOWN, RESPOND WITH PLAIN TEXT.
    """
    response = requests.get(GEMINI_URL).json()
    analysis = response["candidates"][0]["content"]["parts"][0]["text"]

    return analysis

# Plotting the trends
# Plotting the trends with units
def plot_trends(trends_data: pl.DataFrame, pollutant_name: str):
    filtered = trends_data.filter(pl.col("Name") == pollutant_name)
    df = filtered.to_pandas()
    df = df.sort_values('time_order')
    time_periods = df.sort_values('time_order')['Time Period'].unique()

    measure = filtered["Measure Info"].unique().to_list()
    measure = measure[0] if len(measure) > 0 else None
    unit = measure if measure else ""

    fig = px.line(df, 
                  x="Time Period",
                  y="avg_value",
                  color="Geo Place Name",
                  title=f"Trends for {pollutant_name}")
    
    fig.update_layout(
        xaxis={
            'categoryorder': 'array',
            'categoryarray': time_periods
        },
        yaxis_title=f"Average Value/Mean ({unit})"
    )

    for trace in fig.data:
        trace.visible = "legendonly"
    
    fig.update_xaxes(tickangle=45)
    
    return fig

# Getting all the graphs
graph_names = [
    "Fine particles (PM 2.5)", "Asthma emergency department visits due to PM2.5", "Respiratory hospitalizations due to PM2.5 (age 20+)",
    "Cardiovascular hospitalizations due to PM2.5 (age 40+)", "Deaths due to PM2.5", "Ozone (O3)", "Asthma hospitalizations due to Ozone", 
    "Cardiac and respiratory deaths due to Ozone", "Asthma emergency departments visits due to Ozone", "Nitrogen dioxide (NO2)",
    "Boiler Emissions- Total NOx Emissions", "Boiler Emissions- Total PM2.5 Emissions", "Outdoor Air Toxics - Benzene", "Outdoor Air Toxics - Formaldehyde",
    "Boiler Emissions- Total SO2 Emissions", "Annual vehicle miles traveled (trucks)", "Annual vehicle miles traveled",
    "Annual vehicle miles traveled (cars)"
]

figures = []
for name in graph_names:
    figures.append(plot(trends_analysis, name))

# Setting up the Dash app
app = dash.Dash(__name__)

layout = dash.html.Div([
    dash.html.H1("New York AIRR Report", style={"color": "#04A777", "text-align": "center"}),
    dash.html.H2("Click on the legend to see all the values.", style={"color": "#81A4CD", "text-align": "center"}),
    dash.html.Div([
        dash.html.Div([
            dash.html.Div([
                dash.html.H3("Big Picture: ", style={"display": "inline-block", "margin-right": "10px", "vertical-align": "middle"}),
                dash.html.P(f"{figures[i][1]}", style={"display": "inline-block", "color": "#595758", "text-align": "center", "vertical-align": "middle"}),
                dash.dcc.Graph(id=f"graph-{i}", figure=figures[i][0])
            ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "padding": "10px"}),
            dash.html.Div([
                dash.html.H3("Big Picture: ", style={"display": "inline-block", "margin-right": "10px", "vertical-align": "middle"}),
                dash.html.P(f"{figures[i+1][1] if i+1 < len(figures) else 'No Analysis Available.'}", style={"display": "inline-block", "color": "#595758", "text-align": "center", "vertical-align": "middle"}),
                dash.dcc.Graph(id=f"graph-{i+1}", figure=figures[i+1][0] if i+1 < len(figures) else {})
            ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "padding": "10px"})
        ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-between", "gap": "20px"})  
        for i in range(0, len(figures), 2)
    ], style={"height": "100vh", "overflowY": "auto", "padding": "20px"})
])

app.layout = layout

layout_dict = layout.to_plotly_json()
with open("layout.json", "w", encoding="UTF-8") as f:
    json.dump(layout_dict, f, cls=plotly.utils.PlotlyJSONEncoder)