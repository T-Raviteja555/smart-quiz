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
nltk.download('punkt_tab', quiet=True)
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
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.question_bank = json.load(f)['quizzes']
        
        # Preprocess questions and build TF-IDF model
        self.documents = []
        self.metadata = []
        self._prepare_documents()
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
        print("TF-IDF matrix shape:", self.tfidf_matrix.shape)
        
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text by tokenizing, removing stopwords, and cleaning.
        
        Args:
            text (str): Input text to preprocess.
        
        Returns:
            str: Processed text.
        """
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        tokens = word_tokenize(text)
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
        if difficulty not in self.supported_difficulties:
            raise ValueError(f"Difficulty must be one of {self.supported_difficulties}")
        if num_questions > self.max_questions:
            raise ValueError(f"Number of questions exceeds maximum limit of {self.max_questions}")
        
        query = f"{goal} {difficulty}"
        if topic:
            query += f" {topic}"
        query = self._preprocess_text(query)
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        top_indices = np.argsort(similarities)[::-1]
        selected_questions = []
        used_indices = set()
        
        for idx in top_indices:
            if len(selected_questions) >= num_questions:
                break
            meta = self.metadata[idx]
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
        
        quiz_id = f"quiz_{np.random.randint(1000, 9999)}"
        return {
            'quiz_id': quiz_id,
            'goal': goal,
            'questions': selected_questions
        }

def evaluate_quiz(quiz: Dict, expected_goal: str, expected_difficulty: str, expected_topic: Optional[str]) -> float:
    """
    Evaluate the relevance of quiz questions based on expected criteria.
    
    Args:
        quiz (Dict): Generated quiz dictionary.
        expected_goal (str): Expected goal (e.g., 'GATE').
        expected_difficulty (str): Expected difficulty (e.g., 'beginner').
        expected_topic (Optional[str]): Expected topic (e.g., 'General Aptitude').
    
    Returns:
        float: Proportion of questions matching the criteria.
    """
    questions = quiz['questions']
    correct = sum(1 for q in questions if 
                  q['difficulty'].lower() == expected_difficulty.lower() and (not expected_topic or q['topic'].lower() == expected_topic.lower()))
    return correct / len(questions) if questions else 0

def precision_at_k(quiz: Dict, expected_goal: str, expected_difficulty: str, expected_topic: Optional[str], k: int) -> float:
    """
    Calculate Precision@k for the quiz questions.
    
    Args:
        quiz (Dict): Generated quiz dictionary.
        expected_goal (str): Expected goal.
        expected_difficulty (str): Expected difficulty.
        expected_topic (Optional[str]): Expected topic.
        k (int): Number of top questions to consider.
    
    Returns:
        float: Proportion of top-k questions that are relevant.
    """
    questions = quiz['questions'][:k]
    correct = sum(1 for q in questions if 
                  q['difficulty'].lower() == expected_difficulty.lower() and
                  (not expected_topic or q['topic'].lower() == expected_topic.lower()))
    return correct / k if questions else 0

if __name__ == "__main__":
    # Initialize QuizGenerator
    try:
        generator = QuizGenerator(
            data_path=CONFIG["DATA_DIR"] / "All_Questions.json",
            config_path=CONFIG["DATA_DIR"] / "config.json"
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)

    # Define test queries
    test_queries = [
        {"goal": "GATE", "num_questions": 5, "difficulty": "beginner", "topic": "General Aptitude"},
        {"goal": "Amazon SDE", "num_questions": 3, "difficulty": "intermediate", "topic": "Algorithms"},
        {"goal": "GATE", "num_questions": 4, "difficulty": "advanced", "topic": "Mathematics"}
    ]

    # Evaluate and log results
    output_file = CONFIG["DATA_DIR"] / "evaluation_results.txt" 
    print("Evaluating QuizGenerator...")
    with open(output_file, "w", encoding='utf-8') as f:
        for query in test_queries:
            try:
                quiz = generator.generate_quiz(**query)
                accuracy = evaluate_quiz(quiz, query["goal"], query["difficulty"], query["topic"])
                precision = precision_at_k(quiz, query["goal"], query["difficulty"], query["topic"], k=query["num_questions"])
                
                # Print results
                print(f"\nQuery: {query}")
                print(f"Relevance Accuracy: {accuracy:.2f}")
                print(f"Precision@{query['num_questions']}: {precision:.2f}")
                print("Generated Quiz:")
                print(json.dumps(quiz, indent=2))
                
                # Log to file
                f.write(f"Query: {query}\n")
                f.write(f"Relevance Accuracy: {accuracy:.2f}\n")
                f.write(f"Precision@{query['num_questions']}: {precision:.2f}\n")
                f.write("Generated Quiz:\n")
                f.write(json.dumps(quiz, indent=2))
                f.write("\n\n")
                
            except ValueError as e:
                error_msg = f"Error for query {query}: {e}"
                print(error_msg)
                f.write(error_msg + "\n\n")

    print(f"\nEvaluation results saved to {output_file}")