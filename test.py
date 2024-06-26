
from langchain_core.tools import tool
from typing import Annotated
from utils import execute_query,write_headings_to_csv,write_rows_to_csv, get_blob_url, upload_to_blob
from chart_functions import chart_creator
from typing_extensions import TypedDict
from prompts import prompt, chart_creator_prompt
from langgraph.graph.message import AnyMessage, add_messages
from typing import Annotated
import requests
from langchain_openai import AzureChatOpenAI

import re
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

azure_key="43acd730f49d47b494589ffefa5028fa"
api_base = "https://askauraopenai.openai.azure.com/"
api_version = "2024-02-01"

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
    
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import ToolMessage

from langgraph.prebuilt import ToolNode


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


from azure.storage.blob import BlobServiceClient


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print(f"Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


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

llm = AzureChatOpenAI(deployment_name="chat",
                      openai_api_key=azure_key,
                      azure_endpoint=api_base,
                      api_version=api_version)
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

tools = [get_sql_query,get_data_from_database_and_create_report,get_data_from_database,create_chart]
tool_names = {t.name for t in tools}

assistant_runnable = assistant_prompt1 | llm.bind_tools(tools)

#-----------------------------------------------------------------------------------------------------------------------------Graph
from typing import Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

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
    # NEW: The graph will always halt before executing the "tools" node.
    # The user can approve or reject (or even alter the request) before
    # the assistant continues
    
)

import uuid


thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": str(uuid.uuid4())}}




_printed = set()
# We can reuse the tutorial questions from part 1 to see how it does.
for i in range(100):
    question=input("Enter message >>")
    events = graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
    for event in events:
        _print_event(event, _printed)
    snapshot = graph.get_state(config)
   