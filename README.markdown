Smart Quiz Generator Microservice

The Smart Quiz Generator Microservice is a production-ready, FastAPI-based REST API designed to generate and manage quiz questions for educational and professional goals, such as GATE, Amazon Software Development Engineer (Amazon SDE), and Common Admission Test (CAT). It supports multiple-choice (MCQ) and short-answer questions across beginner, intermediate, and advanced difficulty levels. Managed via a curated configuration in config.json, the API provides endpoints for retrieving questions, generating customized quizzes, managing supported goals with authentication, monitoring system health with visualizations, and analyzing performance metrics. The system emphasizes modularity, scalability, and maintainability, deployed as a Docker container for plug-and-play operation.

Project Structure

The codebase is organized for separation of concerns and ease of maintenance:

project_root/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # API endpoint definitions
│   │   ├── middleware.py          # Middleware and lifespan handlers
│   │   ├── models.py             # Pydantic models for requests/responses
│   ├── services/
│   │   ├── __init__.py
│   │   ├── question_service.py    # Business logic for question operations
│   │   ├── infra_service.py       # Infrastructure logic (health, metrics)
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── base.py               # Base generator interface
│   │   ├── tfidfRetrieval/
│   │   │   ├── __init__.py
│   │   │   ├── tfidfGenerator.py  # TF-IDF retrieval logic
│   │   ├── templateRetrieval/
│   │   │   ├── __init__.py
│   │   │   ├── templateGenerator.py  # Template-driven question generator
│   │   │   ├── questionTemplates.py  # Question template definitions
│   ├── utils/
│   │   ├── config_loader.py      # Configuration loading and logging setup
│   │   ├── exceptions.py         # Custom exception handlers
│   ├── templates/
│   │   ├── health_visualization.html  # Chart.js dashboard for health endpoint
│   ├── __init__.py
│   ├── questions.py              # Question loading and validation logic
│   ├── main.py                   # FastAPI app initialization and server
├── config.json                   # Configuration file
├── schema.json                   # JSON Schema for goal validation
├── api_tokens.json               # API token for authentication
├── data/
│   ├── consolidated_questions_updated.json  # Question bank (672 questions)
├── tests/
│   ├── test_goals.py             # Tests for POST /goals endpoint
├── logs/
│   ├── app.log                   # Application logs
│   ├── metrics.log               # Metrics logs
│   ├── performance.log           # Performance logs
├── Dockerfile                    # Docker build instructions
├── docker-compose.yaml           # Docker Compose configuration
├── performance_metrics.json      # Performance metrics for health dashboard
├── README.md                     # Project documentation

Features and Highlights

The microservice offers a robust set of features, designed for reliability, scalability, and developer-friendliness:

Flexible Question Management





Retrieve Questions: GET /questions fetches all questions from the question bank (672 questions: GATE: 219, Amazon SDE: 195, CAT: 213), supporting MCQ and short-answer formats.



Generate Quizzes: POST /generate creates tailored quizzes based on goal, difficulty, and number of questions (1–10).



Question Validation: Uses Pydantic models (models.py) and custom validation (questions.py) to ensure data integrity (e.g., 4 options for MCQs, null options for short answers).

Goal Management





Manage Goals: POST /goals adds/removes goals in config.json, updating schema.json with valid goals.



Authentication: Requires API token from api_tokens.json for secure operations.



Data Integrity: Ensures new goals have ≥10 questions; prevents removal of goals with associated questions; uses filelock for thread-safe file updates.

Dynamic Question Generation





Retrieval Mode: TF-IDF (tfidfGenerator.py) ranks questions from the question bank based on goal relevance, optimized with TTLCache.



Template Mode: Generates dynamic questions (templateGenerator.py, questionTemplates.py) using Jinja2 templates and SymPy for mathematical/logical accuracy (e.g., quadratic equations, aerodynamics, algorithms).



Configurable Modes: Toggle between retrieval and template modes via config.json or POST /generate parameter.



Supported Goals: GATE (e.g., aerodynamics), Amazon SDE (e.g., data structures), CAT (e.g., quantitative aptitude).

Production-Ready Infrastructure





Health Monitoring: GET /health reports dependency status and question counts; ?visualize=true displays a Chart.js dashboard for question distribution and performance metrics.



Performance Metrics: GET /local-metrics and GET /performance-metrics provide real-time and aggregated insights (latency, throughput, error rate), stored in metrics.json and performance_metrics.json.



Structured Logging: Uses structlog for JSON logs (app.log, metrics.log, performance.log) with daily rotation and 7-day retention.



Thread-Safe Operations: filelock ensures atomic updates to JSON files in concurrent environments.



Dockerized Deployment: Dockerfile and docker-compose.yaml enable scalable, plug-and-play deployment.

Optimized Response Structure





Pydantic inheritance model (QuestionResponseBase, McqQuestionResponse, ShortAnswerQuestionResponse) ensures clean, type-safe responses, excluding options for short-answer questions.



Extensible design for adding new question types (e.g., coding questions).

Developer-Friendly





Interactive API documentation via Swagger UI (/docs) and ReDoc (/redoc).



Comprehensive error handling with standardized JSON responses (exceptions.py).



Modular architecture with dependency injection for maintainability.

High-Level Design (HLD)

The microservice follows a layered architecture:





Client Layer: External clients interact via HTTP requests (e.g., POST /generate, POST /goals).



API Layer: FastAPI handles routing, validation, and serialization (routes.py, models.py).



Service Layer: Encapsulates business logic (question_service.py, infra_service.py).



Generator Layer: Abstracts question generation (tfidfGenerator.py, templateGenerator.py).



Data Layer: File-based storage (config.json, schema.json, consolidated_questions_updated.json).



Cache Layer: TTLCache optimizes question loading (questions.py).



Logging/Monitoring: Structured logs (structlog) and metrics (metrics.json, performance_metrics.json).

Data Flow Example (POST /goals):





Client sends POST /goals with goal, action, api_token, and optional questions.



FastAPI validates the request using GoalRequest model.



QuestionService validates api_token, checks question count (≥10 for new goals), appends questions to consolidated_questions_updated.json, updates config.json/schema.json, and clears question_cache.



Response (GoalResponse) is returned with updated supported_goals.

Low-Level Design (LLD) for POST /goals





Endpoint: POST /goals



Request Model (GoalRequest in models.py):

class GoalRequest(BaseModel):
    goal: str  # e.g., "New Goal"
    action: str  # "add" or "remove"
    api_token: str  # e.g., "secure-token-123"
    questions: Optional[List[QuizQuestion]]  # Optional questions



Response Model (GoalResponse):

class GoalResponse(BaseModel):
    message: str  # e.g., "Goal added successfully"
    supported_goals: List[str]  # e.g., ["GATE", "Amazon SDE"]



Components:





Router (routes.py): Validates request, routes to QuestionService.



QuestionService (question_service.py):





Validates api_token against api_tokens.json.



For add: Validates questions, checks count (≥10), appends to question bank, updates config.json/schema.json.



For remove: Ensures no questions exist, updates config.json/schema.json.



Questions Module (questions.py): Validates questions, manages question bank with filelock.



Cache: TTLCache for question loading, cleared after updates.



Error Handling:





401: Invalid api_token.



400: Invalid goal, insufficient questions, or mismatched question goal.



500: File I/O or validation errors.

Installation

Prerequisites





Python 3.10+ (for local development)



pip (Python package manager)



Docker and Docker Compose (for containerized deployment)



Git (optional, for cloning)



Internet access (for Chart.js CDN in health dashboard)

Steps





Clone the Repository (if using Git):

git clone <repository-url>
cd <repository-directory>



Set Up Configuration Files:





Ensure config.json, schema.json, api_tokens.json, and performance_metrics.json are in the project root.



Place consolidated_questions_updated.json in data/ with 672 questions.



Restrict permissions for api_tokens.json:

chmod 600 api_tokens.json



Local Development (Optional):





Create a virtual environment:

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate



Install dependencies:

pip install -r requirements.txt



Run the application:

python app/main.py



Access at http://127.0.0.1:8000.



Dockerized Deployment:





Build and run:

docker-compose up -d --build



Stop:

docker-compose down



Access at http://127.0.0.1:8000.



Access API Documentation:





Swagger UI: http://127.0.0.1:8000/docs



ReDoc: http://127.0.0.1:8000/redoc

Configuration

config.json

{
    "DATA_DIR": "/data",
    "DATASET": "consolidated_questions_updated.json",
    "CACHE_MAXSIZE": 100,
    "CACHE_TTL": 3600,
    "MAX_WORKERS": 4,
    "max_questions": 10,
    "default_num_questions": 5,
    "supported_goals": ["GATE", "Amazon SDE", "CAT"],
    "supported_difficulties": ["beginner", "intermediate", "advanced"],
    "supported_types": ["mcq", "short_answer"],
    "supported_generator_modes": ["retrieval", "template"],
    "generator_mode": "retrieval",
    "version": "1.0.0",
    "logging": {
        "level": "INFO",
        "logpath": "logs/app.log",
        "metrics_logpath": "logs/metrics.log",
        "performance_logpath": "logs/performance.log",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "rotating_file_handler": {
            "when": "midnight",
            "interval": 1,
            "backupCount": 7
        }
    },
    "monitoring": {
        "metrics_enabled": true,
        "metrics_file": "metrics.json",
        "performance_metrics_file": "performance_metrics.json",
        "performance_aggregation_interval": 60
    }
}

schema.json (Excerpt)

{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "inputRequest": {
            "properties": {
                "goal": {
                    "type": "string",
                    "enum": ["GATE", "Amazon SDE", "CAT"],
                    "description": "Target exam or role for the quiz."
                },
                "num_questions": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced"]
                },
                "mode": {
                    "type": ["string", "null"],
                    "enum": ["retrieval", "template", null]
                }
            },
            "required": ["goal", "num_questions", "difficulty"]
        }
    }
}

api_tokens.json

{
    "api_token": "secure-token-123"
}

performance_metrics.json (Sample)

[
    {
        "timestamp": "2025-06-23T12:00:00",
        "request_count": 100,
        "throughput": 10.0,
        "avg_latency": 0.1,
        "min_latency": 0.05,
        "max_latency": 0.2,
        "p95_latency": 0.15,
        "error_rate": 0.01
    }
]

Configuration Notes





DATA_DIR: Set to /data, matching the Docker volume mount (E:/smart-quiz/data on host).



supported_goals: Managed via POST /goals, dynamically updates schema.json.



Logging: Configures daily rotation with 7-day retention.



Monitoring: Metrics stored in metrics.json and performance_metrics.json; performance_aggregation_interval controls aggregation frequency.



Chart.js: Health dashboard requires internet access for CDN (https://cdn.jsdelivr.net/npm/chart.js).

Usage

Endpoints





GET /questions: Retrieves all 672 questions from the question bank.



POST /generate: Generates a quiz based on goal, difficulty, num_questions, and mode.



POST /goals: Adds/removes goals or appends questions, requires api_token.



GET /health: Reports API health; ?visualize=true displays a Chart.js dashboard.



GET /config: Returns configuration details (goals, mode, version).



GET /local-metrics: Provides real-time request metrics.



GET /performance-metrics: Returns aggregated performance metrics.

Example: Add New Goal (POST /goals)

Add a new goal with 2 questions (assuming 8 existing questions for New Goal):

curl -X POST "http://127.0.0.1:8000/goals" \
-H "Content-Type: application/json" \
-d '{
    "goal": "New Goal",
    "action": "add",
    "api_token": "secure-token-123",
    "questions": [
        {
            "goal": "New Goal",
            "type": "mcq",
            "question": "In a group of 5, if A is friends with B and C, who can be friends with E?",
            "options": ["A only", "B and C", "D only", "Anyone"],
            "answer": "Anyone",
            "difficulty": "intermediate",
            "topic": "Logical Reasoning"
        },
        {
            "goal": "New Goal",
            "type": "short_answer",
            "question": "Number of critical points of f(x, y) = x^3 + y^3 - 3xy?",
            "options": null,
            "answer": "2",
            "difficulty": "intermediate",
            "topic": "Mathematics"
        }
    ]
}'

Response:

{
    "message": "Goal 'New Goal' added successfully with 10 questions",
    "supported_goals": ["GATE", "Amazon SDE", "CAT", "New Goal"]
}

Example: Generate Quiz (POST /generate, Template Mode)

curl -X POST "http://127.0.0.1:8000/generate" \
-H "Content-Type: application/json" \
-d '{"goal": "GATE", "difficulty": "beginner", "num_questions": 2, "mode": "template"}'

Response:

{
    "quiz_id": "quiz_1234",
    "goal": "GATE",
    "questions": [
        {
            "type": "short_answer",
            "question": "Solve 2x² + 5x + 3 = 0 (round to 2 decimals).",
            "answer": "-1.50, -1.00",
            "difficulty": "beginner",
            "topic": "algebra"
        },
        {
            "type": "short_answer",
            "question": "Thrust of a jet engine (50 kg/s, 600 m/s) in kN?",
            "answer": "30.00",
            "difficulty": "beginner",
            "topic": "propulsion"
        }
    ]
}

Example: Health Dashboard (GET /health?visualize=true)

curl http://127.0.0.1:8000/health?visualize=true

Or open in a browser: http://127.0.0.1:8000/health?visualize=true

Response: HTML page with Chart.js visualizations:





Bar chart: Question counts by goal (GATE: 219, Amazon SDE: 195, CAT: 213).



Bar charts: MCQ/short-answer counts per goal.



Line chart: Performance metrics (request count, throughput, latency, error rate).

Sequence Diagram (POST /goals)

sequenceDiagram
    actor Client
    participant Router as FastAPI Router
    participant Service as QuestionService
    participant Questions as questions.py
    participant Cache as question_cache
    participant Files as config.json, schema.json, question_bank

    Client->>Router: POST /goals {goal, action, api_token, questions}
    Router->>Service: manage_goals(request)
    Service->>Service: Validate api_token (api_tokens.json)
    alt Invalid api_token
        Service-->>Router: HTTP 401 (Invalid API token)
        Router-->>Client: Error response
    else Valid api_token
        Service->>Questions: Validate questions (goal, type, options)
        Questions-->>Service: Validated questions or error
        alt Validation error
            Service-->>Router: HTTP 400/500 (Validation error)
            Router-->>Client: Error response
        else Questions valid
            Service->>Questions: count_questions_for_goal(goal)
            Questions-->>Service: Existing question count
            alt Goal exists in supported_goals
                Service->>Questions: append_questions_to_bank(questions)
                Questions->>Files: Append to consolidated_questions_updated.json
                Questions-->>Service: Success
                Service->>Cache: clear()
                Service->>Questions: load_questions()
                Questions-->>Service: Updated question cache
                Service-->>Router: GoalResponse (Appended questions)
                Router-->>Client: Success response
            else New goal
                alt Total questions < 10
                    Service-->>Router: HTTP 400 (Insufficient questions)
                    Router-->>Client: Error response
                else Sufficient questions
                    Service->>Questions: append_questions_to_bank(questions)
                    Questions->>Files: Append to consolidated_questions_updated.json
                    Questions-->>Service: Success
                    Service->>Cache: clear()
                    Service->>Questions: load_questions()
                    Questions-->>Service: Updated question cache
                    Service->>Files: Update config.json (supported_goals)
                    Service->>Files: Update schema.json (goal enum)
                    Service-->>Router: GoalResponse (Goal added)
                    Router-->>Client: Success response
                end
            end
        end
    end
    Note over Client,Files: Shows flow for adding/removing goals with validation and file updates.

Testing





Run the Application:

docker-compose up -d --build



Test Endpoints:





Use curl, Postman, or Swagger UI (/docs).



Examples: Add goals, generate quizzes, check health (see Usage).



Verify Logs:

docker logs <container_id>
docker exec <container_id> tail -f /app/logs/app.log



Run Unit Tests:

docker exec -it <container_id> bash
python -m unittest tests/test_goals.py -v

Troubleshooting





500 Errors: Check config.json, schema.json, or consolidated_questions_updated.json for validity. Inspect app.log for details.



401 on POST /goals: Verify api_token matches api_tokens.json.



No Questions in POST /generate: Ensure questions exist for the goal/difficulty or templates are defined in questionTemplates.py.



Blank Health Dashboard: Confirm performance_metrics.json exists and internet access for Chart.js CDN. Check browser console for errors.



Debugging:





Enable debug logging: Set "level": "DEBUG" in config.json and restart.



Inspect logs: docker exec <container_id> tail -f /app/logs/app.log.

Contributing





Fork and Clone:

git clone <repository-url>
cd <repository-directory>
git checkout -b feature/<feature-name>



Make Changes:





Add templates to questionTemplates.py.



Enhance tfidfGenerator.py for better retrieval.



Update question_service.py for new features.



Add tests in tests/.



Test:

python -m unittest discover tests/



Submit Pull Request:





Push changes and create a pull request with a clear description.



Follow PEP 8, include type hints, and aim for >80% test coverage.

License

This project is licensed under the MIT License. See the LICENSE file for details.

Contact

For questions or support, contact:





Email: t.raviteja@gmail.com