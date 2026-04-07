from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.nodes.get_tickers import get_tickers
from agent.nodes.fetch_data import fetch_data
from agent.nodes.calculate_indicators import calculate_indicators
from agent.nodes.pre_screen import pre_screen
from agent.nodes.decision_maker import decision_maker
from agent.nodes.generate_charts import generate_charts
from agent.nodes.notifier import notifier

def create_agent():
    """
    エージェントの処理ワークフロー(Graph)を構築する
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("get_tickers", get_tickers)
    workflow.add_node("fetch_data", fetch_data)
    workflow.add_node("calculate_indicators", calculate_indicators)
    workflow.add_node("pre_screen", pre_screen)
    workflow.add_node("decision_maker", decision_maker)
    workflow.add_node("generate_charts", generate_charts)
    workflow.add_node("notifier", notifier)
    
    # Add edges
    workflow.add_edge(START, "get_tickers")
    workflow.add_edge("get_tickers", "fetch_data")
    workflow.add_edge("fetch_data", "calculate_indicators")
    workflow.add_edge("calculate_indicators", "pre_screen")
    workflow.add_edge("pre_screen", "decision_maker")
    workflow.add_edge("decision_maker", "generate_charts")
    workflow.add_edge("generate_charts", "notifier")
    workflow.add_edge("notifier", END)
    
    app = workflow.compile()
    
    return app
