# Step1: Setup Streamlit
import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/ask"

st.set_page_config(page_title="AI Mental Health Therapist", layout="wide")
st.title("🧠 SafeSpace – AI Mental Health Therapist")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Step2: User is able to ask question
# Chat input
user_input = st.chat_input("What's on your mind today?")
if user_input:
    # Append user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # AI Agent exists here
    try:
        payload = {
            "message": user_input,
            "history": st.session_state.chat_history[:-1]
        }
        response = requests.post(BACKEND_URL, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            tool_called = data.get("tool_called", "None")
            tool_suffix = f"\n\n*Tool used: `{tool_called}`*" if tool_called and tool_called != "None" else ""
            assistant_reply = f"{data.get('response', '')}{tool_suffix}"
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"⚠️ Server returned error {response.status_code}: {response.text}"
            })
    except requests.exceptions.ConnectionError:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "⚠️ Could not connect to the backend server. Please make sure the backend is running at http://localhost:8000."
        })
    except Exception as e:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"⚠️ An unexpected error occurred: {e}"
        })


# Step3: Show response from backend
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])