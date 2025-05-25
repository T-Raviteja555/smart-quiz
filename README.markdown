Smart Quiz Generator Microservice

The Smart Quiz Generator Microservice is a FastAPI-based application designed to serve quiz questions for educational and professional goals, such as GATE AE, Amazon SDE, and CAT. It supports multiple question types (MCQ and short answer) and difficulty levels (beginner, intermediate, advanced). Managed via a curated configuration in config.json, the API provides endpoints for retrieving questions, generating customized quizzes, managing supported goals with authentication, monitoring system health with visualizations, and analyzing performance metrics. The system emphasizes modularity, scalability, and maintainability.

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
│   │   │   ├── tfidfGenerator.py          # TF-IDF retrieval logic
│        ├── templateRetrieval/
│   │   │   ├── __init__.py
│   │   │   ├── templateGenerator.py  # Template-driven question generator
│   │   │   ├── questionTemplates.py      # Question template definitions
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
│   ├── consolidated_questions_updated.json  # Question bank
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

Features

The microservice offers a robust set of features for quiz management and generation:

Flexible Question Management





Retrieve Questions: GET /questions fetches all questions from the question bank, supporting MCQ and short-answer formats.



Generate Quizzes: POST /generate creates tailored quizzes based on goal, difficulty, and number of questions (1–10).



Question Validation: Uses Pydantic models to ensure data integrity (e.g., MCQs have exactly 4 options; short answers have null options).

Goal Management





Manage Goals: POST /goals adds or removes goals in config.json, updating schema.json with valid goals.



Authentication: Requires an API token from api_tokens.json.



New Goals: Must have at least 10 questions in the question bank or provided in the request.



Existing Goals: Appends provided questions without modifying supported goals.



Data Integrity: Prevents goal removal if associated questions exist; uses filelock for thread-safe file updates.

Dynamic Question Generation





Retrieval Mode: Uses TF-IDF (tfidfGenerator.py) to select relevant questions from the question bank.



Template Mode: Generates dynamic questions (QuizTemplateGenerator.py) using Jinja2 templates and SymPy for mathematical and logical accuracy.



Configurable Modes: Set via config.json or overridden in POST /generate (retrieval or template).



Supported Goals: Includes GATE AE (e.g., aerodynamics), Amazon SDE (e.g., algorithms), and CAT (e.g., quantitative aptitude).

Infrastructure Monitoring





Health Checks: GET /health reports status of dependencies and question counts.



Visualization Dashboard: GET /health?visualize=true displays Chart.js charts for question counts and performance metrics.



Metrics: GET /local-metrics and GET /performance-metrics provide real-time and aggregated performance data (e.g., latency, throughput).

Performance and Scalability





Caching: Thread-safe TTLCache for question loading and TF-IDF computations.



Parallel Processing: Uses ThreadPoolExecutor for large datasets.



Logging: Structured JSON logs with daily rotation using structlog.



Error Handling: Standardized JSON error responses with custom exception handlers.

Developer-Friendly





API Documentation: Interactive Swagger UI (/docs) and ReDoc (/redoc).



Dockerized Deployment: Simplifies setup with Dockerfile and docker-compose.yaml.



Extensibility: Modular design for adding new question types or endpoints.

Sequence Diagram

The following Mermaid sequence diagram illustrates the POST /goals endpoint for adding a new goal with questions, including authentication, validation, and file updates:

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
        Service->>Questions: Validate questions (goal, type, options, etc.)
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

    Note over Client,Files: Adds a new goal with questions, including validation and file updates.
    Note over Client,Files: For existing goals, skips config.json/schema.json updates, only appends questions.
    Note over Client,Files: For removal, validates token and ensures no questions exist in the bank.

Installation

Prerequisites





Python 3.10+ (for local development)



pip (Python package manager)



Docker and Docker Compose (for containerized deployment)



Redis (optional, for metrics storage)



Internet access (for Chart.js CDN in health dashboard)

Steps





Clone the Repository (if using Git):

git clone <repository-url>
cd <repository-directory>



Set Up Configuration Files:





Ensure config.json, schema.json, api_tokens.json, and performance_metrics.json are in the project root.



Place consolidated_questions_updated.json in the data/ directory.



Restrict permissions for api_tokens.json:

chmod 600 api_tokens.json



Local Development (Optional):





Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate



Install dependencies:

pip install -r requirements.txt



Run the application:

python app/main.py



Access the API at http://127.0.0.1:8000.



Dockerized Deployment:





Build and run:

docker-compose up -d --build



Stop the application:

docker-compose down



Access the API at http://127.0.0.1:8000.



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
    "supported_goals": ["GATE AE", "Amazon SDE", "CAT", "MAT"],
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

schema.json

{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Smart Quiz API Schema",
    "type": "object",
    "definitions": {
        "question": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["mcq", "short_answer"]},
                "question": {"type": "string"},
                "options": {"type": ["array", "null"], "items": {"type": "string"}},
                "answer": {"type": "string"},
                "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                "topic": {"type": "string"}
            },
            "required": ["type", "question", "options", "answer", "difficulty", "topic"],
            "additionalProperties": false
        },
        "inputRequest": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "enum": ["GATE AE", "Amazon SDE", "CAT", "MAT"]},
                "num_questions": {"type": "integer", "minimum": 1, "maximum": 10},
                "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                "mode": {"type": ["string", "null"], "enum": ["retrieval", "template", null]}
            },
            "required": ["goal", "num_questions", "difficulty"],
            "additionalProperties": false
        }
    }
}

api_tokens.json

{
    "api_token": "secure-token-123"
}

performance_metrics.json

[
    {
        "timestamp": "2025-05-25T19:00:00",
        "request_count": 100,
        "throughput": 10.0,
        "avg_latency": 0.1,
        "min_latency": 0.05,
        "max_latency": 0.2,
        "p95_latency": 0.15,
        "error_rate": 0.01
    }
]

Usage

Endpoints





GET /questions: Retrieve all questions from the question bank.



POST /generate: Generate a quiz (e.g., {"goal": "GATE AE", "difficulty": "beginner", "num_questions": 5, "mode": "template"}).



POST /goals: Add/remove goals or append questions (requires api_token).



GET /health: Check API health; use ?visualize=true for a Chart.js dashboard.



GET /config: View configuration details.



GET /local-metrics: Access real-time metrics.



GET /performance-metrics: View aggregated performance metrics.

Example: Add New Goal

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
    "supported_goals": ["GATE AE", "Amazon SDE", "CAT", "MAT", "New Goal"]
}

Example: Generate Quiz

curl -X POST "http://127.0.0.1:8000/generate" \
-H "Content-Type: application/json" \
-d '{"goal": "GATE AE", "difficulty": "beginner", "num_questions": 2, "mode": "template"}'

Response:

{
    "quiz_id": "quiz_1234",
    "goal": "GATE AE",
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

Testing





Run the Application:

docker-compose up -d --build



Test Endpoints:





Use curl, Postman, or Swagger UI (/docs).



Example: Add a goal, generate a quiz, or check health (http://127.0.0.1:8000/health?visualize=true).



Verify Logs:

docker logs <container_id>



Run Unit Tests:

docker exec -it <container_id> bash
python -m unittest tests/test_goals.py -v

Troubleshooting





500 Errors: Check config.json, schema.json, or consolidated_questions_updated.json for validity.



401 on POST /goals: Verify api_token matches api_tokens.json.



No Questions in POST /generate: Ensure questions exist for the goal/difficulty or templates are defined.



Blank Health Dashboard: Confirm performance_metrics.json exists and internet access for Chart.js CDN (https://cdn.jsdelivr.net/npm/chart.js).

Debugging:





View logs: docker exec <container_id> tail -f /app/logs/app.log



Enable debug logging: Set "level": "DEBUG" in config.json and restart.

Contributing





Fork and Clone:

git clone <repository-url>
cd <repository-directory>
git checkout -b feature/<feature-name>



Make Changes:





Add templates to templates.py or enhance tfidfGenerator.py.



Update question_service.py for new features.



Include unit tests in tests/.



Test and Submit:





Run tests: python -m unittest discover tests/



Push and create a pull request with clear descriptions.

Guidelines:





Follow PEP 8 and include type hints.



Aim for >80% test coverage.



Update README.md for new features.

License

This project is licensed under the MIT License. See the LICENSE file for details.

Contact

For questions or support, contact:





Email: t.raviteja@gmail.com