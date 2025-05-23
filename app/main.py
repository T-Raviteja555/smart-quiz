import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import structlog
import logging
from typing import List, Dict, Optional
from app.questions import load_questions, generate_questions, QuizQuestion
from app.utils.config_loader import CONFIG
from app.utils.exceptions import ErrorResponse, exception_handlers
import random

# Configure structlog for JSON logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard logging
logging_config = CONFIG.get('logging', {})
log_level = getattr(logging, logging_config.get('level', 'INFO').upper(), logging.INFO)
logging.basicConfig(level=log_level, handlers=[logging.StreamHandler()])
logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Questions API",
    description="API for retrieving GATE AE and Amazon SDE questions",
    version="1.0.0"
)

# Register global exception handlers
for exc_type, handler in exception_handlers.items():
    app.add_exception_handler(exc_type, handler)

# Pydantic models
class GenerateQuestionsRequest(BaseModel):
    goal: str = Field(..., description="Goal of the questions (e.g., 'GATE AE', 'Amazon SDE')", example="GATE AE", enum=["GATE AE", "Amazon SDE"])
    num_questions: int = Field(..., ge=1, le=10, description="Number of questions to generate", example=5)
    difficulty: str = Field(..., description="Difficulty level (e.g., 'beginner', 'intermediate', 'advanced')", example="beginner", enum=["beginner", "intermediate", "advanced"])

class QuestionResponse(BaseModel):
    type: str
    question: str
    options: List[str]
    answer: str
    difficulty: str
    topic: str

class GenerateQuestionsResponse(BaseModel):
    quiz_id: str = Field(..., description="Unique identifier for the quiz", example="quiz_1234")
    goal: str = Field(..., description="Goal of the quiz", example="GATE AE")
    questions: List[QuestionResponse] = Field(..., description="List of generated questions")

class HealthCheckResponse(BaseModel):
    status: str
    details: Optional[Dict[str, str]] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "details": {
                    "question_bank": "Available (10 questions)",
                    "configuration": "Loaded successfully"
                }
            }
        }

# Load questions at startup (cached by questions.py)
questions_cache = load_questions()

def display_questions(questions: List[QuizQuestion]):
    for q in questions:
        logger.info(f"Answer: {q.answer}")

# Endpoints
@app.get(
    "/questions",
    response_model=GenerateQuestionsResponse,
    tags=["questions"],
    summary="Retrieve all questions",
    description="Returns a list of all available questions in dataset."
)
async def get_questions():
    questions = load_questions()
    quiz_id = f"quiz_{random.randint(1000, 9999)}"
    # Convert to response model without goal in questions
    response_questions = [
        QuestionResponse(
            type=q.type,
            question=q.question,
            options=q.options,
            answer=q.answer,
            difficulty=q.difficulty,
            topic=q.topic
        ) for q in questions
    ]
    return GenerateQuestionsResponse(
        quiz_id=quiz_id,
        goal=questions[0].goal if questions else "GATE AE",
        questions=response_questions
    )

@app.post(
    "/generate",
    response_model=GenerateQuestionsResponse,
    tags=["generate"],
    responses={
        200: {"description": "Successful response with generated questions", "model": GenerateQuestionsResponse},
        400: {"description": "Invalid input parameters", "model": ErrorResponse},
        422: {"description": "Validation error for request payload", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Generate questions for a quiz",
    description=(
        "Generates a specified number of questions based on goal and difficulty.\n\n"
        "### Parameters\n"
        "- **goal**: Supported values: `GATE AE`, `Amazon SDE`\n"
        "- **difficulty**: Supported values: `beginner`, `intermediate`, `advanced`\n"
        "- **num_questions**: Integer between 1 and 10\n\n"
        "### Error Handling\n"
        "- Returns standardized JSON errors (`{\"detail\": \"Error message\"}` or `{\"detail\": [\"Error messages\"]}`) for invalid inputs or server errors.\n"
        "- Common status codes: `400` (invalid input), `422` (validation error), `500` (server error).\n"
    )
)
async def generate_questions_post(request: GenerateQuestionsRequest):
    try:
        supported_goals = ["GATE AE", "Amazon SDE"]
        if request.goal not in supported_goals:
            raise HTTPException(status_code=400, detail=f"Goal must be one of {supported_goals}")
        if request.difficulty not in CONFIG['supported_difficulties']:
            raise HTTPException(status_code=400, detail=f"Difficulty must be one of {CONFIG['supported_difficulties']}")
        if not questions_cache:
            raise HTTPException(status_code=500, detail="Question bank not available")
        questions = generate_questions(request.goal, request.difficulty, request.num_questions)
        # Convert to response model without goal in questions
        response_questions = [
            QuestionResponse(
                type=q.type,
                question=q.question,
                options=q.options,
                answer=q.answer,
                difficulty=q.difficulty,
                topic=q.topic
            ) for q in questions
        ]
        return GenerateQuestionsResponse(
            quiz_id=f"quiz_{random.randint(1000, 9999)}",
            goal=request.goal,
            questions=response_questions
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["health"],
    responses={
        200: {"description": "Service is healthy", "model": HealthCheckResponse},
        503: {"description": "Service is unhealthy", "model": HealthCheckResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Check API health",
    description=(
        "Checks the health of the API by verifying critical dependencies.\n\n"
        "### Response\n"
        "- **status**: `healthy` if all dependencies are operational, `unhealthy` otherwise.\n"
        "- **details**: Information about checked dependencies (e.g., question bank, configuration).\n"
    )
)
async def health_check():
    details = {}
    is_healthy = True

    # Check question bank
    try:
        question_count = len(questions_cache)
        details["question_bank"] = f"Available ({question_count} questions)"
    except Exception as e:
        details["question_bank"] = f"Not available: {str(e)}"
        is_healthy = False

    # Check configuration
    required_keys = ["supported_difficulties", "supported_types"]
    missing_keys = [key for key in required_keys if key not in CONFIG]
    if missing_keys:
        details["configuration"] = f"Missing keys: {', '.join(missing_keys)}"
        is_healthy = False
    else:
        details["configuration"] = "Loaded successfully"

    status = "healthy" if is_healthy else "unhealthy"
    logger.info(
        "Health check",
        status=status,
        details=details
    )

    return HealthCheckResponse(
        status=status,
        details=details
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)