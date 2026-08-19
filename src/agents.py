import os
import certifi
import time
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import TypedDict, Annotated, Any
import operator
import uuid
import asyncio
import json

import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langgraph.checkpoint.postgres import PostgresSaver

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from src.tools.flight_tool import search_flights
from src.mcp import (
    tavily_mcp_search,
    extract_destination,
    forecast_mcp_search,
    weather_mcp_search,
)
from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    DATABASE_URL,
    get_database_url,
)


def run_async(coro):
    """Run async MCP helpers from sync LangGraph nodes safely under FastAPI."""
    try:
        asyncio.get_running_loop()
        in_running_loop = True
    except RuntimeError:
        in_running_loop = False

    if not in_running_loop:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


llm = ChatGroq(
    model=GROQ_MODEL, 
    api_key=GROQ_API_KEY,
    temperature=LLM_TEMPERATURE,
    max_tokens=LLM_MAX_TOKENS,
)


from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    get_database_url,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    MAX_CONVERSATION_MESSAGES,
    TEXT_TRUNCATE_LENGTH,
)
from src.constants import (
    KNOWN_AGENTS,
    AGENT_EXECUTION_ORDER,
)


class TravelState(TypedDict, total=False):
    # IMPORTANT: Don't use operator.add for messages - causes context overflow
    messages: list[AnyMessage]
    user_query: str

    # Supervisor + guardrail state
    guardrail_allowed: bool
    guardrail_reason: str
    selected_agents: list[str]
    trip_constraints: dict[str, Any]
    supervisor_reasoning: str

    # Specialist results
    flight_results: str
    hotel_results: str
    weather_results: str
    itinerary: str

    # Budget + HITL state
    budget_results: str
    approval_request: str
    approved: bool
    human_feedback: str
    final_response: str

    llm_calls: int
    
    # EVAL INSTRUMENTATION: Track execution for evaluation
    tools_used: Annotated[list[str], operator.add]
    trajectory: Annotated[list[str], operator.add]
    start_time: float
    end_time: float


KNOWN_AGENTS_SET = KNOWN_AGENTS

AGENT_ORDER = AGENT_EXECUTION_ORDER


def _llm_text(system_prompt: str, user_prompt: str) -> str:
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    return str(response.content)


def _json_from_llm(text: str) -> dict[str, Any]:
    """Extract the first complete JSON object returned by the model."""
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("The model did not return a JSON object.")

    return json.loads(text[start : end + 1])


def _empty_constraints() -> dict[str, Any]:
    return {
        "destination": "",
        "origin": "",
        "duration": "",
        "budget": "",
        "travel_style": "",
        "special_preferences": [],
    }


def trim_messages(messages: list, max_messages: int = MAX_CONVERSATION_MESSAGES) -> list:
    """
    Trim conversation history to reduce token usage.
    Keeps only the most recent N messages to stay within context limits.
    Always preserves system messages.
    """
    if len(messages) <= max_messages:
        return messages
    
    # Separate system messages from others
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
    
    # Keep only last N non-system messages
    recent_msgs = other_msgs[-max_messages:]
    
    # Return system messages + recent conversation
    return system_msgs + recent_msgs


def truncate_text(text: str, max_chars: int = TEXT_TRUNCATE_LENGTH) -> str:
    """Truncate text to max_chars with ellipsis if needed."""
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"


# Supervisor Agent + Input Guardrail
def supervisor_agent(state: TravelState):
    query = state["user_query"]
    llm_calls = state.get("llm_calls", 0)

    guardrail_prompt = f"""
    Determine whether the following request belongs to travel planning or travel information.
    Valid requests can include destinations, flights, hotels, weather, budgets, visas, transportation,
    sightseeing, food, packing or itineraries.

    Block clearly unrelated requests and requests asking for harmful or illegal instructions.
    Do not block a valid travel request merely because some details are missing.

    Return strict JSON only:
    {{
        "allowed": true,
        "reason": ""
    }}

    User request: {query}
    """

    try:
        guardrail_raw = _llm_text(
            "You are the input guardrail for a travel planning application. "
            "Return strict JSON only.",
            guardrail_prompt,
        )
        guardrail_result = _json_from_llm(guardrail_raw)
        allowed = bool(guardrail_result.get("allowed", True))
        guardrail_reason = str(guardrail_result.get("reason", "")).strip()
        llm_calls += 1
    except Exception as exc:
        print(f"Guardrail fallback used: {exc}")
        allowed = True
        guardrail_reason = "Guardrail validation fallback allowed the request"

    if not allowed:
        reason = guardrail_reason or (
            "GraphVoyageAI can only help with travel-planning requests. "
            "Please ask about a destination, flight, hotel, weather, budget, or itinerary."
        )
        return {
            "guardrail_allowed": False,
            "guardrail_reason": reason,
            "selected_agents": [],
            "trip_constraints": _empty_constraints(),
            "supervisor_reasoning": reason,
            "final_response": reason,
            "messages": state.get("messages", []) + [AIMessage(content=f"Guardrail blocked request: {reason}")],
            "llm_calls": llm_calls,
            "trajectory": ["supervisor_agent"],
        }

    supervisor_prompt = f"""
    Route travel tasks to specialist agents.

    Agents:
    - flight_agent: flights, airlines, routes
    - hotel_agent: hotels, accommodation
    - weather_agent: weather, climate
    - budget_agent: costs, budget
    - itinerary_agent: travel plan (always include)

    Return JSON:
    {{
        "selected_agents": ["flight_agent", "hotel_agent", "weather_agent", "budget_agent", "itinerary_agent"],
        "trip_constraints": {{
            "destination": "",
            "origin": "",
            "duration": "",
            "budget": "",
            "travel_style": "",
            "special_preferences": []
        }},
        "reasoning": ""
    }}

    User request: {query}
    """

    try:
        supervisor_raw = _llm_text(
            "You route work to travel specialist agents. Return strict JSON only.",
            supervisor_prompt,
        )
        parsed = _json_from_llm(supervisor_raw)
        requested_agents = parsed.get("selected_agents", [])
        selected_agents = [
            name
            for name in AGENT_ORDER
            if name in requested_agents and name in KNOWN_AGENTS_SET
        ]

        if "itinerary_agent" not in selected_agents:
            selected_agents.append("itinerary_agent")

        constraints = _empty_constraints()
        parsed_constraints = parsed.get("trip_constraints", {})
        if isinstance(parsed_constraints, dict):
            constraints.update(parsed_constraints)

        reasoning = str(parsed.get("reasoning", "")).strip()
        llm_calls += 1
    except Exception as exc:
        print(f"Supervisor fallback used: {exc}")
        selected_agents = AGENT_ORDER.copy()
        constraints = _empty_constraints()
        reasoning = (
            "Supervisor parsing failed, so the original full travel workflow "
            "was selected as a safe fallback."
        )

    return {
        "guardrail_allowed": True,
        "guardrail_reason": guardrail_reason,
        "selected_agents": selected_agents,
        "trip_constraints": constraints,
        "supervisor_reasoning": reasoning,
        "messages": state.get("messages", []) + [AIMessage(content="Supervisor created the agent plan.")],
        "llm_calls": llm_calls,
        "trajectory": ["supervisor_agent"],
    }


def guardrail_blocked_agent(state: TravelState):
    reason = state.get("final_response") or state.get("guardrail_reason") or (
        "This request was blocked by the travel input guardrail."
    )
    return {
        "final_response": reason,
        "messages": state.get("messages", []) + [AIMessage(content=reason)],
        "trajectory": ["guardrail_blocked_agent"],
    }


def flight_agent(state: TravelState):
    query = state["user_query"]

    try:
        flight_data = search_flights(query)
    except Exception as exc:
        flight_data = f"Flight information unavailable: {exc}"

    return {
        "flight_results": truncate_text(flight_data, 1500),  # Truncate output
        "messages": state.get("messages", []) + [AIMessage(content="Flight results fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
        "tools_used": ["search_flights"],
        "trajectory": ["flight_agent"],
    }


def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"

    try:
        hotel_results = run_async(tavily_mcp_search(query))
    except Exception as exc:
        hotel_results = f"Hotel information unavailable: {exc}"

    return {
        "hotel_results": truncate_text(hotel_results, 1500),  # Truncate output
        "messages": state.get("messages", []) + [AIMessage(content="Hotel information fetched.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
        "tools_used": ["tavily_mcp_search"],
        "trajectory": ["hotel_agent"],
    }


def weather_agent(state: TravelState):
    city = extract_destination(state["user_query"])

    try:
        weather_data = run_async(weather_mcp_search(city))
        forecast_data = run_async(forecast_mcp_search(city))
        weather_results = f"""
        Current Weather: {weather_data}

        Forecast: {forecast_data}
        """
    except Exception as exc:
        weather_results = f"Weather information unavailable: {exc}"

    return {
        "weather_results": truncate_text(weather_results, 1000),  # Truncate output
        "messages": state.get("messages", []) + [AIMessage(content="Weather information fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
        "tools_used": ["weather_mcp_search", "forecast_mcp_search"],
        "trajectory": ["weather_agent"],
    }


def budget_agent(state: TravelState):
    # Aggressively truncate inputs to prevent context overflow
    flight_summary = truncate_text(state.get('flight_results', ''), 400)
    hotel_summary = truncate_text(state.get('hotel_results', ''), 400)
    weather_summary = truncate_text(state.get('weather_results', ''), 200)
    
    prompt = f"""Analyze trip budget feasibility.

    Query: {state['user_query']}
    Constraints: {state.get('trip_constraints', {})}
    Flights: {flight_summary}
    Hotels: {hotel_summary}
    Weather: {weather_summary}

    Return: 1) Cost estimate 2) Budget risks 3) Savings tips 4) Feasibility
    Label estimates as approximate if needed.
    Keep response concise (max 1000 words).
    """

    messages = [
        SystemMessage(content="Travel budget analyst. Be concise."),
        HumanMessage(content=prompt),
    ]
    
    print(f"💰 Budget Agent - Prompt length: {len(prompt)} chars")
    
    response = llm.invoke(messages)

    return {
        "budget_results": str(response.content)[:2000],  # Truncate output too
        "messages": state.get("messages", []) + [AIMessage(content="Budget assessment generated.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
        "trajectory": ["budget_agent"],
    }


def itinerary_agent(state: TravelState):
    # Aggressively truncate to prevent context overflow
    flight_summary = truncate_text(state.get('flight_results', ''), 600)
    hotel_summary = truncate_text(state.get('hotel_results', ''), 600)
    weather_summary = truncate_text(state.get('weather_results', ''), 300)
    budget_summary = truncate_text(state.get('budget_results', ''), 500)
    
    prompt = f"""Create travel itinerary.

    Query: {state['user_query']}
    Constraints: {state.get('trip_constraints', {})}
    Flights: {flight_summary}
    Hotels: {hotel_summary}
    Weather: {weather_summary}
    Budget: {budget_summary}

    Make it practical, budget-aware, and ready for review.
    Keep response focused (max 1500 words).
    """

    messages = [
        SystemMessage(content="Expert travel planner. Be concise and practical."),
        HumanMessage(content=prompt),
    ]
    
    print(f"🗓️  Itinerary Agent - Prompt length: {len(prompt)} chars")
    
    response = llm.invoke(messages)

    approval_request = (
        "Please review the generated draft itinerary. Approve it to create the "
        "final polished plan, or provide feedback for revision."
    )

    return {
        "itinerary": str(response.content)[:3000],  # Truncate output
        "approval_request": approval_request,
        "messages": state.get("messages", []) + [AIMessage(content="Draft itinerary created for human review.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
        "trajectory": ["itinerary_agent"],
    }


def human_approval_agent(state: TravelState):
    # Do not wrap interrupt() in try/except. LangGraph uses it to pause execution.
    review = interrupt(
        {
            "question": "Do you approve this itinerary?",
            "draft_itinerary": state.get("itinerary", ""),
            "approval_request": state.get("approval_request", ""),
            "selected_agents": state.get("selected_agents", []),
            "supervisor_reasoning": state.get("supervisor_reasoning", ""),
            "expected_response": {
                "approved": True,
                "feedback": "Optional revision feedback",
            },
        }
    )

    approved = bool(review.get("approved", False))
    human_feedback = str(review.get("feedback", "")).strip()

    status = "approved" if approved else "sent back for revision"
    return {
        "approved": approved,
        "human_feedback": human_feedback,
        "messages": state.get("messages", []) + [AIMessage(content=f"Human review {status}.")],
        "trajectory": ["human_approval_agent"],
    }


def final_agent(state: TravelState):
    if state.get("approved", False):
        review_instruction = (
            "The user approved the draft. Preserve its decisions while polishing it."
        )
    else:
        review_instruction = (
            "The user requested a revision. Apply this feedback carefully: "
            f"{state.get('human_feedback', '') or 'Improve the draft before finalizing it.'}"
        )

    # CRITICAL: Heavily truncate all inputs to prevent context overflow
    flight_summary = truncate_text(state.get('flight_results', ''), 600)
    hotel_summary = truncate_text(state.get('hotel_results', ''), 600)
    weather_summary = truncate_text(state.get('weather_results', ''), 300)
    budget_summary = truncate_text(state.get('budget_results', ''), 500)
    itinerary_summary = truncate_text(state.get('itinerary', ''), 2000)

    final_prompt = f"""Generate the final travel response for the user.

    Human Review: {review_instruction}
    User Request: {state['user_query']}
    Supervisor Constraints: {state.get('trip_constraints', {})}
    Flights: {flight_summary}
    Hotels: {hotel_summary}
    Weather: {weather_summary}
    Budget Analysis: {budget_summary}
    Draft Itinerary: {itinerary_summary}

    Format the final answer beautifully using these sections:
    1. Trip Summary
    2. Flight Information
    3. Hotel Suggestions
    4. Weather Information
    5. Day-by-Day Itinerary
    6. Estimated Budget
    7. Final Recommendations

    Important:
    - Be clear and practical
    - Mention that live flight APIs may not provide ticket prices when pricing is unavailable
    - Include weather-based travel advice
    - Keep the response useful for real travel planning
    - Incorporate the human feedback when revision was requested
    - Keep response concise (max 2000 words)
    """

    print(f"📝 Final Agent - Prompt length: {len(final_prompt)} chars")

    response = llm.invoke(
        [
            SystemMessage(content="You are a professional AI travel booking assistant. Be concise and structured."),
            HumanMessage(content=final_prompt),
        ]
    )

    return {
        "final_response": response.content,
        "messages": state.get("messages", []) + [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
        "trajectory": ["final_agent"],
        "end_time": time.time(),
    }


# Dynamic Supervisor Routing
ROUTE_MAP = {
    "guardrail_blocked": "guardrail_blocked",
    "flight_agent": "flight_agent",
    "hotel_agent": "hotel_agent",
    "weather_agent": "weather_agent",
    "budget_agent": "budget_agent",
    "itinerary_agent": "itinerary_agent",
}


def _selected_agents(state: TravelState) -> list[str]:
    selected = state.get("selected_agents", [])
    return [agent for agent in AGENT_ORDER if agent in selected]


def route_from_supervisor(state: TravelState) -> str:
    if not state.get("guardrail_allowed", True):
        return "guardrail_blocked"

    selected = _selected_agents(state)
    return selected[0] if selected else "itinerary_agent"


def route_after_agent(current_agent: str):
    def route(state: TravelState) -> str:
        selected = _selected_agents(state)
        current_index = AGENT_ORDER.index(current_agent)

        for next_agent in AGENT_ORDER[current_index + 1 :]:
            if next_agent in selected:
                return next_agent
        return "itinerary_agent"

    return route


# Build Graph
graph = StateGraph(TravelState)

graph.add_node("supervisor", supervisor_agent)
graph.add_node("guardrail_blocked", guardrail_blocked_agent)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("budget_agent", budget_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("human_approval", human_approval_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", route_from_supervisor, ROUTE_MAP)

graph.add_conditional_edges("flight_agent", route_after_agent("flight_agent"), ROUTE_MAP)
graph.add_conditional_edges("hotel_agent", route_after_agent("hotel_agent"), ROUTE_MAP)
graph.add_conditional_edges("weather_agent", route_after_agent("weather_agent"), ROUTE_MAP)
graph.add_conditional_edges("budget_agent", route_after_agent("budget_agent"), ROUTE_MAP)

graph.add_edge("itinerary_agent", "human_approval")
graph.add_edge("human_approval", "final_agent")
graph.add_edge("final_agent", END)
graph.add_edge("guardrail_blocked", END)

# PostgreSQL Checkpointer
DATABASE_URL = get_database_url()
_conn = psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)
checkpointer = PostgresSaver(_conn)
checkpointer.setup()
travel_graph = graph.compile(checkpointer=checkpointer)


def _interrupt_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    interrupts = result.get("__interrupt__", [])
    if not interrupts:
        return None

    first_interrupt = interrupts[0]
    payload = getattr(first_interrupt, "value", first_interrupt)
    return payload if isinstance(payload, dict) else {"value": payload}


def _serialize_result(result: dict[str, Any], thread_id: str) -> dict[str, Any]:
    messages = result.get("messages", [])
    last_message = messages[-1].content if messages else ""
    answer = result.get("final_response") or last_message
    interrupt_payload = _interrupt_payload(result)

    if interrupt_payload:
        answer = interrupt_payload.get("draft_itinerary") or result.get("itinerary", "")

    # Calculate latency if both timestamps exist
    start_time = result.get("start_time", 0.0)
    end_time = result.get("end_time", 0.0)
    latency = end_time - start_time if end_time > 0 else 0.0

    return {
        "thread_id": thread_id,
        "answer": answer,
        "requires_approval": interrupt_payload is not None,
        "approval_request": (
            interrupt_payload.get("approval_request", "")
            if interrupt_payload
            else result.get("approval_request", "")
        ),
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "budget_results": result.get("budget_results", ""),
        "itinerary": (
            interrupt_payload.get("draft_itinerary", "")
            if interrupt_payload
            else result.get("itinerary", "")
        ),
        "selected_agents": result.get("selected_agents", []),
        "trip_constraints": result.get("trip_constraints", {}),
        "supervisor_reasoning": result.get("supervisor_reasoning", ""),
        "guardrail_allowed": result.get("guardrail_allowed", True),
        "guardrail_reason": result.get("guardrail_reason", ""),
        "approved": result.get("approved"),
        "human_feedback": result.get("human_feedback", ""),
        "llm_calls": result.get("llm_calls", 0),
        # EVAL INSTRUMENTATION: Include metrics for evaluation
        "tools_used": result.get("tools_used", []),
        "trajectory": result.get("trajectory", []),
        "latency_seconds": latency,
        "start_time": start_time,
        "end_time": end_time,
    }


def run_travel_agent(user_input: str, thread_id: str | None = None):
    """Start a new travel-planning run and pause at human approval."""
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {"configurable": {"thread_id": thread_id}}

    result = travel_graph.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "guardrail_allowed": True,
            "guardrail_reason": "",
            "selected_agents": [],
            "trip_constraints": _empty_constraints(),
            "supervisor_reasoning": "",
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "budget_results": "",
            "itinerary": "",
            "approval_request": "",
            "approved": False,
            "human_feedback": "",
            "final_response": "",
            "llm_calls": 0,
            "tools_used": [],
            "trajectory": [],
            "start_time": time.time(),
            "end_time": 0.0,
        },
        config=config,
    )

    return _serialize_result(result, thread_id)


def resume_travel_agent(thread_id: str, approved: bool, feedback: str = ""):
    """Resume the paused LangGraph thread after human review."""
    if not thread_id:
        raise ValueError("thread_id is required to resume a travel plan.")

    config = {"configurable": {"thread_id": thread_id}}
    result = travel_graph.invoke(
        Command(
            resume={
                "approved": approved,
                "feedback": feedback.strip(),
            }
        ),
        config=config,
    )

    return _serialize_result(result, thread_id)
