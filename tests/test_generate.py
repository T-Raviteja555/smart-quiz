import unittest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.questions import QuizQuestion
from app.api.models import GenerateQuestionsResponse, HealthCheckResponse

class TestGenerateEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_questions = [
            QuizQuestion(
                type="mcq",
                question=f"Question about {goal} {i}",
                options=["A", "B", "C", "D"],
                answer="A",
                difficulty="beginner",
                topic="algorithms",
                goal=goal
            ) for i, goal in enumerate(["GATE AE", "GATE AE", "Amazon SDE", "Amazon SDE", "GATE AE"], 1)
        ] + [
            QuizQuestion(
                type="short_answer",
                question=f"Short answer question {i}",
                options=None,
                answer="Answer",
                difficulty="beginner",
                topic="general",
                goal="GATE AE"
            ) for i in range(6, 11)
        ]

    @patch('app.services.question_service.QuestionService.generate_quiz')
    def test_generate_questions_retrieval_success(self, mock_generate_quiz):
        mock_response = GenerateQuestionsResponse(
            quiz_id="quiz_1234",
            goal="GATE AE",
            questions=[
                {
                    "type": q.type,
                    "question": q.question,
                    "options": q.options,
                    "answer": q.answer,
                    "difficulty": q.difficulty,
                    "topic": q.topic
                } for q in self.mock_questions[:5]
            ]
        )
        mock_generate_quiz.return_value = mock_response
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 5,
                "difficulty": "beginner",
                "mode": "retrieval"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["quiz_id"], "quiz_1234")
        self.assertEqual(data["goal"], "GATE AE")
        self.assertEqual(len(data["questions"]), 5)
        for q in data["questions"]:
            if q["type"] == "short_answer":
                self.assertNotIn("options", q)  # options excluded
            else:
                self.assertIn("options", q)
                self.assertIsInstance(q["options"], list)

    @patch('app.services.question_service.QuestionService.generate_quiz')
    def test_generate_questions_template_success(self, mock_generate_quiz):
        mock_response = GenerateQuestionsResponse(
            quiz_id="quiz_1234",
            goal="GATE AE",
            questions=[{
                "type": "short_answer",
                "question": "Solve 2x² + 5x + 3 = 0 for x.",
                "options": None,
                "answer": "-3/2, -1",
                "difficulty": "beginner",
                "topic": "algebra"
            }, {
                "type": "short_answer",
                "question": "The thrust of a jet engine with mass flow rate 50 kg/s and exhaust velocity 600 m/s is (in kN, to one decimal place):",
                "options": None,
                "answer": "30.0",
                "difficulty": "beginner",
                "topic": "propulsion"
            }]
        )
        mock_generate_quiz.return_value = mock_response
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 2,
                "difficulty": "beginner",
                "mode": "template"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["quiz_id"], "quiz_1234")
        self.assertEqual(data["goal"], "GATE AE")
        self.assertEqual(len(data["questions"]), 2)
        for q in data["questions"]:
            self.assertEqual(q["type"], "short_answer")
            self.assertNotIn("options", q)  # options excluded
            self.assertIn(q["question"], [
                "Solve 2x² + 5x + 3 = 0 for x.",
                "The thrust of a jet engine with mass flow rate 50 kg/s and exhaust velocity 600 m/s is (in kN, to one decimal place):"
            ])

    @patch('app.services.question_service.QuestionService.generate_quiz')
    def test_generate_questions_default_mode(self, mock_generate_quiz):
        mock_response = GenerateQuestionsResponse(
            quiz_id="quiz_1234",
            goal="GATE AE",
            questions=[
                {
                    "type": q.type,
                    "question": q.question,
                    "options": q.options,
                    "answer": q.answer,
                    "difficulty": q.difficulty,
                    "topic": q.topic
                } for q in self.mock_questions[:5]
            ]
        )
        mock_generate_quiz.return_value = mock_response
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
        self.assertEqual(data["quiz_id"], "quiz_1234")
        self.assertEqual(data["goal"], "GATE AE")
        self.assertEqual(len(data["questions"]), 5)
        for q in data["questions"]:
            if q["type"] == "short_answer":
                self.assertNotIn("options", q)  # options excluded
            else:
                self.assertIn("options", q)
                self.assertIsInstance(q["options"], list)

    @patch('app.services.question_service.QuestionService.generate_quiz')
    def test_generate_questions_invalid_difficulty(self, mock_generate_quiz):
        mock_generate_quiz.side_effect = HTTPException(
            status_code=400,
            detail="Difficulty must be one of ['beginner', 'intermediate', 'advanced']"
        )
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 5,
                "difficulty": "invalid",
                "mode": "retrieval"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Difficulty must be one of", response.json()["detail"])

    @patch('app.services.question_service.QuestionService.generate_quiz')
    def test_generate_questions_invalid_goal(self, mock_generate_quiz):
        mock_generate_quiz.side_effect = HTTPException(
            status_code=400,
            detail="Goal must be one of ['GATE AE', 'Amazon SDE', 'CAT', 'MAT']"
        )
        response = self.client.post(
            "/generate",
            json={
                "goal": "Invalid Goal",
                "num_questions": 5,
                "difficulty": "beginner",
                "mode": "retrieval"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Goal must be one of", response.json()["detail"])

    @patch('app.services.question_service.QuestionService.generate_quiz')
    def test_generate_questions_invalid_mode(self, mock_generate_quiz):
        mock_generate_quiz.side_effect = HTTPException(
            status_code=400,
            detail="Mode must be one of ['retrieval', 'template']"
        )
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 5,
                "difficulty": "beginner",
                "mode": "invalid"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Mode must be one of", response.json()["detail"])

    def test_generate_questions_validation_error(self):
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": -1,
                "difficulty": "beginner",
                "mode": "retrieval"
            }
        )
        self.assertEqual(response.status_code, 422)
        self.assertTrue(isinstance(response.json()["detail"], list))

    @patch('app.services.question_service.QuestionService.generate_quiz')
    def test_generate_questions_server_error(self, mock_generate_quiz):
        mock_generate_quiz.side_effect = Exception("Database error")
        response = self.client.post(
            "/generate",
            json={
                "goal": "GATE AE",
                "num_questions": 5,
                "difficulty": "beginner",
                "mode": "retrieval"
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

    @patch('app.services.infra_service.InfraService.health_check')
    def test_health_check_healthy(self, mock_health_check):
        mock_health_check.return_value = HealthCheckResponse(
            status="healthy",
            details={
                "question_bank": "Available (10 questions)",
                "configuration": "Loaded successfully",
                "questions_by_goal": "GATE AE: 10",
                "questions_by_type": "mcq: 10"
            }
        )
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("question_bank", data["details"])
        self.assertIn("configuration", data["details"])
        self.assertEqual(data["details"]["question_bank"], "Available (10 questions)")
        self.assertEqual(data["details"]["configuration"], "Loaded successfully")

    @patch('app.services.infra_service.InfraService.health_check')
    def test_health_check_unhealthy(self, mock_health_check):
        mock_health_check.return_value = HealthCheckResponse(
            status="unhealthy",
            details={
                "question_bank": "Not available: Error loading questions",
                "configuration": "Missing keys: supported_difficulties, supported_types",
                "questions_by_goal": "Not available",
                "questions_by_type": "Not available"
            }
        )
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertIn("question_bank", data["details"])
        self.assertIn("configuration", data["details"])
        self.assertIn("Not available", data["details"]["question_bank"])
        self.assertIn("Missing keys", data["details"]["configuration"])

if __name__ == '__main__':
    result = unittest.main(verbosity=2, exit=False)
    if result.wasSuccessful():
        print("Success: All tests passed!")
    else:
        print("Failure: Some tests did not pass.")