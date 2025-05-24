import os
import logging
from typing import List, Dict
from pydantic import BaseModel
import orjson
from pathlib import Path
from cachetools import cached, TTLCache
from concurrent.futures import ThreadPoolExecutor
from app.utils.config_loader import CONFIG
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizQuestion(BaseModel):
    type: str
    question: str
    options: List[str]
    answer: str
    difficulty: str
    topic: str
    goal: str

    class Config:
        json_loads = orjson.loads
        json_dumps = lambda x, **kwargs: orjson.dumps(x).decode()

supported_goals = CONFIG.get('supported_goals', [])
logger.info(f"Valid goals: {supported_goals}")
supported_difficulties = CONFIG.get('supported_difficulties', [])
logger.info(f"Supported difficulties: {supported_difficulties}")
# Thread-safe cache
question_cache = TTLCache(maxsize=CONFIG['CACHE_MAXSIZE'], ttl=CONFIG['CACHE_TTL'])

# Thread pool
executor = ThreadPoolExecutor(max_workers=CONFIG['MAX_WORKERS'])

def _validate_question_item(item: Dict) -> Dict:
    """Basic validation for question data"""
    item = item.copy()
    item.setdefault('options', [])
    item.setdefault('difficulty', 'intermediate')
    item.setdefault('topic', 'general')
    item.setdefault('goal', '')
    item.setdefault('answer', '')
    
    # Validate question type
    if item.get('type') not in ('mcq', 'short_answer'):
        raise ValueError("type must be 'mcq' or 'short_answer'")
    
    # Validation for mcq questions
    if item.get('type') == 'mcq':
        if not item.get('options') or not isinstance(item['options'], list) or len(item['options']) != 4:
            raise ValueError("mcq questions must have exactly 4 options")
    
    # Validation for short_answer questions
    if item.get('type') == 'short_answer':
        if item.get('options') != []:
            raise ValueError("short_answer questions must have empty options list")
    
    # Basic string checks
    if not isinstance(item.get('question'), str) or len(item['question']) < 10:
        raise ValueError("question must be a string with at least 10 characters")
    if not isinstance(item.get('goal'), str) or item['goal'] not in supported_goals:
        raise ValueError(f"goal must be one of {supported_goals}")
    if not isinstance(item.get('difficulty'), str) or item['difficulty'] not in supported_difficulties:
        raise ValueError(f"difficulty must be one of {supported_difficulties}")
    if not isinstance(item.get('topic'), str) or len(item['topic']) < 3:
        raise ValueError("topic must be a string with at least 3 characters")
    if not isinstance(item.get('answer'), str) or len(item['answer']) == 0:
        raise ValueError("answer must be a non-empty string")
    
    return item

@cached(question_cache)
def load_questions() -> List[QuizQuestion]:
    """Load and validate questions from file with caching and parallel processing"""
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
            return list(executor.map(
                lambda item: QuizQuestion(**_validate_question_item(item)),
                questions
            ))

        # Single-threaded for small datasets
        return [QuizQuestion(**_validate_question_item(item)) for item in questions]

    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
        raise ValueError(f"Failed to load questions: {str(e)}")

def generate_questions(goal: str, difficulty: str, no_of_questions: int) -> List[QuizQuestion]:
    """Generate random questions based on goal and difficulty"""
    questions = load_questions()
    # Filter questions by goal and difficulty
    matching_questions = [q for q in questions if q.goal == goal and q.difficulty == difficulty]

    # Check if enough questions are available
    if len(matching_questions) < no_of_questions:
        raise ValueError(
            f"Requested {no_of_questions} questions, but only {len(matching_questions)} "
            f"available for goal '{goal}' and difficulty '{difficulty}'"
        )
    
    # Adjust number of questions based on config constraints
    if no_of_questions > CONFIG['max_questions']:
        no_of_questions = CONFIG['max_questions']
    if no_of_questions < CONFIG['default_num_questions']:
        no_of_questions = CONFIG['default_num_questions']
    
    # Return random sample of questions
    return random.sample(matching_questions, no_of_questions)