from agent import graph

config = {"configurable": {"thread_id": "session_1"}}

print("Local Email Agent initialized. Type 'quit' to exit.")

while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ['quit', 'exit', 'q', 'e', 'thanks', 'thank you']:
        print("Shutting down agent...")
        break

    formatted_input = {"messages": [("user", user_input)]}

    print("Agent is thinking... ", end="", flush=True)

    for msg, metadata in graph.stream(formatted_input, config=config, stream_mode="messages"):
        if metadata.get("langgraph_node") == "call_model" and msg.content:
            print(msg.content, end="", flush=True)

    print("\n" + "-" * 40)