import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Read the csv file
df = pd.read_csv('test.csv')

# Create a dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    dcc.Graph(id='graph'),
])

# Callback to update the graph
@app.callback(
    Output('graph', 'figure'),
    [Input('graph', 'id')]
)
def update_graph(id):
    # Create a chart using plotly
    fig = px.histogram(df, x='risk_category', nbins=50, title='Number of People Based on Risk Category')
    fig.update_xaxes(title='Risk Category')
    fig.update_yaxes(title='Number of People')
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8500)