
# OVERVIEW
Your task is to create an agentic application for demonstration purposes. The application should be a customer service concierge for personal banking. 
Users will interact with it by chatting, so it should have a simple chat interface that supports multi-turn conversations between a human user and the agent.

# DETAILS
- You can use LangChain, LangGraph, or Deep Agents. You are free to choose the best framework.
- When I show this application to customers, I want to show off the features of LangSmith Engine. You can read about LangSmith Engine here https://docs.langchain.com/langsmith/engine and here https://www.langchain.com/blog/introducing-langsmith-engine. Therefore the application should have some errors that cause LangSmith Engine to detect issues to be fixed. Make sure you include deliberate errors in the implementation. Some good errors modes will be: hallucinations and broken tool calls.
- You must create a load generation script that generates several traces, some of which should trigger the error modes.
- Create a golden dataset that shows examples representative of good user inputs and good agent outputs. No more than 7 examples.
- Create an offline evaluation experiment with 2 LLM-as-judge evaluators to check for hallucinations and tool call trajectories.
- You are free to determine the best source of data for the chatbot, but at a minimum I want a tool call that retrieves documents before answering user questions. 
- The application should be deployable to LangSmith deployments.




