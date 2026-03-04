from langchain_ollama import ChatOllama

model = ChatOllama(model="llama3.1:8b", temperature=0)

from tools import get_unread_email_headers, get_email_content

tools = [get_unread_email_headers, get_email_content]

from langgraph.graph import MessagesState, END, START, StateGraph

agent = model.bind_tools(tools)

def call_model(state: MessagesState):
    """Invokes the LLM with the current conversation history."""
    response = agent.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: MessagesState):
    """Determines whether to continue to the tools node or end the graph."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    else:
        return END

from langgraph.prebuilt import ToolNode

tools_node = ToolNode(tools)

workflow = StateGraph(MessagesState)

workflow.add_node("call_model", call_model)
workflow.add_node("tools", tools_node)

workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", should_continue)
workflow.add_edge("tools", "call_model")

graph = workflow.compile()
