from langchain_ollama import ChatOllama
from langgraph.graph import MessagesState, END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from tools import get_unread_email_headers, get_email_content

model = ChatOllama(model="llama3.1:8b", temperature=0)
tools = [get_unread_email_headers, get_email_content]
agent = model.bind_tools(tools)

SYSTEM_PROMPT = SystemMessage(content="""You are a strict, helpful email assistant. 
Follow these rules exactly:
1. If the user asks to read an email, you MUST first use get_unread_email_headers to find the exact email ID. 
2. NEVER guess or invent an email ID. 
3. NEVER invent tool parameters. Use only the tools provided.""")

def call_model(state: MessagesState):
    """Invokes the LLM with the current conversation history and system prompt."""
    messages = state["messages"]
    
    if not messages or getattr(messages[0], "type", "") != "system":
        messages = [SYSTEM_PROMPT] + messages
        
    response = agent.invoke(messages)
    return {"messages": [response]}

def should_continue(state: MessagesState):
    """Determines whether to continue to the tools node or end the graph."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

tools_node = ToolNode(tools)

workflow = StateGraph(MessagesState)
workflow.add_node("call_model", call_model)
workflow.add_node("tools", tools_node)

workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", should_continue)
workflow.add_edge("tools", "call_model")

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)