import unittest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.questions import Question, generate_questions

class TestGenerateEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_questions = [
            Question(
                question_no=i,
                goal="GATE AE",
                type="mcq",
                question=f"Question {i}",
                answer_text="Answer",
                options=["A", "B", "C", "D"],
                answer_option="A",
                difficulty="beginner",
                topic="general"
            ) for i in range(1, 11)
        ]

    @patch('app.questions.load_questions')
    def test_generate_questions_success(self, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 5,
                "difficulty": "beginner"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 10)
        self.assertEqual(len(data["questions"]), 5)

    @patch('app.questions.load_questions')
    def test_generate_questions_invalid_difficulty(self, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 5,
                "difficulty": "invalid"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Difficulty must be one of", response.json()["detail"])

    @patch('app.questions.load_questions')
    def test_generate_questions_invalid_goal(self, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        response = self.client.post(
            "/generate",
            json={
                "goal": "Invalid Goal",
                "num_questions": 5,
                "difficulty": "beginner"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Goal must be one of", response.json()["detail"])

    def test_generate_questions_validation_error(self):
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": -1,
                "difficulty": "beginner"
            }
        )
        self.assertEqual(response.status_code, 422)
        self.assertTrue(isinstance(response.json()["detail"], list))

    @patch('app.questions.load_questions', side_effect=Exception("Database error"))
    def test_generate_questions_server_error(self, mock_load_questions):
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 5,
                "difficulty": "beginner"
            }
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Internal server error")

    def test_exception_handler_registration(self):
        from fastapi.exceptions import RequestValidationError
        from app.utils.exceptions import ServiceUnavailableError
        expected_handlers = [Exception, RequestValidationError, HTTPException, ServiceUnavailableError]
        registered_handlers = list(app.exception_handlers.keys())
        for handler in expected_handlers:
            self.assertIn(handler, registered_handlers, f"Handler for {handler} not registered")

    @patch('app.main.questions_cache', new_callable=list)
    def test_health_check_healthy(self, mock_questions_cache):
        mock_questions_cache.extend(self.mock_questions)
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("question_bank", data["details"])
        self.assertIn("configuration", data["details"])
        self.assertEqual(data["details"]["question_bank"], "Available (10 questions)")
        self.assertEqual(data["details"]["configuration"], "Loaded successfully")

    @patch('app.main.questions_cache', new_callable=list)
    @patch('app.main.CONFIG', {})
    def test_health_check_unhealthy(self, mock_questions_cache):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertIn("question_bank", data["details"])
        self.assertIn("configuration", data["details"])
        self.assertEqual(data["details"]["question_bank"], "Available (0 questions)")
        self.assertIn("Missing keys: supported_difficulties, supported_types", data["details"]["configuration"])

if __name__ == '__main__':
    result = unittest.main(verbosity=2, exit=False)
    if result.wasSuccessful():
        print("Success: All tests passed!")
    else:
        print("Failure: Some tests did not pass.")