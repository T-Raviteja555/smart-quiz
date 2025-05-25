import json
import os
import logging
import structlog
from typing import List, Dict, Optional
from pydantic import BaseModel
import orjson
from pathlib import Path
from cachetools import cached, TTLCache
from concurrent.futures import ThreadPoolExecutor
from app.utils.config_loader import CONFIG
from filelock import FileLock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

class QuizQuestion(BaseModel):
    type: str
    question: str
    options: Optional[List[str]]
    answer: str
    difficulty: str
    topic: str
    goal: str

    class Config:
        json_loads = orjson.loads
        json_dumps = lambda x, **kwargs: orjson.dumps(x).decode()

supported_difficulties = CONFIG.get('supported_difficulties', [])
logger.info(f"Supported difficulties: {supported_difficulties}")
# Thread-safe cache
question_cache = TTLCache(maxsize=CONFIG['CACHE_MAXSIZE'], ttl=CONFIG['CACHE_TTL'])

# Thread pool
executor = ThreadPoolExecutor(max_workers=CONFIG['MAX_WORKERS'])

def _validate_question_item(item: Dict) -> Dict:
    """Basic validation for question data with logging for problematic entries."""
    item = item.copy()
    item.setdefault('options', None)
    item.setdefault('difficulty', 'intermediate')
    item.setdefault('topic', 'general')
    item.setdefault('goal', '')
    item.setdefault('answer', '')
    
    try:
        # Validate question type
        if item.get('type') not in ('mcq', 'short_answer'):
            logger.error(
                "Invalid question type",
                question=item.get('question', 'unknown'),
                type=item.get('type'),
                error="type must be 'mcq' or 'short_answer'"
            )
            raise ValueError("type must be 'mcq' or 'short_answer'")
        
        # Validation for mcq questions
        if item.get('type') == 'mcq':
            if not item.get('options') or not isinstance(item['options'], list) or len(item['options']) != 4:
                logger.error(
                    "Invalid mcq options",
                    question=item.get('question', 'unknown'),
                    options=item.get('options'),
                    error="mcq questions must have exactly 4 options"
                )
                raise ValueError("mcq questions must have exactly 4 options")
        
        # Validation for short_answer questions
        if item.get('type') == 'short_answer':
            if item.get('options') is not None:
                if isinstance(item['options'], list) and len(item['options']) == 0:
                    logger.warning(
                        "Legacy short_answer options detected, converting to null",
                        question=item.get('question', 'unknown'),
                        options=item.get('options')
                    )
                    item['options'] = None
                else:
                    logger.error(
                        "Invalid short_answer options",
                        question=item.get('question', 'unknown'),
                        options=item.get('options'),
                        error="short_answer questions must have options set to null or an empty list"
                    )
                    raise ValueError("short_answer questions must have options set to null or an empty list")
        
        # Basic string checks
        if not isinstance(item.get('question'), str) or len(item['question']) < 10:
            logger.error(
                "Invalid question length",
                question=item.get('question', 'unknown'),
                error="question must be a string with at least 10 characters"
            )
            raise ValueError("question must be a string with at least 10 characters")
        if not isinstance(item.get('goal'), str) or not item['goal']:
            logger.error(
                "Invalid goal",
                question=item.get('question', 'unknown'),
                goal=item.get('goal'),
                error="goal must be a non-empty string"
            )
            raise ValueError("goal must be a non-empty string")
        supported_goals = CONFIG.get('supported_goals', [])
        if item['goal'] not in supported_goals:
            logger.error(
                "Invalid goal",
                question=item.get('question', 'unknown'),
                goal=item.get('goal'),
                supported_goals=supported_goals,
                error=f"goal must be one of {supported_goals}"
            )
            raise ValueError(f"goal must be one of {supported_goals}")
        if not isinstance(item.get('difficulty'), str) or item['difficulty'] not in supported_difficulties:
            logger.error(
                "Invalid difficulty",
                question=item.get('question', 'unknown'),
                difficulty=item.get('difficulty'),
                supported_difficulties=supported_difficulties,
                error=f"difficulty must be one of {supported_difficulties}"
            )
            raise ValueError(f"difficulty must be one of {supported_difficulties}")
        if not isinstance(item.get('topic'), str) or len(item['topic']) < 3:
            logger.error(
                "Invalid topic",
                question=item.get('question', 'unknown'),
                topic=item.get('topic'),
                error="topic must be a string with at least 3 characters"
            )
            raise ValueError("topic must be a string with at least 3 characters")
        if not isinstance(item.get('answer'), str) or len(item['answer']) == 0:
            logger.error(
                "Invalid answer",
                question=item.get('question', 'unknown'),
                answer=item.get('answer'),
                error="answer must be a non-empty string"
            )
            raise ValueError("answer must be a non-empty string")
    
        return item
    
    except ValueError as e:
        logger.error(
            "Validation failed for question item",
            item=item,
            error=str(e)
        )
        raise

def load_questions() -> List[QuizQuestion]:
    """Load and validate questions from file with caching and parallel processing."""
    try:
        file_path = Path(CONFIG['DATA_DIR']) / CONFIG['DATASET']
        logger.info(f"Loading questions from {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            data = orjson.loads(raw_content)

        # Handle flat list structure
        questions = data  # Direct list of questions

        # Parallel processing for large datasets
        if len(questions) > 100:
            validated_questions = list(executor.map(
                lambda item: QuizQuestion(**_validate_question_item(item)),
                questions
            ))
        else:
            # Single-threaded for small datasets
            validated_questions = [QuizQuestion(**_validate_question_item(item)) for item in questions]

        logger.info(f"Loaded {len(validated_questions)} questions")
        return validated_questions

    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
        raise ValueError(f"Failed to load questions: {str(e)}")

def get_goals_in_question_bank() -> set:
    """Return a set of unique goals present in the question bank."""
    try:
        file_path = Path(CONFIG['DATA_DIR']) / CONFIG['DATASET']
        with open(file_path, 'r', encoding='utf-8') as f:
            data = orjson.loads(f.read())
        goals = set(item.get('goal', '') for item in data if isinstance(item.get('goal', ''), str) and item.get('goal', ''))
        logger.info(f"Goals in question bank: {goals}")
        return goals
    except Exception as e:
        logger.error(f"Failed to load goals from question bank: {str(e)}")
        return set()

def count_questions_for_goal(goal: str) -> int:
    """Count the number of questions for a given goal in the question bank."""
    try:
        file_path = Path(CONFIG['DATA_DIR']) / CONFIG['DATASET']
        with open(file_path, 'r', encoding='utf-8') as f:
            data = orjson.loads(f.read())
        count = sum(1 for item in data if item.get('goal') == goal)
        logger.info(f"Counted {count} questions for goal '{goal}'")
        return count
    except Exception as e:
        logger.error(f"Failed to count questions for goal '{goal}': {str(e)}")
        return 0

def append_questions_to_bank(questions: List[QuizQuestion]):
    """Append validated questions to the question bank."""
    try:
        file_path = Path(CONFIG['DATA_DIR']) / CONFIG['DATASET']
        with FileLock(str(file_path) + ".lock"):
            # Read existing questions
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = orjson.loads(f.read())
            except (FileNotFoundError, orjson.JSONDecodeError):
                existing_data = []
            
            # Append new questions
            new_questions = [q.dict() for q in questions]
            existing_data.extend(new_questions)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4)
        
        logger.info(f"Appended {len(questions)} questions to question bank")
    except Exception as e:
        logger.error(f"Failed to append questions to question bank: {str(e)}")
        raise ValueError(f"Failed to append questions: {str(e)}")