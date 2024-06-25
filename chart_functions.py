
import pandas as pd
import plotly.express as px
from prompts import chart_creator_prompt
from utils import extract_column_names,download_csv
from urllib.parse import urlparse
import os

from langchain_core.tools import tool
from typing import Annotated
from utils import execute_query,write_headings_to_csv,write_rows_to_csv,extract_column_names
from typing_extensions import TypedDict
from prompts import prompt, chart_creator_prompt
from langgraph.graph.message import AnyMessage, add_messages
import csv
import psycopg2
from typing import Annotated
import requests
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import ToolMessage

from langgraph.prebuilt import ToolNode

from langgraph.graph.message import AnyMessage, add_messages

import re
from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

azure_key="43acd730f49d47b494589ffefa5028fa"
api_base = "https://askauraopenai.openai.azure.com/"
api_version = "2024-02-01"

llm = AzureChatOpenAI(deployment_name="chat",
                      openai_api_key=azure_key,
                      azure_endpoint=api_base,
                      api_version=api_version,
                      streaming=True)



@tool
def create_bar_chart(csv_file_name:str,chart_title:str,x_axis:str,y_axis:str,group_by:str):
    """Create a bar chart.

    Args:
    chart_title (str) : Title of the chart
    x_axis (str) : x axis value
    y_axis (str) : y axis value
    group_by (str) : value to be counted or grouped by

    """
    
    
    if group_by is not None:
    
        data = pd.read_csv(csv_file_name,encoding='latin-1')

        # Count the number of people by age
        counts = data[group_by].value_counts().reset_index()
        counts.columns = [x_axis, y_axis]

        # Create a bar chart
        fig = px.bar(counts, x=x_axis, y=y_axis, title=chart_title)
        fig.write_html("chart.html")

        return "chart URL - http://exampleurl.com/"
    
@tool
def create_pie_chart(csv_file_name:str,chart_title:str,group_by:str):
    """Create a pie chart

    Args:
        chart_title (str) : Title of the chart
        group_by (str) : value to be counted or grouped by

    """
    
    data = pd.read_csv(csv_file_name,encoding='latin-1')

    counts = data[group_by].value_counts().reset_index()
    counts.columns = [group_by, 'Value']

# Create a pie chart
    fig = px.pie(counts, values='Value', names=group_by, title=chart_title)
    fig.write_html("chart.html")

    return "chart URL - http://exampleurl.com/"


@tool
def create_line_chart(csv_file_name:str,chart_title:str,x_axis:str,y_axis:str):
    """
    Create a line chart

    Args:
        chart_title (str) : Title of the chart
        x_axis (str) : x axis value
        y_axis (str) : y axis value
    """
    data = pd.read_csv(csv_file_name,encoding='latin-1')
    fig = px.line(data, x=x_axis, y=y_axis, title=chart_title)
    fig.write_html("chart.html")

    return "chart URL - http://exampleurl.com/"
    


tools=[create_bar_chart,create_line_chart,create_pie_chart]
llm_with_tools= llm.bind_tools(tools)



def chart_creator(user_request,csv_file_url):
    parsed_url = urlparse(csv_file_url)
    file_path= os.path.basename(parsed_url.path)
    col_names= extract_column_names(file_path)


    messages = [SystemMessage(chart_creator_prompt.format(columns=col_names,csv_file_path=file_path)),HumanMessage(user_request)]
    ai_msg = llm_with_tools.invoke(messages)
    
    
    for tool_call in ai_msg.tool_calls:
        print(tool_call["name"], "tool is called with args :",tool_call["args"])
        selected_tool = {item.name: item for item in tools}[tool_call["name"].lower()]
        tool_output = selected_tool.invoke(tool_call["args"])
        return tool_output

res= chart_creator("create a chart that shows number of poeple by risk category","https://devbeekle.blob.core.windows.net/reports/74902eb4f7f8490cb5a1e97adb275e30.csv")