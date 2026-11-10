# Step1: Setup FastAPI backend
import sys
from pathlib import Path

# Add backend directory to sys.path so internal imports work regardless of working directory
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, Form
from pydantic import BaseModel
import uvicorn

from ai_agent import graph, SYSTEM_PROMPT, parse_response, get_agent_response

app = FastAPI()

# Step2: Receive and validate request from Frontend
class Query(BaseModel):
    message: str
    history: list = []



@app.post("/ask")
async def ask(query: Query):
    tool_called_name, final_response = get_agent_response(query.message, history=query.history)
    # Step3: Send response to the frontend
    return {"response": final_response,
            "tool_called": tool_called_name}

from fastapi.responses import PlainTextResponse
from xml.etree.ElementTree import Element, tostring

def _twiml_message(body: str) -> PlainTextResponse:
    """Create minimal TwiML <Response><Message>...</Message></Response>"""
    response_el = Element('Response')
    message_el = Element('Message')
    message_el.text = body
    response_el.append(message_el)
    xml_bytes = tostring(response_el, encoding='utf-8')
    return PlainTextResponse(content=xml_bytes, media_type='application/xml')



@app.post("/whatsapp_ask")
async def whatsapp_ask(Body: str = Form(...)): 
    user_text = Body.strip() if Body else ""
    tool_called_name, final_response = get_agent_response(user_text)

    if not final_response:
        final_response = "I'm here to support you, but I couldn't generate a response just now."

    # Step3: Send response to Twilio
    return _twiml_message(final_response)



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)







