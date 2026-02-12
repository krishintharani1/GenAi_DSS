from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from ..config import StoryConfig

class BaseAgent(ABC):
    def __init__(self, name: str, config: StoryConfig):
        self.name = name
        self.config = config
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens_per_prompt
        )
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the LLM."""
        try:
            # Merging system prompt concept into single message if needed, 
            # but here we just take the prompt as is, assuming it contains everything.
            messages = [
                ("human", prompt)
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            print(f"Error generating response for {self.name}: {e}")
            return ""
