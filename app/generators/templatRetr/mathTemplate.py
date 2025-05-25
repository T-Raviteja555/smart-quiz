import random
from typing import List
from app.questions import QuizQuestion
from app.generators.base import Generator
from jinja2 import Template
from sympy import symbols, Eq, solve
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MathTemplateGenerator(Generator):
    def __init__(self):
        self.templates = [
            {
                "template": Template("Solve {{a}}x² + {{b}}x + {{c}} = 0 for x."),
                "difficulty": "beginner",
                "topic": "algebra",
                "generate_params": lambda: {
                    "a": np.random.randint(1, 6),
                    "b": np.random.randint(-5, 6),
                    "c": np.random.randint(-5, 6)
                },
                "compute_answer": lambda params: self.solve_quadratic(params["a"], params["b"], params["c"])
            },
            {
                "template": Template("The thrust of a jet engine with mass flow rate {{m}} kg/s and exhaust velocity {{v}} m/s is (in kN, to one decimal place):"),
                "difficulty": "beginner",
                "topic": "propulsion",
                "generate_params": lambda: {
                    "m": np.random.randint(40, 60),
                    "v": np.random.randint(500, 700)
                },
                "compute_answer": lambda params: f"{(params['m'] * params['v'] / 1000):.1f}"
            }
        ]

    def solve_quadratic(self, a: int, b: int, c: int) -> str:
        x = symbols('x')
        equation = Eq(a*x**2 + b*x + c, 0)
        roots = solve(equation, x)
        return ", ".join(str(root) for root in roots)

    def generate(self, goal: str, difficulty: str, num_questions: int, **kwargs) -> List[QuizQuestion]:
        try:
            valid_templates = [t for t in self.templates if t["difficulty"] == difficulty]
            if not valid_templates:
                raise ValueError(f"No templates available for difficulty = '{difficulty}'")
            
            questions = []
            for _ in range(num_questions):
                template = random.choice(valid_templates)
                params = template["generate_params"]()
                question_text = template["template"].render(**params)
                answer = template["compute_answer"](params)
                
                questions.append(QuizQuestion(
                    type="short_answer",
                    question=question_text,
                    options=None,  # Explicitly set to None for short_answer
                    answer=answer,
                    difficulty=difficulty,
                    topic=template["topic"],
                    goal=goal
                ))
            
            return questions
        
        except Exception as e:
            logger.error(f"Template generation failed: {str(e)}")
            raise ValueError(f"Failed to generate questions: {str(e)}")