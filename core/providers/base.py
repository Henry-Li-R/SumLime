from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def query(self, prompt: str) -> str:
        pass