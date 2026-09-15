"""
ArgusCX — LLM Core Client
Initializes the ChatGroq client based on environment configuration.
"""
from typing import Optional
from langchain_groq import ChatGroq
from app.core.config import settings

def get_llm(temperature: float = 0.0) -> Optional[ChatGroq]:
    """
    Returns an initialized ChatGroq LangChain object.
    Returns None if no GROQ_API_KEY is provided in the configuration.
    """
    if not settings.GROQ_API_KEY:
        return None
        
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=temperature,
        max_tokens=4096,
        model_kwargs={"top_p": 0.9}
    )
