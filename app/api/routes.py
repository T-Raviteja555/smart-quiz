from fastapi import APIRouter, Depends
from app.api.models import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    HealthCheckResponse,
    ConfigResponse,
    LocalMetricsResponse,
    PerformanceMetricsResponse,
    GoalRequest,
    GoalResponse
)
from app.services.question_service import QuestionService
from app.services.infra_service import InfraService
from typing import List

router = APIRouter()

def get_question_service():
    return QuestionService()

def get_infra_service():
    return InfraService()

@router.get(
    "/questions",
    response_model=GenerateQuestionsResponse,
    tags=["questions"],
    summary="Retrieve all questions",
    description="Returns a list of all available questions in dataset."
)
async def get_questions(service: QuestionService = Depends(get_question_service)):
    return service.get_all_questions()

@router.post(
    "/generate",
    response_model=GenerateQuestionsResponse,
    tags=["generate"],
    responses={
        200: {"description": "Successful response with generated questions", "model": GenerateQuestionsResponse},
        400: {"description": "Invalid input parameters"},
        422: {"description": "Validation error for request payload"},
        500: {"description": "Internal server error"}
    },
    summary="Generate questions for a quiz",
    description=(
        "Generates a specified number of questions based on goal, difficulty, and mode.\n\n"
        "### Parameters\n"
        "- **goal**: A supported goal (e.g., 'GATE AE', managed via POST /goals)\n"
        "- **difficulty**: Supported values: `beginner`, `intermediate`, `advanced`\n"
        "- **num_questions**: Integer between 1 and 10\n"
        "- **mode**: Optional generation mode: `retrieval` (TF-IDF) or `template` (formula-driven). Defaults to config.generator_mode.\n\n"
        "### Error Handling\n"
        "- Returns standardized JSON errors (`{\"detail\": \"Error message\"}` or `{\"detail\": [\"Error messages\"]}`) for invalid inputs or server errors.\n"
        "- Common status codes: `400` (invalid input), `422` (validation error), `500` (server error).\n"
    )
)
async def generate_questions_post(
    request: GenerateQuestionsRequest,
    service: QuestionService = Depends(get_question_service)
):
    return service.generate_quiz(
        request.goal,
        request.difficulty,
        request.num_questions,
        request.mode
    )

@router.post(
    "/goals",
    response_model=GoalResponse,
    tags=["goals"],
    responses={
        200: {"description": "Goal added, questions appended, or goal removed successfully", "model": GoalResponse},
        400: {"description": "Invalid goal, action, questions, or insufficient questions"},
        401: {"description": "Invalid API token"},
        422: {"description": "Validation error for request payload"},
        500: {"description": "Internal server error"}
    },
    summary="Add or remove a supported goal",
    description=(
        "Adds a new goal to or removes an existing goal from the supported goals list, or appends questions to an existing goal, updating config.json and schema.json as needed.\n\n"
        "### Parameters\n"
        "- **goal**: The goal to add or remove (e.g., 'GATE AE')\n"
        "- **action**: Action to perform: `add` or `remove`\n"
        "- **api_token**: API token for authentication\n"
        "- **questions**: Optional list of questions to add for the goal (requires at least 10 questions total for new goals)\n\n"
        "### Notes\n"
        "- Adding a new goal requires it to exist in the question bank or be provided, with at least 10 questions total.\n"
        "- If the goal already exists, provided questions are appended to the question bank.\n"
        "- Removing a goal fails if it has associated questions in the question bank.\n"
        "- Updates are atomic using file locking.\n"
        "- Requires a valid API token stored in api_tokens.json.\n"
    )
)
async def manage_goals(
    request: GoalRequest,
    service: QuestionService = Depends(get_question_service)
):
    if request.action == "add":
        return service.add_goal(request.goal, request.questions, request.api_token)
    elif request.action == "remove":
        return service.remove_goal(request.goal, request.api_token)

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["health"],
    responses={
        200: {"description": "Service is healthy", "model": HealthCheckResponse},
        503: {"description": "Service is unhealthy", "model": HealthCheckResponse},
        500: {"description": "Internal server error"}
    },
    summary="Check API health",
    description=(
        "Checks the health of the API by verifying critical dependencies.\n\n"
        "### Response\n"
        "- **status**: `healthy` if all dependencies are operational, `unhealthy` otherwise.\n"
        "- **details**: Information about checked dependencies (e.g., question bank, configuration) and question counts by goal and type.\n"
    )
)
async def health_check(service: InfraService = Depends(get_infra_service)):
    return service.health_check()

@router.get(
    "/config",
    response_model=ConfigResponse,
    tags=["config"],
    responses={
        200: {"description": "Configuration details retrieved successfully", "model": ConfigResponse},
        500: {"description": "Internal server error"}
    },
    summary="Retrieve configuration details",
    description=(
        "Returns the generator mode, version, supported goals, and question types from the configuration.\n\n"
        "### Response\n"
        "- **generator_mode**: The mode of the question generator (e.g., 'retrieval').\n"
        "- **version**: The API version from the configuration (e.g., '1.0.0').\n"
        "- **goal**: List of supported goals, managed via POST /goals.\n"
        "- **type**: Supported question types.\n"
    )
)
async def get_config(service: QuestionService = Depends(get_question_service)):
    return service.get_config()

@router.get(
    "/local-metrics",
    response_model=LocalMetricsResponse,
    tags=["monitoring"],
    summary="Local metrics",
    description="Exposes locally collected metrics including request counts, average latencies, and error counts."
)
async def local_metrics(service: InfraService = Depends(get_infra_service)):
    return service.get_local_metrics()

@router.get(
    "/performance-metrics",
    response_model=List[PerformanceMetricsResponse],
    tags=["monitoring"],
    summary="Performance metrics",
    description="Exposes aggregated performance metrics including throughput, latency statistics, and error rates."
)
async def performance_metrics(service: InfraService = Depends(get_infra_service)):
    return service.get_performance_metrics()