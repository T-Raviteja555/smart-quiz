import os
import logging
import random
from typing import List, Optional, Dict
from pydantic import BaseModel 
import orjson 
from pathlib import Path
from cachetools import cached, TTLCache
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from app.utils.config_loader import CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""class Question(BaseModel):
   
    goal: str
    type: str
    question: str
    answer_text: str = ''
    options: Optional[List[str]] = None
    answer_option: Optional[str] = None
    difficulty: str = 'medium'
    topic: str = 'general'"""
    
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

# Thread-safe cache
question_cache = TTLCache(maxsize=CONFIG['CACHE_MAXSIZE'], ttl=CONFIG['CACHE_TTL'])

# Thread pool
executor = ThreadPoolExecutor(max_workers=CONFIG['MAX_WORKERS'])

def _validate_question_item(item: Dict) -> Dict:
    """Basic validation for question data"""
    
    # Basic type checking and defaults
    item = item.copy()
    item.setdefault('answer', '')
    item.setdefault('options', None)
    item.setdefault('difficulty', 'medium')
    item.setdefault('topic', 'general')
    item.setdefault('goal', '')
    
    # Validate question type
    """if item.get('type') not in ('mcq', 'short_answer'):
        raise ValueError("type must be 'mcq' or 'short_answer'")
    
    # Validation for mcq questions
    if item.get('type') == 'mcq':
        if not item.get('options') or not isinstance(item['options'], list) or len(item['options']) != 4:
            raise ValueError("mcq questions must have exactly 4 options")
        if item.get('answer_option') and item['answer_option'] not in ('A', 'B', 'C', 'D'):
            raise ValueError("answer_option for mcq must be 'A', 'B', 'C', or 'D'")
    """
    # Basic string checks
    if not isinstance(item.get('question'), str) or len(item['question']) < 10:
        raise ValueError("question must be a string with at least 10 characters")
    if not isinstance(item.get('goal'), str) or len(item['goal']) < 3:
        raise ValueError("goal must be a string with at least 3 characters")
    
    return item

@cached(question_cache)
def load_questions() -> List[QuizQuestion]:
    """Load and validate questions from file with caching and parallel processing"""
    try:
        file_path = Path(CONFIG['DATA_DIR']) / CONFIG['DATASET']  # Fixed typo: DATSET -> DATASET
        logger.info(f"Loading questions from {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            data = orjson.loads(raw_content)

        # Handle nested structure from All_Questions.json
        questions = []
        for quiz in data.get('quizzes', []):
            for idx, question in enumerate(quiz.get('questions', [])):
                adapted_question = {
                    'type': quiz['type'],
                    'question': question['question'],
                    'options': question.get('options', []),
                    'answer': question['answer'],
                    'difficulty': question['difficulty'],
                    'topic': question['topic'],
                    'goal': quiz['goal'],
                }
                questions.append(adapted_question)

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
@lru_cache(maxsize=100)
def get_question_by_id(question_id: int) -> Optional[QuizQuestion]:
    """Retrieve single question by ID with caching"""
    questions = load_questions()
    return next((q for q in questions if q.question_no == question_id), None)

def generate_questions(goal: str, difficulty: str, no_of_questions: int) -> List[QuizQuestion]:
    """Generate random questions based on goal and difficulty"""
    questions = load_questions()
    # Filter questions by goal and difficulty
    matching_questions = [q for q in questions if q.goal == goal and q.difficulty == difficulty]

    # Check if enough questions are available
    if len(matching_questions) < CONFIG['default_num_questions']:
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