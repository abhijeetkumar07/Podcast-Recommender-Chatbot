import os
import logging
from typing import Optional
from config import config

logger = logging.getLogger(__name__)

def get_llm(temperature: float = 0.3):
    """
    Returns an instantiated LangChain Chat Model.
    Configurable between Google Gemini and OpenAI.
    Gracefully falls back if no API key is provided.
    """
    api_key = config.GOOGLE_API_KEY
    if config.DEFAULT_LLM_PROVIDER == "gemini" and api_key and api_key != "your_actual_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=config.GEMINI_MODEL,
                google_api_key=api_key,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")

    if config.OPENAI_API_KEY:
        try:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                from langchain_community.chat_models import ChatOpenAI
            return ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key=config.OPENAI_API_KEY,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatOpenAI: {e}")

    logger.warning("No valid API Key detected for Gemini or OpenAI. LLM features will run in intelligent offline fallback mode.")
    return None
