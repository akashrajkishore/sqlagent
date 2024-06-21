

import pandas as pd
import plotly.express as px

# Read the csv file
df = pd.read_csv('test.csv')

# Group by 'risk_category' and count the number of 'person_id'
grouped_df = df.groupby('risk_category')['person_id'].count().reset_index()

# Create the bar chart
fig = px.bar(grouped_df, x='risk_category', y='person_id', labels={'person_id':'Number of People', 'risk_category':'Risk Category'}, title='Number of People Based on Risk Category')

fig.show()
