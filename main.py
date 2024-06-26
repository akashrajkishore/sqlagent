
from langchain_core.tools import tool
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.runnables import RunnableLambda, Runnable, RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
import uuid
from langgraph.prebuilt import ToolNode
from typing import Annotated
from typing import Literal
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition
import requests
from langchain_openai import AzureChatOpenAI
from langchain_core.messages.ai import AIMessage
import re
from dotenv import load_dotenv
import os
from fastapi import FastAPI
from pydantic import BaseModel

from chart_functions import chart_creator
from utils import execute_query,write_headings_to_csv,write_rows_to_csv, get_blob_url, upload_to_blob
from prompts import prompt


load_dotenv()

#------------------------------------------------------------------------------------------------------------------------------Tools
@tool
def get_data_from_database_and_create_report(sql_query:str)->str:
    """ A tool that will fetch data from the database using the SQL query and use it to create a document file. Returns the URL of the created file."""
    
   
    task = uuid.uuid4().hex
    csv_file=f"{task}.csv"
    output = execute_query(sql_query)
    col_names = output[0]  # First item in the tuple
    data = output[1]  # Second item in the tuple
    
    write_headings_to_csv(csv_file,col_names)
    write_rows_to_csv(csv_file,data)
   
    
    # Upload to blob:
    blob_name = csv_file
    upload_to_blob(file_path=csv_file,blob_name=blob_name)
    blob_url = get_blob_url(blob_name)


    return blob_url


@tool
def get_sql_query(user_request:str)->str:
    """Get an SQL query to fulfill the user's request. Returns an SQL query if the operation is successful. 
    Args:
        user_request (str) : The user's request

    Returns:
        str : An SQL query
    """

    url = os.getenv("DATABEE-ENGINE-URL")
    
    data = {
        "finetuning_id": "",
        "evaluate": False,
        "metadata": {},
        "prompt": {
            "text": user_request,
            "db_connection_id": os.getenv("DB-CONNECTION_ID"),
            "metadata": {}
        },
        "low_latency_mode": False
    }

    response = requests.post(url, json=data)

    if response.status_code == 201:
        print("Status Code:", response.status_code)
        
        response_json = response.json()

        sql_query = response_json.get('sql')
        # To extract the SQL query from the text:
        pattern = re.compile(r'SELECT.*?;', re.DOTALL | re.IGNORECASE)
        match = pattern.search(sql_query)
        return match.group(0)

    else:
        print("Status code: ",response.status_code)
        return "Unable to get SQL query"
    
@tool
def get_data_from_database(sql_query:str)->list:
    """A tool that will fetch data from the database using the SQL query and return the output of the executed query

    Args:
        sql_query (str): The SQL query that is to be executed.

    Returns:
        str: Output of the executed SQL query
    """
    try:
        output = execute_query(sql_query)
        data = output[1]  # Second item in the tuple
        if len(data)>1:
            return "output is too long, use the 'get_data_from_database_and_create_report' function"
        else:
            return data[0]
        
    except:
        return "Operation failed"
    

@tool
def create_chart(user_request:str,csv_file_url:str)->str:
    """ Create a chart based on user request. Returns the URL of the chart.
    
    Args:
        user_request (str): A detailed explanation of the user's request with clear context.
        csv_file_url (str): URL of a csv file.

    Returns:
        str : URL of created chart.
    """

    try:
        output=chart_creator(user_request,csv_file_url)
        return output
    
    except Exception as error:
        print(error)
        return "An error has occurred, try again"
        
#----------------------------------------------------------------------------------------------------------------------------Tools End
    



def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }






def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )




#-----------------------------------------------------------------------------------------------------------------------------State


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

llm = AzureChatOpenAI(deployment_name=os.getenv("DEPLOYMENT_NAME"),
                      openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                      azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                      api_version=os.getenv("OPENAI_API_VERSION"),
                      streaming=True)
assistant_prompt1 = ChatPromptTemplate.from_messages(
    [
        (
           prompt

        ),
        ("placeholder", "{messages}"),
    ]
)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

tools = [get_sql_query,get_data_from_database,get_data_from_database_and_create_report,create_chart]
tool_names = {t.name for t in tools}

assistant_runnable = assistant_prompt1 | llm.bind_tools(tools)

#-----------------------------------------------------------------------------------------------------------------------------Graph


builder = StateGraph(State)

builder.add_node("assistant", Assistant(assistant_runnable))
builder.set_entry_point("assistant")
builder.add_node("tools", create_tool_node_with_fallback(tools))




def route_tools(state: State) -> Literal["tools", "__end__"]:
    next_node = tools_condition(state)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in tool_names:
        return "tools"
    


builder.add_conditional_edges(
    "assistant",
    route_tools,
)
builder.add_edge("tools", "assistant")


memory = SqliteSaver.from_conn_string(":memory:")
graph = builder.compile(
    checkpointer=memory,
    )


def sqlagent(thread_id:str,user_message:str)->str:
    if not thread_id:
        thread_id = str(uuid.uuid4())

    config = {"configurable": {"thread_id": thread_id}}
    print(thread_id)
    
    events = graph.stream(
        {"messages": ("user", user_message)}, config, stream_mode="values"
    )
    for event in events:
        message = event.get("messages")
        if isinstance(message, list):
            message = message[-1]
        if isinstance(message,AIMessage):
            if message.content:
                return thread_id,message.content
    snapshot = graph.get_state(config)
    


app = FastAPI()

# Define input and output models using Pydantic
class Input(BaseModel):
    id: str = ""
    user_message: str 

class Output(BaseModel):
    id: str
    sqlagent_message: str

# Endpoint to handle POST requests
@app.post("/sqlagent", response_model=Output)
async def process_user_message(data: Input):
    thread_id = data.id if data.id else ""
    user_message = data.user_message  

    result = sqlagent(thread_id,user_message)
    output_thread_id=result[0]
    sqlagent_message=result[1]

    
    return Output(id=output_thread_id, sqlagent_message=sqlagent_message)

