from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from typing_extensions import Literal
from app.utils.config_loader import CONFIG
from app.questions import QuizQuestion

class GoalRequest(BaseModel):
    goal: str = Field(..., description="Goal to add or remove (e.g., 'GATE')", example="GATE", min_length=1)
    action: str = Field(..., description="Action to perform", example="add", enum=["add", "remove"])
    api_token: str = Field(..., description="API token for authentication", example="secure-token-123", min_length=1)
    questions: Optional[List[QuizQuestion]] = Field(
        None,
        description="Optional list of questions to add for the goal (requires at least 10 questions total)",
        example=[
            {
                "goal": "GATE",
                "type": "mcq",
                "question": "Consider a thin flat plate at 2° angle of attack in a hypersonic flow at Mach 10. Assume that the pressure coefficient on the lower surface of the plate is given by the Newtonian theory, C_p = 2 sin^2 α, where α is the angle that the local surface makes with the free stream flow direction. Assume that the pressure coefficient on the upper surface is zero. The lift coefficient of the flat plate is",
                "options": [
                    "A. 0.024",
                    "B. 0.048",
                    "C. 0.072",
                    "D. 0.096"
                ],
                "answer": "A. 0.024",
                "difficulty": "advanced",
                "topic": "Aerodynamics"
            },
            {
                "goal": "GATE",
                "type": "short_answer",
                "question": "Let f(x, y) = x^3 + y^3 - 3xy. The total number of critical points of the function is",
                "answer": "2",
                "options": [],
                "difficulty": "intermediate",
                "topic": "Mathematics"
            }
        ]
    )

class GenerateQuestionsRequest(BaseModel):
    goal: str = Field(
        ..., 
        description="Goal of the questions (e.g., 'GATE', 'Amazon SDE')", 
        example="GATE", 
        min_length=1
    )
    num_questions: int = Field(..., ge=1, le=10, description="Number of questions to generate", example=5)
    difficulty: str = Field(..., description="Difficulty level (e.g., 'beginner', 'intermediate', 'advanced')", example="beginner", enum=["beginner", "intermediate", "advanced"])
    mode: Optional[str] = Field(None, description="Generation mode (e.g., 'retrieval', 'template'). Defaults to config.generator_mode.", example="retrieval", enum=["retrieval", "template"])

class QuestionResponseBase(BaseModel):
    type: str
    question: str
    answer: str
    difficulty: str
    topic: str

class McqQuestionResponse(QuestionResponseBase):
    type: Literal["mcq"]
    options: List[str] = Field(..., min_items=4, max_items=4)

class ShortAnswerQuestionResponse(QuestionResponseBase):
    type: Literal["short_answer"]

QuestionResponse = Union[McqQuestionResponse, ShortAnswerQuestionResponse]

class GenerateQuestionsResponse(BaseModel):
    quiz_id: str = Field(..., description="Unique identifier for the quiz", example="quiz_1234")
    goal: str = Field(..., description="Goal of the quiz", example="GATE")
    questions: List[QuestionResponse] = Field(..., description="List of generated questions")

class GoalResponse(BaseModel): 
    message: str = Field(..., description="Result of the goal action", example="Goal 'GATE' added successfully")
    supported_goals: List[str] = Field(..., description="Updated list of supported goals", example=["GATE", "Amazon SDE"])

class HealthCheckResponse(BaseModel):
    status: str
    details: Optional[Dict[str, str]] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "details": {
                    "question_bank": "Available (10 questions)",
                    "configuration": "Loaded successfully",
                    "questions_by_goal": "GATE: 5, Amazon SDE: 5",
                    "questions_by_type": "MCQ: 8, Coding: 2"
                }
            }
        }

class ConfigResponse(BaseModel):
    generator_mode: str = Field(..., description="Mode of the question generator", example="retrieval")
    version: str = Field(..., description="API version from configuration", example="1.0.0")
    goal: List[str] = Field(..., description="Supported goals (managed via POST /goals)", example=["GATE", "Amazon SDE"])
    type: List[str] = Field(..., description="Type of the questions", example=["mcq", "short_answer"])

class LocalMetricsResponse(BaseModel):
    request_count: Dict[str, int]
    average_latency: Dict[str, float]
    error_count: Dict[str, int]

class PerformanceMetricsResponse(BaseModel):
    timestamp: str
    request_count: int
    throughput: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p95_latency: float
    error_rate: float
    