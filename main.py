
from langchain_core.tools import tool
from typing import Annotated

from typing_extensions import TypedDict
from prompts import prompt
from langgraph.graph.message import AnyMessage, add_messages
import csv
import psycopg2
from typing import Annotated
import requests
import re
from langchain_openai import ChatOpenAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

#------------------------------------------------------------------------------------------------------------------------------Tools
@tool
def get_data_from_database(sql_query:str)->str:
    """get data from a database using a postgreSQL query. Returns status of the operation"""
    
    

# Define your database connection parameters
    db_params = {
        'dbname': 'postgres',
        'user': 'aura_admin',
        'password': 'England125',
        'host': 'auradata.postgres.database.azure.com',  # e.g., 'localhost' or '127.0.0.1'
        'port': '5432'  # e.g., '5432'
    }

    try:
        # Connect to your postgres DB
        connection = psycopg2.connect(**db_params)

        # Create a cursor object
        cursor = connection.cursor()

        # Execute a query
        cursor.execute(sql_query)

        # Fetch all results from the executed query
        rows = cursor.fetchall()
        data=[]
        # Print fetched rows
        for row in rows:
            data.append(row)

        csv_file = 'output.csv'

    # Write the data to a CSV file
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            
            # Write the data rows
            writer.writerows(data)

        print(f"Data has been written to {csv_file}")
        return "operation successful"

    except Exception as error:
        print(f"Error: {error}")
        return "operation failed"

    finally:
        # Close the cursor and connection to the database
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@tool
def get_sql_query(user_request:str)->str:
    """Get an SQL query to fulfill the user's request. Returns an SQL query if the operation is successful. """

    url = 'https://databee-engine.azurewebsites.net/api/v1/prompts/sql-generations'
    text=user_request
    data = {
        "finetuning_id": "",
        "evaluate": False,
        "metadata": {},
        "prompt": {
            "text": user_request,
            "db_connection_id": "666219d8f359460d6cc32410",
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

llm = ChatOpenAI(model="gpt-3.5-turbo")

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

tools = [get_data_from_database,get_sql_query]
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
    while snapshot.next:
        # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
        # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
        # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
        user_input = input(
            "Do you approve of the above actions? Type 'y' to continue;"
            " otherwise, explain your requested changed.\n\n"
        )
        if user_input.strip() == "y":
            # Just continue
            result = graph.invoke(
                None,
                config,
            )
        else:
            # Satisfy the tool invocation by
            # providing instructions on the requested changes / change of mind
            result = graph.invoke(
                {
                    "messages": [
                        ToolMessage(
                            tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                            content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                        )
                    ]
                },
                config,
            )
        snapshot = graph.get_state(config)