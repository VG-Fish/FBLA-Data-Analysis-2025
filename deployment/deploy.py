import json, dash

app = dash.Dash(__name__)

with open("layout.json", "r") as f:
    layout_dict = json.load(f)

app.layout = dash.html.Div.from_plotly_json(layout_dict)

server = app.server
