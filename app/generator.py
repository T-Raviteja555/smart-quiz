import json
import string
from typing import List, Dict, Optional
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path

# Download NLTK data (ensure this is done once during setup)
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab',quiet=True)
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Configuration constants
CONFIG = {
    "DATA_DIR": Path("E:/smart-quiz/data"),
    "DATSET": "consolidated_questions_updated.json",
    "CACHE_TTL": 3600,
    "CACHE_MAXSIZE": 1000,
    "MAX_WORKERS": 4,
    "MAX_QUESTIONS": 10,
    "MIN_QUESTIONS": 5
}
class QuizGenerator:
    def __init__(self, data_path: str, config_path: str):
        """
        Initialize the quiz generator with question bank and configuration.
        
        Args:
            data_path (str): Path to the question bank JSON file.
            config_path (str): Path to the config.json file.
        """
        self.stop_words = set(stopwords.words('english'))
        self.data_path = Path(data_path)
        self.config_path = Path(config_path)
        
        # Load configuration
        if not self.config_path.exists():
            raise FileNotFoundError("config.json is missing")
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        # Validate configuration
        self.max_questions = self.config.get('max_questions', 10)
        self.supported_difficulties = self.config.get('supported_difficulties', 
                                                   ['beginner', 'intermediate', 'advanced'])
        self.supported_types = self.config.get('supported_types', ['mcq', 'short_answer'])
        
        # Load question bank
        if not self.data_path.exists():
            raise FileNotFoundError("Question bank JSON is missing")
        with open(self.data_path, 'r',encoding='utf-8') as f:
            self.question_bank = json.load(f)['quizzes']
        
        # Preprocess questions and build TF-IDF model
        self.documents = []
        self.metadata = []
        self._prepare_documents()
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
        print("tfidf_matrix",self.tfidf_matrix)
        
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text by tokenizing, removing stopwords, and cleaning.
        
        Args:
            text (str): Input text to preprocess.
        
        Returns:
            str: Processed text.
        """
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and non-alphabetic tokens
        tokens = [t for t in tokens if t.isalpha() and t not in self.stop_words]
        return ' '.join(tokens)
    
    def _prepare_documents(self):
        """
        Prepare documents for TF-IDF by combining question, goal, and topic.
        Store metadata for retrieval.
        """
        for quiz in self.question_bank:
            goal = quiz['goal']
            q_type = quiz['type']
            for question in quiz['questions']:
                # Combine question text, goal, and topic for better context
                text = question['question']
                topic = question.get('topic', '')
                doc = f"{text} {goal} {topic}"
                self.documents.append(self._preprocess_text(doc))
                self.metadata.append({
                    'goal': goal,
                    'type': q_type,
                    'question': question['question'],
                    'options': question.get('options', []),
                    'answer': question['answer_text'],
                    'difficulty': question['difficulty'],
                    'topic': topic
                })
    
    def generate_quiz(self, goal: str, num_questions: int, difficulty: str, topic: Optional[str] = None) -> Dict:
        """
        Generate a quiz based on user input.
        
        Args:
            goal (str): Target domain (e.g., 'Amazon SDE', 'GATE').
            num_questions (int): Number of questions to return.
            difficulty (str): Difficulty level ('beginner', 'intermediate', 'advanced').
            topic (Optional[str]): Specific topic to filter (e.g., 'Algorithms').
        
        Returns:
            Dict: Quiz response in the specified JSON format.
        """
        # Validate inputs
        if difficulty not in self.supported_difficulties:
            raise ValueError(f"Difficulty must be one of {self.supported_difficulties}")
        if num_questions > self.max_questions:
            raise ValueError(f"Number of questions exceeds maximum limit of {self.max_questions}")
        
        # Construct query
        query = f"{goal} {difficulty}"
        if topic:
            query += f" {topic}"
        query = self._preprocess_text(query)
        print ("query=",query)
        # Transform query to TF-IDF vector
        query_vector = self.vectorizer.transform([query])
        print ("query_vector=",query_vector)
        # Compute cosine similarity
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        print ("similarities=",similarities)
        # Get top matching questions
        top_indices = np.argsort(similarities)[::-1]
        selected_questions = []
        used_indices = set()
        
        for idx in top_indices:
            if len(selected_questions) >= num_questions:
                break
            meta = self.metadata[idx]
            # Apply filters
            if (meta['goal'].lower() == goal.lower() and 
                meta['difficulty'].lower() == difficulty.lower() and
                idx not in used_indices):
                if topic and meta['topic'].lower() != topic.lower():
                    continue
                question = {
                    'type': meta['type'],
                    'question': meta['question'],
                    'options': meta['options'] if meta['type'] == 'mcq' else [],
                    'answer': meta['answer'],
                    'difficulty': meta['difficulty'],
                    'topic': meta['topic']
                }
                selected_questions.append(question)
                used_indices.add(idx)
        
        # Generate quiz response
        quiz_id = f"quiz_{np.random.randint(1000, 9999)}"
        return {
            'quiz_id': quiz_id,
            'goal': goal,
            'questions': selected_questions
        }

if __name__ == "__main__":
    # Example usage
    generator = QuizGenerator(
        data_path=CONFIG["DATA_DIR"] / "All_Questions.json",
        config_path=CONFIG["DATA_DIR"] / "config.json"
    )
    quiz = generator.generate_quiz(
        goal="GATE",
        num_questions=5,
        difficulty="beginner",
        topic="General Aptitude"
    )
    print(json.dumps(quiz, indent=2)) 