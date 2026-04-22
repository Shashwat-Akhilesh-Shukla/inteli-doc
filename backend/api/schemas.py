from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message author (user or assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The user's query or prompt to be answered by the documentation.")
    history: List[ChatMessage] = Field(default_factory=list, description="Previous messages in the conversation for context.")
    
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message details.")
