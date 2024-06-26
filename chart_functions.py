
import pandas as pd
import plotly.express as px
from prompts import chart_creator_prompt
from utils import extract_column_names,download_csv
from urllib.parse import urlparse
import os
from langchain_core.tools import tool
from utils import extract_column_names, get_blob_url, upload_to_blob
from prompts import chart_creator_prompt

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages



llm = AzureChatOpenAI(deployment_name=os.getenv("DEPLOYMENT_NAME"),
                      openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                      azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                      api_version=os.getenv("OPENAI_API_VERSION"),
                      streaming=True)



@tool
def create_bar_chart(csv_file_name:str,chart_title:str,x_axis:str,y_axis:str,group_by:str=None):
    """Create a bar chart.

    Args:
    chart_title (str) : Title of the chart
    x_axis (str) : x axis value
    y_axis (str) : y axis value
    group_by (str) : value to be counted or grouped by if required

    """
    data = pd.read_csv(csv_file_name,encoding='latin-1')
 
    
    if group_by is not None:
    

        # Count the number of people by age
        counts = data[group_by].value_counts().reset_index()
        counts.columns = [x_axis, y_axis]

        # Create a bar chart
        fig = px.bar(counts, x=x_axis, y=y_axis, title=chart_title)

    else:
        fig = px.bar(data, x=x_axis, y=y_axis, title=chart_title)

    chart_file_path = csv_file_name.rsplit('.', 1)[0]+".html"
    fig.write_html(chart_file_path)
    print(chart_file_path," is created")

    blob_name=chart_file_path
    upload_to_blob(file_path=chart_file_path,blob_name=blob_name)
    blob_url = get_blob_url(blob_name)

    return blob_url

    
@tool
def create_pie_chart(csv_file_name:str,chart_title:str,values:str,label:str,group_by:str=None):
    """Create a pie chart

    Args:
        chart_title (str) : Title of the chart
        group_by (str, optional) : value to be counted or grouped by if required
        values (str) : value that determines the size of each slice in the pie chart.
        label (str) : label for slices in the pie chart

    """
    
    data = pd.read_csv(csv_file_name,encoding='latin-1')

    if group_by is not None:

        counts = data[group_by].value_counts().reset_index()
        counts.columns = [group_by, 'Value']


        fig = px.pie(counts, values=values, names=group_by, title=chart_title)

    else:
        fig = px.pie(data, values=values, names=label, title=chart_title)

    chart_file_path = csv_file_name.rsplit('.', 1)[0]+".html"
    fig.write_html(chart_file_path)
    print(chart_file_path," is created")

    blob_name=chart_file_path
    upload_to_blob(file_path=chart_file_path,blob_name=blob_name)
    blob_url = get_blob_url(blob_name)

    return blob_url


@tool
def create_line_chart(csv_file_name:str,chart_title:str,x_axis:str,y_axis:str):
    """
    Create a line chart

    Args:
        chart_title (str) : Title of the chart
        x_axis (str) : x axis value
        y_axis (str) : y axis value

    Returns:
        str : URL of the created chart
    """
    data = pd.read_csv(csv_file_name,encoding='latin-1')
    fig = px.line(data, x=x_axis, y=y_axis, title=chart_title)
    chart_file_path = csv_file_name.rsplit('.', 1)[0]+".html"
    fig.write_html(chart_file_path)
    print(chart_file_path," is created")

    blob_name=chart_file_path
    upload_to_blob(file_path=chart_file_path,blob_name=blob_name)
    blob_url = get_blob_url(blob_name)

    return blob_url
    


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

