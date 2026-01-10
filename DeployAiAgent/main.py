import os
import subprocess
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from photo_agent import run_agent

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Request model for agent invocation
class AgentRequest(BaseModel):
    """
    Request model for agent invocation.
    """
    prompt: str

# Response model for agent invocation
class AgentResponse(BaseModel):
    """
    Response model for agent invocation.
    """
    response: str

@app.get("/")
async def home(request: Request):
    """
    Serve the main HTML interface.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/agent", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest):
    """
    Endpoint to invoke the AI agent with a user prompt.    
    """
    try:
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
        
        # Run the agent with the user's prompt
        response = run_agent(request.prompt)
        return AgentResponse(response=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {str(e)}")
    
uvicorn.run(app, host="0.0.0.0", port=8000)