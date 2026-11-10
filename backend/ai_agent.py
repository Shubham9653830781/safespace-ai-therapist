import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from langchain_core.tools import tool
except ImportError:
    from langchain.agents import tool

try:
    from backend.config import GOOGLE_MAPS_API_KEY, GROQ_API_KEY
    from backend.tools import query_medgemma, call_emergency
except ImportError:
    from config import GOOGLE_MAPS_API_KEY, GROQ_API_KEY
    from tools import query_medgemma, call_emergency

@tool
def ask_mental_health_specialist(query: str) -> str:
    """
    Generate a therapeutic response using the MedGemma model.
    Use this for all general user queries, mental health questions, emotional concerns,
    or to offer empathetic, evidence-based guidance in a conversational tone.
    """
    return query_medgemma(query)


@tool
def emergency_call_tool() -> None:
    """
    Place an emergency call to the safety helpline's phone number via Twilio.
    Use this only if the user expresses suicidal ideation, intent to self-harm,
    or describes a mental health emergency requiring immediate help.
    """
    call_emergency()



import googlemaps
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None


@tool
def find_nearby_therapists_by_location(location: str) -> str:
    """
    Finds real therapists near the specified location using Google Maps API.
    If the API key is unavailable, provides direct directory links and verified helpline phone numbers.
    
    Args:
        location (str): The city or area to search.
    
    Returns:
        str: A list of therapist names, addresses, and phone numbers or direct directory search resources.
    """
    if not gmaps:
        import urllib.parse
        encoded_loc = urllib.parse.quote(location.strip())
        return (
            f"Direct Google Maps lookup is currently unconfigured. Here are immediate directories and verified contact numbers for {location}:\n\n"
            f"1. **Psychology Today Therapist Directory**: https://www.psychologytoday.com/us/therapists/{encoded_loc}\n"
            f"2. **GoodTherapy Directory**: https://www.goodtherapy.org/therapists/{encoded_loc}\n"
            f"3. **SAMHSA National Mental Health Helpline (24/7, Free)**: 1-800-662-4357 (TTY: 1-800-487-4889)\n"
            f"4. **988 Suicide & Crisis Lifeline**: Call or text 988\n"
            f"5. **Crisis Text Line**: Text HOME to 741741\n"
            f"6. **International Helpline Directory**: https://findahelpline.com/"
        )
    try:
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return f"Could not find coordinates for '{location}'. Please try a more specific city or postal code."
        lat_lng = geocode_result[0]['geometry']['location']
        lat, lng = lat_lng['lat'], lat_lng['lng']
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=5000,
            keyword="Psychotherapist"
        )
        top_results = places_result.get('results', [])[:5]
        if not top_results:
            return f"No therapist listings found within 5km of {location} on Google Maps."

        output = [f"Therapists near {location}:"]
        for place in top_results:
            name = place.get("name", "Unknown")
            address = place.get("vicinity", "Address not available")
            phone = "Phone not available"
            place_id = place.get("place_id")
            if place_id:
                try:
                    details = gmaps.place(place_id=place_id, fields=["formatted_phone_number"])
                    phone = details.get("result", {}).get("formatted_phone_number", "Phone not available")
                except Exception:
                    pass

            output.append(f"- **{name}** | {address} | 📞 {phone}")

        return "\n".join(output)
    except Exception as e:
        import urllib.parse
        encoded_loc = urllib.parse.quote(location.strip())
        return (
            f"Google Maps service notice: {e}\n\n"
            f"Here are immediate direct directories and contact numbers for therapists near {location}:\n\n"
            f"1. **Psychology Today Therapist Directory**: https://www.psychologytoday.com/us/therapists/{encoded_loc}\n"
            f"2. **GoodTherapy Directory**: https://www.goodtherapy.org/therapists/{encoded_loc}\n"
            f"3. **SAMHSA National Mental Health Helpline (24/7, Free)**: 1-800-662-4357\n"
            f"4. **988 Suicide & Crisis Lifeline**: Call or text 988\n"
            f"5. **Crisis Text Line**: Text HOME to 741741\n"
            f"6. **International Helpline Directory**: https://findahelpline.com/"
        )


# Step1: Create an AI Agent & Link to backend
#from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

tools = [ask_mental_health_specialist, emergency_call_tool, find_nearby_therapists_by_location]
if GROQ_API_KEY:
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY)
    graph = create_react_agent(llm, tools=tools)
else:
    llm = None
    graph = None

SYSTEM_PROMPT = """
You are an AI engine supporting mental health conversations with warmth, empathy, and vigilance.
You have access to three tools:

1. `ask_mental_health_specialist`: Use this tool to answer all emotional or psychological queries with therapeutic guidance.
2. `find_nearby_therapists_by_location`: Use this tool if the user asks about nearby therapists or if recommending local professional help would be beneficial.
3. `emergency_call_tool`: Use this immediately if the user expresses suicidal thoughts, self-harm intentions, or is in crisis.

CRITICAL INSTRUCTIONS:
- Whenever you use a tool, always provide a thoughtful, empathetic response to the user presenting the insights or guidance.
- Never output an empty response. Always respond kindly, clearly, and supportively.
"""

def parse_response(stream):
    tool_called_name = "None"
    last_tool_output = None
    final_response = None

    for s in stream:
        # Check if a tool was called
        tool_data = s.get('tools')
        if tool_data:
            tool_messages = tool_data.get('messages')
            if tool_messages and isinstance(tool_messages, list):
                for msg in tool_messages:
                    tool_called_name = getattr(msg, 'name', 'None')
                    content = getattr(msg, 'content', None)
                    if content:
                        last_tool_output = content

        # Check if agent returned a message
        agent_data = s.get('agent')
        if agent_data:
            messages = agent_data.get('messages')
            if messages and isinstance(messages, list):
                for msg in messages:
                    if msg.content:
                        final_response = msg.content

    # If the agent didn't generate extra text, use the tool's therapeutic output
    if not final_response and last_tool_output:
        final_response = last_tool_output

    return tool_called_name, final_response


def get_agent_response(user_message: str, history: list = None):
    """
    Robust response handler that runs the LangGraph agent and falls back gracefully
    if the underlying model produces an empty generation or tool schema error.
    """
    if not graph:
        return "None", "GROQ_API_KEY is not configured. Please set your GROQ_API_KEY in backend/config.py or as an environment variable."

    messages = [("system", SYSTEM_PROMPT)]
    if history:
        for item in history[-6:]:  # Keep recent context
            role = "user" if item.get("role") == "user" else "assistant"
            content = item.get("content", "")
            if content:
                clean_content = content.split("\n\n*Tool used:")[0].split(" WITH TOOL:")[0]
                messages.append((role, clean_content))
    messages.append(("user", user_message))

    inputs = {"messages": messages}

    # Attempt 1: LangGraph ReAct agent stream
    try:
        stream = graph.stream(inputs, stream_mode="updates")
        tool_called_name, final_response = parse_response(stream)
        if final_response:
            return tool_called_name, final_response
    except Exception as e:
        print(f"[WARNING] Agent execution error: {e}. Executing specialist fallback...")

    # Attempt 2: Direct fallback to mental health specialist tool
    try:
        specialist_response = ask_mental_health_specialist.invoke({"query": user_message})
        if specialist_response:
            return "ask_mental_health_specialist", specialist_response
    except Exception as e:
        print(f"[ERROR] Specialist fallback failed: {e}")

    return "None", "I hear you, and I want you to know you are not alone. Even when things feel overwhelming, your feelings are valid. What would feel most supportive right now?"


"""if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        print(f"Received user input: {user_input[:200]}...")
        inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", user_input)]}
        stream = graph.stream(inputs, stream_mode="updates")
        tool_called_name, final_response = parse_response(stream)
        print("TOOL CALLED: ", tool_called_name)
        print("ANSWER: ", final_response)"""
        