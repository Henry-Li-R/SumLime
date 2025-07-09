from abc import ABC, abstractmethod

class LLMProvider(ABC):
    
    SYSTEM_MESSAGE = "You are a fact-checking assistant. Reply with 'Supported', 'Not Supported', or 'Uncertain', followed by a short explanation on a new line."
    
    @abstractmethod
    def query(self, prompt: str) -> str:
        pass