import time
from typing import Dict, Any, List, TypedDict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from core import PerceptionModule, action_tools
from xai_logger import xai_logger
from simulation import sim

# Define State
class AgentState(TypedDict):
    messages: List[BaseMessage]
    intersection_id: str
    telemetry_raw: Dict[str, Any]
    semantic_context: str
    scenario_type: str # 'standard' or 'emergency'

# Setup Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
llm_with_tools = llm.bind_tools(action_tools)

def extract_token_usage(res) -> int:
    try:
        # Support varying metadada formats across LLMs
        return res.response_metadata.get('token_usage', {}).get('total_token_count', 0)
    except Exception:
        return 0

# Node 1: Perception
def perception_node(state: AgentState):
    sim_data = sim.get_sensors_data(state["intersection_id"])
    context = PerceptionModule.telemetry_to_text(sim_data)
    return {
        "telemetry_raw": sim_data,
        "semantic_context": context,
        "messages": [HumanMessage(content=context)]
    }

# Node 2: Supervisor Agent
def supervisor_agent(state: AgentState):
    start_time = time.time()
    context = state["semantic_context"]
    
    prompt = f"""You are the Supervisor Agent for traffic control. Evaluate the current context:
{context}

Is there an emergency vehicle present?
Output exactly either "emergency" or "standard"."""
    
    res = llm.invoke([HumanMessage(content=prompt)])
    scenario_type = "emergency" if "emergency" in res.content.lower() else "standard"
    
    xai_logger.log_reasoning(
        agent_name="SupervisorAgent",
        context=context,
        reasoning=f"Evaluated context and decided this is a {scenario_type} scenario.",
        action=f"Route to {scenario_type} workflow."
    )
    
    latency = (time.time() - start_time) * 1000
    xai_logger.log_metrics(token_usage=extract_token_usage(res), latency_ms=latency)
    
    return {"scenario_type": scenario_type}

# Routing function
def route_scenario(state: AgentState) -> Literal["intersection_agent", "emergency_agent"]:
    if state["scenario_type"] == "emergency":
        return "emergency_agent"
    return "intersection_agent"

# Node 3: Intersection Agent (Standard)
def intersection_agent(state: AgentState):
    start_time = time.time()
    context = state["semantic_context"]
    
    prompt = f"""You are the Intersection Agent for a smart mobility system. 
Your goal is to minimize average waiting time and prevent starvation (lanes waiting too long).
You must balance 'queue length' with 'longest wait'. A lane with a small queue but a massive wait time should be prioritized to solve the edge case of starvation.
State your reasoning clearly, evaluating all lanes, then call the `set_light_green` tool to execute your decision.

Context:
{context}
"""
    messages = [HumanMessage(content=prompt)]
    res = llm_with_tools.invoke(messages)
    
    reasoning = res.content if res.content else "Decided to invoke tool based on longest queue."
    xai_logger.log_reasoning(
        "IntersectionAgent", 
        context, 
        reasoning, 
        "Invoked set_light_green"
    )
    
    latency = (time.time() - start_time) * 1000
    xai_logger.log_metrics(extract_token_usage(res), latency)

    return {"messages": [res]}

# Node 4: Emergency Vehicle Agent
def emergency_agent(state: AgentState):
    start_time = time.time()
    context = state["semantic_context"]
    
    prompt = f"""You are the Emergency Vehicle Agent for a smart mobility system.
Your priority is life-safety. You negotiate right-of-way to establish a Green Corridor.
Review the situational context. If there are multiple emergency vehicles, prioritize the one with the longest wait time or the largest queue behind it.
Explain your reasoning, then call `override_signal` to give a green light to the chosen lane with the emergency vehicle.

Context:
{context}
"""
    messages = [HumanMessage(content=prompt)]
    res = llm_with_tools.invoke(messages)
    
    reasoning = res.content if res.content else "Detected emergency vehicle, invoking override tool immediately."
    xai_logger.log_reasoning(
        "EmergencyVehicleAgent", 
        context, 
        reasoning, 
        "Invoked override_signal"
    )
    
    latency = (time.time() - start_time) * 1000
    xai_logger.log_metrics(extract_token_usage(res), latency)

    return {"messages": [res]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"

# Graph Construction
workflow = StateGraph(AgentState)

workflow.add_node("perception", perception_node)
workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("intersection_agent", intersection_agent)
workflow.add_node("emergency_agent", emergency_agent)
workflow.add_node("tools", ToolNode(action_tools))

workflow.add_edge(START, "perception")
workflow.add_edge("perception", "supervisor")
workflow.add_conditional_edges("supervisor", route_scenario)
workflow.add_conditional_edges("intersection_agent", should_continue)
workflow.add_conditional_edges("emergency_agent", should_continue)
workflow.add_edge("tools", END)

app = workflow.compile()
