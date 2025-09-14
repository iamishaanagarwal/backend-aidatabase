from typing import Union, Optional, List, Dict, Any
import json
import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")
# Configure OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: List[ChatMessage] = []
    file_data: Optional[str] = None  # JSON string if file was uploaded

class ChatResponse(BaseModel):
    message: str
    chat_history: List[ChatMessage]
    error: Optional[str] = None

class AnalysisResponse(BaseModel):
    message: str
    analysis: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    message: Optional[str] = Form(None),
    chat_history: Optional[str] = Form("[]"),
    file: Optional[UploadFile] = File(None),
    chat_request: Optional[ChatRequest] = Body(None)
):
    history = []  # Default empty history
    
    try:
        # Handle different input methods (form data vs JSON)
        if chat_request:
            # JSON request
            user_message = chat_request.message
            history = chat_request.chat_history
            file_data = chat_request.file_data
        else:
            # Form data request
            if not message:
                raise HTTPException(status_code=400, detail="Message is required")
            
            user_message = message
            
            # Parse chat history from form
            try:
                history_data = json.loads(chat_history or "[]")
                history = [ChatMessage(**msg) for msg in history_data]
            except (json.JSONDecodeError, TypeError):
                history = []
            
            # Handle file upload
            file_data = None
            if file:
                if not file.filename or not file.filename.endswith('.json'):
                    raise HTTPException(
                        status_code=400,
                        detail="Please upload a JSON file containing database logs."
                    )
                
                content = await file.read()
                try:
                    json_data = json.loads(content.decode('utf-8'))
                    file_data = json.dumps(json_data, indent=2)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid JSON format. Please ensure your file contains valid JSON data."
                    )
        
        # Prepare the system prompt for database analysis
        system_prompt = """You are a database performance expert. Analyze ALL queries in the provided database logs.

        For each query, provide:
        - Performance assessment (duration_ms, calls, rows)
        - Specific optimization recommendations
        - Index suggestions
        - Priority level (Critical/High/Medium/Low)

        Be concise but comprehensive. Cover every query in the logs."""
        
        # Build conversation history for OpenAI
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Prepare the current user message
        current_message = user_message
        if file_data:
            current_message += f"\n\nDatabase Logs:\n{file_data}"
        
        # Add current user message
        messages.append({"role": "user", "content": current_message})
        
        # Call OpenAI API with properly typed messages
        formatted_messages: List[Dict[str, Any]] = []
        for msg in messages:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})
        
        response = openai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=formatted_messages,  # type: ignore
            max_tokens=4000,
            temperature=0.7
        )
        
        assistant_response = response.choices[0].message.content or "I'm sorry, I couldn't generate a response."
        
        # Build updated chat history
        updated_history = history.copy()
        updated_history.append(ChatMessage(role="user", content=user_message))
        updated_history.append(ChatMessage(role="assistant", content=assistant_response))
        
        return ChatResponse(
            message=assistant_response,
            chat_history=updated_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ChatResponse(
            message="Sorry, I encountered an error while processing your request.",
            chat_history=history,
            error=str(e)
        )


