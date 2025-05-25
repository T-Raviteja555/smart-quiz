import random
from typing import List
import logging
from templates import TEMPLATES

# Mock QuizQuestion and Generator for testing (replace with actual imports)
class QuizQuestion:
    def __init__(self, type, question, options, answer, difficulty, topic, goal):
        self.type = type
        self.question = question
        self.options = options
        self.answer = answer
        self.difficulty = difficulty
        self.topic = topic
        self.goal = goal

class Generator:
    def generate(self, goal: str, difficulty: str, num_questions: int, **kwargs) -> List[QuizQuestion]:
        pass

logger = logging.getLogger(__name__)

class MathTemplateGenerator(Generator):
    def __init__(self):
        self.templates = TEMPLATES

    def generate(self, goal: str, difficulty: str, num_questions: int, **kwargs) -> List[QuizQuestion]:
        try:
            valid_templates = [t for t in self.templates if t["difficulty"] == difficulty and t["goal"] == goal]
            if not valid_templates:
                raise ValueError(f"No templates available for goal='{goal}', difficulty='{difficulty}'")
            
            questions = []
            for _ in range(num_questions):
                template = random.choice(valid_templates)
                params = template["generate_params"]()
                question_text = template["template"].render(**params)
                answer = template["compute_answer"](params)
                options = template.get("options", [])
                if callable(options):
                    options = options(params)
                
                questions.append(QuizQuestion(
                    type="mcq" if options else "short_answer",
                    question=question_text,
                    options=options,
                    answer=answer,
                    difficulty=difficulty,
                    topic=template["topic"],
                    goal=goal
                ))
            
            return questions
        
        except Exception as e:
            logger.error(f"Template generation failed: {str(e)}")
            raise ValueError(f"Failed to generate questions: {str(e)}")