import unittest
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient
from app.main import app
from app.questions import QuizQuestion
from app.api.models import GoalResponse
import json

class TestGoalsEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_questions = [
            QuizQuestion(
                type="mcq",
                question=f"Question {i}",
                options=["A", "B", "C", "D"],
                answer="A",
                difficulty="beginner",
                topic="algorithms",
                goal="New Goal"
            ) for i in range(15)  # 15 questions for New Goal
        ] + [
            QuizQuestion(
                type="short_answer",
                question=f"Short answer {i}",
                options=None,
                answer="Answer",
                difficulty="beginner",
                topic="propulsion",
                goal="GATE"
            ) for i in range(5)
        ]
        self.sample_questions = [
            QuizQuestion(
                type="mcq",
                question="(Logical Reasoning) In a group of 5 people, if A is friends with B and C, and B is not friends with D, who can be friends with E?",
                options=["A only", "B and C", "D only", "Anyone"],
                answer="Anyone",
                difficulty="intermediate",
                topic="Data Interpretation and Logical Reasoning - Logical Reasoning",
                goal="New Goal"
            ),
            QuizQuestion(
                type="short_answer",
                question="Let f(x, y) = x^3 + y^3 - 3xy. The total number of critical points of the function is",
                options=None,
                answer="2",
                difficulty="intermediate",
                topic="Mathematics",
                goal="New Goal"
            )
        ]
        self.api_token = "secure-token-123"

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    @patch('app.questions.count_questions_for_goal')
    @patch('app.questions.append_questions_to_bank')
    def test_add_goal_with_questions_success(self, mock_append, mock_count, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE", "New Goal"}
        mock_count.return_value = 8  # 8 existing + 2 provided = 10
        mock_config_data = {
            "supported_goals": ["GATE", "Amazon SDE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "inputRequest": {"properties": {"goal": {"enum": ["GATE", "Amazon SDE"]}}},
                "outputResponse": {"properties": {"goal": {"enum": ["GATE", "Amazon SDE"]}}}
            }
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open().return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            with patch('app.services.question_service.Path.open', mock_open()) as mock_schema_file:
                mock_schema_file.side_effect = [
                    mock_open(read_data=json.dumps(mock_schema_data)).return_value,
                    mock_open().return_value
                ]
                response = self.client.post(
                    "/goals",
                    json={
                        "goal": "New Goal",
                        "action": "add",
                        "api_token": self.api_token,
                        "questions": [q.dict() for q in self.sample_questions]
                    }
                )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Goal 'New Goal' added successfully with 10 questions")
        self.assertEqual(data["supported_goals"], ["GATE", "Amazon SDE", "New Goal"])
        mock_append.assert_called_once()

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    @patch('app.questions.count_questions_for_goal')
    @patch('app.questions.append_questions_to_bank')
    def test_add_questions_to_existing_goal(self, mock_append, mock_count, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE", "New Goal"}
        mock_count.return_value = 15
        mock_config_data = {
            "supported_goals": ["GATE", "New Goal"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "New Goal",
                    "action": "add",
                    "api_token": self.api_token,
                    "questions": [q.dict() for q in self.sample_questions]
                }
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Appended 2 questions to existing goal 'New Goal'")
        self.assertEqual(data["supported_goals"], ["GATE", "New Goal"])
        mock_append.assert_called_once()

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    @patch('app.questions.count_questions_for_goal')
    def test_add_goal_without_questions_success(self, mock_count, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE", "New Goal"}
        mock_count.return_value = 15  # ≥10 existing questions
        mock_config_data = {
            "supported_goals": ["GATE", "Amazon SDE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "inputRequest": {"properties": {"goal": {"enum": ["GATE", "Amazon SDE"]}}},
                "outputResponse": {"properties": {"goal": {"enum": ["GATE", "Amazon SDE"]}}}
            }
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open().return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            with patch('app.services.question_service.Path.open', mock_open()) as mock_schema_file:
                mock_schema_file.side_effect = [
                    mock_open(read_data=json.dumps(mock_schema_data)).return_value,
                    mock_open().return_value
                ]
                response = self.client.post(
                    "/goals",
                    json={
                        "goal": "New Goal",
                        "action": "add",
                        "api_token": self.api_token
                    }
                )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Goal 'New Goal' added successfully with 15 questions")
        self.assertEqual(data["supported_goals"], ["GATE", "Amazon SDE", "New Goal"])

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    @patch('app.questions.count_questions_for_goal')
    def test_add_goal_invalid_token(self, mock_count, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE", "New Goal"}
        mock_count.return_value = 15
        mock_config_data = {
            "supported_goals": ["GATE", "Amazon SDE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "New Goal",
                    "action": "add",
                    "api_token": "invalid-token"
                }
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid API token")

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    @patch('app.questions.count_questions_for_goal')
    def test_add_goal_insufficient_questions(self, mock_count, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE", "New Goal"}
        mock_count.return_value = 5  # <10 questions
        mock_config_data = {
            "supported_goals": ["GATE", "Amazon SDE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "New Goal",
                    "action": "add",
                    "api_token": self.api_token,
                    "questions": [self.sample_questions[0].dict()]  # Only 1 question
                }
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Goal 'New Goal' has 6 questions (existing: 5, provided: 1); minimum 10 required", response.json()["detail"])

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    def test_add_goal_not_in_bank(self, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE"}
        mock_config_data = {
            "supported_goals": ["GATE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "Invalid Goal",
                    "action": "add",
                    "api_token": self.api_token
                }
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Goal 'Invalid Goal' not found in question bank and no questions provided", response.json()["detail"])

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    def test_add_goal_invalid_question(self, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE", "New Goal"}
        mock_config_data = {
            "supported_goals": ["GATE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        invalid_question = self.sample_questions[0].dict()
        invalid_question['options'] = ["A", "B"]  # Invalid: MCQ needs 4 options
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "New Goal",
                    "action": "add",
                    "api_token": self.api_token,
                    "questions": [invalid_question]
                }
            )
        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to add goal: mcq questions must have exactly 4 options", response.json()["detail"])

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    def test_remove_goal_success(self, mock_goals, mock_load_questions):
        mock_load_questions.return_value = []  # No questions with CAT
        mock_goals.return_value = set()
        mock_config_data = {
            "supported_goals": ["GATE", "CAT"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "inputRequest": {"properties": {"goal": {"enum": ["GATE", "CAT"]}}},
                "outputResponse": {"properties": {"goal": {"enum": ["GATE", "CAT"]}}}
            }
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open().return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            with patch('app.services.question_service.Path.open', mock_open()) as mock_schema_file:
                mock_schema_file.side_effect = [
                    mock_open(read_data=json.dumps(mock_schema_data)).return_value,
                    mock_open().return_value
                ]
                response = self.client.post(
                    "/goals",
                    json={
                        "goal": "CAT",
                        "action": "remove",
                        "api_token": self.api_token
                    }
                )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Goal 'CAT' removed successfully")
        self.assertEqual(data["supported_goals"], ["GATE"])

    @patch('app.questions.load_questions')
    def test_remove_goal_invalid_token(self, mock_load_questions):
        mock_load_questions.return_value = []
        mock_config_data = {
            "supported_goals": ["GATE", "CAT"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "CAT",
                    "action": "remove",
                    "api_token": "invalid-token"
                }
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid API token")

    @patch('app.questions.load_questions')
    def test_remove_goal_not_exists(self, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_config_data = {
            "supported_goals": ["GATE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "Invalid Goal",
                    "action": "remove",
                    "api_token": self.api_token
                }
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Goal 'Invalid Goal' not in supported goals", response.json()["detail"])

    @patch('app.questions.load_questions')
    @patch('app.questions.get_goals_in_question_bank')
    def test_remove_goal_in_bank(self, mock_goals, mock_load_questions):
        mock_load_questions.return_value = self.mock_questions
        mock_goals.return_value = {"GATE", "New Goal"}
        mock_config_data = {
            "supported_goals": ["GATE"],
            "supported_difficulties": ["beginner", "intermediate", "advanced"],
            "supported_types": ["mcq", "short_answer"],
            "supported_generator_modes": ["retrieval", "template"],
            "generator_mode": "retrieval"
        }
        mock_token_data = {"api_token": self.api_token}
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(mock_config_data)).return_value,
                mock_open(read_data=json.dumps(mock_token_data)).return_value
            ]
            response = self.client.post(
                "/goals",
                json={
                    "goal": "GATE",
                    "action": "remove",
                    "api_token": self.api_token
                }
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot remove goal 'GATE' as it is still present in question bank", response.json()["detail"])

if __name__ == '__main__':
    unittest.main(verbosity=2)