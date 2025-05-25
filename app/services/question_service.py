import random
import structlog
from typing import List
from app.questions import load_questions, QuizQuestion
from app.utils.config_loader import CONFIG
from app.api.models import QuestionResponse, GenerateQuestionsResponse, ConfigResponse, McqQuestionResponse, ShortAnswerQuestionResponse
from app.generators.retrieval.tfidf import TfidfGenerator
from app.generators.templatRetr.mathTemplate import MathTemplateGenerator
from fastapi import HTTPException

logger = structlog.get_logger(__name__)

class QuestionService:
    def __init__(self):
        self.questions_cache = load_questions()
        self.default_generator_mode = CONFIG.get('generator_mode', 'retrieval')
        self.supported_generator_modes = CONFIG.get('supported_generator_modes', ['retrieval', 'template'])
        self.generators = {
            "retrieval": TfidfGenerator(self.questions_cache),
            "template": MathTemplateGenerator()
        }

    def display_questions(self, questions: List[QuizQuestion]):
        """Log answers for a list of questions."""
        for q in questions:
            logger.info(f"Answer: {q.answer}")

    def get_all_questions(self) -> GenerateQuestionsResponse:
        """Retrieve all questions from the cache."""
        questions = self.questions_cache
        quiz_id = f"quiz_{random.randint(1000, 9999)}"
        response_questions = [
            McqQuestionResponse(
                type=q.type,
                question=q.question,
                options=q.options,
                answer=q.answer,
                difficulty=q.difficulty,
                topic=q.topic
            ) if q.type == 'mcq' else ShortAnswerQuestionResponse(
                type=q.type,
                question=q.question,
                answer=q.answer,
                difficulty=q.difficulty,
                topic=q.topic
            ) for q in questions
        ]
        return GenerateQuestionsResponse(
            quiz_id=quiz_id,
            goal=questions[0].goal if questions else "GATE AE",
            questions=response_questions
        )

    def generate_quiz(self, goal: str, difficulty: str, num_questions: int, mode: str = None) -> GenerateQuestionsResponse:
        """Generate a quiz based on goal, difficulty, number of questions, and mode."""
        try:
            supported_goals = CONFIG['supported_goals']
            if goal not in supported_goals:
                raise HTTPException(status_code=400, detail=f"Goal must be one of {supported_goals}")
            if difficulty not in CONFIG['supported_difficulties']:
                raise HTTPException(status_code=400, detail=f"Difficulty must be one of {CONFIG['supported_difficulties']}")
            
            selected_mode = mode if mode else self.default_generator_mode
            if selected_mode not in self.supported_generator_modes:
                raise HTTPException(status_code=400, detail=f"Mode must be one of {self.supported_generator_modes}")
            
            if selected_mode == "retrieval" and not self.questions_cache:
                raise HTTPException(status_code=500, detail="Question bank not available")
            
            generator = self.generators[selected_mode]
            questions = generator.generate(goal, difficulty, num_questions)
            
            response_questions = [
                McqQuestionResponse(
                    type=q.type,
                    question=q.question,
                    options=q.options,
                    answer=q.answer,
                    difficulty=q.difficulty,
                    topic=q.topic
                ) if q.type == 'mcq' else ShortAnswerQuestionResponse(
                    type=q.type,
                    question=q.question,
                    answer=q.answer,
                    difficulty=q.difficulty,
                    topic=q.topic
                ) for q in questions
            ]
            return GenerateQuestionsResponse(
                quiz_id=f"quiz_{random.randint(1000, 9999)}",
                goal=goal,
                questions=response_questions
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_config(self) -> ConfigResponse:
        """Retrieve configuration details."""
        try:
            config_data = {
                "generator_mode": self.default_generator_mode,
                "version": CONFIG.get("version", "unknown"),
                "goal": CONFIG.get("supported_goals", ["unknown"]),
                "type": CONFIG.get("supported_types", ["unknown"])
            }
            logger.info(
                "Configuration retrieved",
                generator_mode=config_data["generator_mode"],
                version=config_data["version"]
            )
            return ConfigResponse(**config_data)
        except Exception as e:
            logger.error("Failed to retrieve configuration", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve configuration")