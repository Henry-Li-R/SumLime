from abc import ABC, abstractmethod

class LLMProvider(ABC):
    
    #SUMMARIZE_MESSAGE = "Compare and summarize the following outputs by different LLMs."
    # "You are a fact-checking assistant. Reply with 'Supported', 'Not Supported', or 'Uncertain', followed by a short explanation on a new line."
    
    @abstractmethod
    def query(self, prompt: str, system_message="") -> str:
        pass