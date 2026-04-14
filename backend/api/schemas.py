from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, description="The user's query or prompt to be answered by the documentation.")
    
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message details.")
