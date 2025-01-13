import dash
from dash import html
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def read_html_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

app.layout = html.Div([
    html.H1("Multiple HTML Figures"),
    dbc.Row([
        dbc.Col(html.Iframe(srcDoc=read_html_file(f'figure{i}.html'), style={'width': '100%', 'height': '400px'}), 
                width=6, className='mb-4')
        for i in range(6)
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
