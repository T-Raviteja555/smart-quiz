from typing import List
from app.questions import QuizQuestion
from app.generators.base import Generator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import random
from cachetools import cached, TTLCache
from app.utils.config_loader import CONFIG
import logging

logger = logging.getLogger(__name__)

tfidf_cache = TTLCache(maxsize=CONFIG['CACHE_MAXSIZE'], ttl=CONFIG['CACHE_TTL'])

def preprocess_text(text: str) -> str:
    import string
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text

@cached(tfidf_cache)
def get_tfidf_matrix(questions: List[QuizQuestion], cache_key: str) -> tuple:
    documents = [preprocess_text(f"{q.question} {q.goal} {q.topic}") for q in questions]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    return vectorizer, tfidf_matrix

class TfidfGenerator(Generator):
    def __init__(self, questions: List[QuizQuestion]):
        self.questions = questions

    def generate(self, goal: str, difficulty: str, num_questions: int, **kwargs) -> List[QuizQuestion]:
        matching_questions = [q for q in self.questions if q.goal == goal and q.difficulty == difficulty]
        
        if not matching_questions:
            raise ValueError(f"No questions available for goal '{goal}' and difficulty '{difficulty}'")
        
        if num_questions > CONFIG['max_questions']:
            num_questions = CONFIG['max_questions']
        if num_questions < CONFIG['default_num_questions']:
            num_questions = CONFIG['default_num_questions']
        
        if len(matching_questions) < num_questions:
            raise ValueError(
                f"Requested {num_questions} questions, but only {len(matching_questions)} "
                f"available for goal '{goal}' and difficulty '{difficulty}'"
            )
        
        documents = [preprocess_text(f"{q.question} {q.goal} {q.topic}") for q in matching_questions]
        query = preprocess_text(goal)
        
        try:
            cache_key = f"{goal}_{difficulty}"
            vectorizer, tfidf_matrix = get_tfidf_matrix(matching_questions, cache_key)
            query_vector = vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            top_indices = np.argsort(similarities)[::-1][:num_questions]
            
            if len(top_indices) < num_questions:
                logger.warning(
                    f"Only {len(top_indices)} relevant questions found for goal '{goal}', "
                    f"difficulty '{difficulty}'. Falling back to random sampling."
                )
                return random.sample(matching_questions, num_questions)
            
            # Ensure options is None for short_answer questions
            selected_questions = []
            for i in top_indices:
                q = matching_questions[i]
                selected_questions.append(QuizQuestion(
                    type=q.type,
                    question=q.question,
                    options=None if q.type == 'short_answer' else q.options,
                    answer=q.answer,
                    difficulty=q.difficulty,
                    topic=q.topic,
                    goal=q.goal
                ))
            return selected_questions
        
        except Exception as e:
            logger.error(f"TF-IDF retrieval failed: {str(e)}. Falling back to random sampling.")
            return random.sample(matching_questions, num_questions)