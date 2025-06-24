import random
import structlog
import json
from typing import List, Optional
from app.questions import load_questions, QuizQuestion, get_goals_in_question_bank, count_questions_for_goal, append_questions_to_bank, question_cache, _validate_question_item
from app.utils.config_loader import CONFIG
from app.api.models import QuestionResponse, GenerateQuestionsResponse, ConfigResponse, McqQuestionResponse, ShortAnswerQuestionResponse, GoalResponse
from app.generators.tfidfRetrieval.tfidfGenerator import TfidfGenerator
from app.generators.templateRetrieval.templateGenerator import QuestionTemplateGenerator
from fastapi import HTTPException
from filelock import FileLock
from pathlib import Path

logger = structlog.get_logger(__name__)

class QuestionService:
    def __init__(self):
        self.questions_cache = load_questions()
        self.default_generator_mode = CONFIG.get('generator_mode', 'retrieval')
        self.supported_generator_modes = CONFIG.get('supported_generator_modes', ['retrieval', 'template'])
        self.generators = {
            "retrieval": TfidfGenerator(self.questions_cache),
            "template": QuestionTemplateGenerator()
        }
        self.config_path = Path("config.json")
        self.schema_path = Path("schema.json")
        self.token_path = Path("api_tokens.json")
        # Load API token
        try:
            with open(self.token_path, 'r', encoding='utf-8') as f:
                self.api_token = json.load(f).get('api_token')
        except Exception as e:
            logger.error(f"Failed to load API token: {str(e)}")
            raise ValueError("API token configuration missing or invalid")

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
            goal=questions[0].goal if questions else "GATE",
            questions=response_questions
        ) 

    def generate_quiz(self, goal: str, difficulty: str, num_questions: int, mode: str = None) -> GenerateQuestionsResponse:
        """Generate a quiz based on goal, difficulty, number of questions, and mode."""
        try:
            supported_goals = CONFIG.get('supported_goals', [])
            if not supported_goals:
                raise HTTPException(status_code=500, detail="No supported goals available")
            if goal not in supported_goals:
                raise HTTPException(status_code=400, detail=f"Goal '{goal}' not in supported goals: {supported_goals}")
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

    def add_goal(self, goal: str, questions: Optional[List[QuizQuestion]] = None, api_token: str = None) -> GoalResponse:
        """Add a new goal to supported_goals or append questions if goal exists, update config.json and schema.json."""
        try:
            # Validate API token
            if api_token != self.api_token:
                raise HTTPException(status_code=401, detail="Invalid API token")
            
            supported_goals = CONFIG.get('supported_goals', [])
            
            # Validate provided questions
            validated_questions = []
            if questions:
                for q in questions:
                    if q.goal != goal:
                        raise HTTPException(status_code=400, detail=f"Question goal '{q.goal}' does not match requested goal '{goal}'")
                    # Convert to dict for validation
                    q_dict = q.dict()
                    validated_q = _validate_question_item(q_dict)
                    validated_questions.append(QuizQuestion(**validated_q))
            
            # Check question count
            existing_count = count_questions_for_goal(goal)
            provided_count = len(validated_questions) if validated_questions else 0
            total_count = existing_count + provided_count
            
            # If goal already exists, append questions only
            if goal in supported_goals:
                if not validated_questions:
                    raise HTTPException(status_code=400, detail=f"Goal '{goal}' already exists; provide questions to append")
                append_questions_to_bank(validated_questions)
                # Clear cache to reload updated question bank
                question_cache.clear()
                self.questions_cache = load_questions()
                logger.info(f"Appended {provided_count} questions for existing goal '{goal}' to question bank")
                return GoalResponse(
                    message=f"Appended {provided_count} questions to existing goal '{goal}'",
                    supported_goals=supported_goals
                )
            
            # For new goal, ensure minimum 10 questions
            if total_count < 10:
                raise HTTPException(
                    status_code=400,
                    detail=f"Goal '{goal}' has {total_count} questions (existing: {existing_count}, provided: {provided_count}); minimum 10 required"
                )
            
            # Check if goal exists in question bank or provided questions
            if existing_count == 0 and provided_count == 0:
                raise HTTPException(status_code=400, detail=f"Goal '{goal}' not found in question bank and no questions provided")
            
            # Append questions to question bank
            if validated_questions:
                append_questions_to_bank(validated_questions)
                # Clear cache to reload updated question bank
                question_cache.clear()
                self.questions_cache = load_questions()
                logger.info(f"Appended {provided_count} questions for goal '{goal}' to question bank")
            
            # Update config.json
            with FileLock(str(self.config_path) + ".lock"):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                config_data['supported_goals'].append(goal)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4)
                CONFIG['supported_goals'] = config_data['supported_goals']
                
                # Update schema.json
                self._update_schema_json()
            
            logger.info(f"Goal '{goal}' added to supported goals", supported_goals=CONFIG['supported_goals'])
            return GoalResponse(
                message=f"Goal '{goal}' added successfully with {total_count} questions",
                supported_goals=CONFIG['supported_goals']
            )
        except Exception as e:
            logger.error(f"Failed to add goal '{goal}'", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to add goal: {str(e)}")

    def remove_goal(self, goal: str, api_token: str = None) -> GoalResponse:
        """Remove a goal from supported_goals, update config.json and schema.json."""
        try:
            # Validate API token
            if api_token != self.api_token:
                raise HTTPException(status_code=401, detail="Invalid API token")
            
            supported_goals = CONFIG.get('supported_goals', [])
            if goal not in supported_goals:
                raise HTTPException(status_code=400, detail=f"Goal '{goal}' not in supported goals")
            if goal in get_goals_in_question_bank():
                raise HTTPException(status_code=400, detail=f"Cannot remove goal '{goal}' as it is still present in question bank")
            
            with FileLock(str(self.config_path) + ".lock"):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                config_data['supported_goals'].remove(goal)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4)
                CONFIG['supported_goals'] = config_data['supported_goals']
                
                # Update schema.json
                self._update_schema_json()
            
            logger.info(f"Goal '{goal}' removed from supported goals", supported_goals=CONFIG['supported_goals'])
            return GoalResponse(
                message=f"Goal '{goal}' removed successfully",
                supported_goals=CONFIG['supported_goals']
            )
        except Exception as e:
            logger.error(f"Failed to remove goal '{goal}'", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to remove goal: {str(e)}")

    def _update_schema_json(self):
        """Update schema.json with supported_goals for GenerateQuestionsRequest.goal."""
        try:
            with FileLock(str(self.schema_path) + ".lock"):
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                schema['definitions']['inputRequest']['properties']['goal']['enum'] = CONFIG.get('supported_goals', [])
                schema['definitions']['outputResponse']['properties']['goal']['enum'] = CONFIG.get('supported_goals', [])
                with open(self.schema_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=4)
            logger.info("Updated schema.json", supported_goals=CONFIG['supported_goals'])
        except Exception as e:
            logger.error(f"Failed to update schema.json", error=str(e))
            raise

    def get_config(self) -> ConfigResponse:
        """Retrieve configuration details."""
        try:
            config_data = {
                "generator_mode": self.default_generator_mode,
                "version": CONFIG.get("version", "unknown"),
                "goal": CONFIG.get("supported_goals", []),
                "type": CONFIG.get("supported_types", ["unknown"])
            }
            logger.info(
                "Configuration retrieved",
                generator_mode=config_data["generator_mode"],
                version=config_data["version"],
                goals=config_data["goal"]
            )
            return ConfigResponse(**config_data)
        except Exception as e:
            logger.error("Failed to retrieve configuration", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve configuration")