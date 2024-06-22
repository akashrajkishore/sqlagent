import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html

# Read the CSV file
df = pd.read_csv('test.csv')

# Count the number of people based on risk category
risk_category_counts = df['risk_category'].value_counts()

# Create a DataFrame for the plot
plot_df = pd.DataFrame({'risk_category': risk_category_counts.index, 'count': risk_category_counts.values})

# Create a plotly figure
fig = px.bar(plot_df, x='risk_category', y='count', title='Number of People Based on Risk Category')

# Create a Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    dcc.Graph(
        id='risk-category-graph',
        figure=fig
    )
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8500)