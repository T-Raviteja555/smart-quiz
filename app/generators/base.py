from abc import ABC, abstractmethod
from typing import List
from app.questions import QuizQuestion

class Generator(ABC):
    @abstractmethod
    def generate(self, goal: str, difficulty: str, num_questions: int, **kwargs) -> List[QuizQuestion]:
        """Generate questions based on input parameters."""
        pass