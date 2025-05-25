# Smart Quiz Generator Microservice

The Questions API is a FastAPI-based application designed to serve quiz questions for educational and professional goals, managed via a curated list in `config.json`. It supports multiple question types (MCQ and short answer) and difficulty levels (beginner, intermediate, advanced). The API provides endpoints for retrieving questions, generating customized quizzes, managing supported goals with authentication, monitoring system health with visualizations, and analyzing performance metrics, all built with a focus on modularity, scalability, and maintainability.

## Project Structure

The codebase is organized to promote separation of concerns and ease of maintenance:

project_root/ ├── app/ │ ├── api/ │ │ ├── init.py │ │ ├── routes.py # API endpoint definitions │ │ ├── middleware.py # Middleware and lifespan handlers │ │ ├── models.py # Pydantic models for request/response │ ├── services/ │ │ ├── init.py │ │ ├── question_service.py # Business logic for question-related operations │ │ ├── infra_service.py # Infrastructure-related logic (health, metrics) │ ├── generators/ │ │ ├── init.py │ │ ├── base.py # Base generator interface │ │ ├── retrieval/ │ │ │ ├── init.py │ │ │ ├── tfidf.py # TF-IDF retrieval logic │ │ │ ├── preprocess.py # Text preprocessing │ │ ├── templates/ │ │ │ ├── init.py │ │ │ ├── QuizTemplateGenerator.py # Template-driven question generator │ │ │ ├── templates.py # Question template definitions │ ├── utils/ │ │ ├── config_loader.py # Configuration loading and logging setup │ │ ├── exceptions.py # Custom exception handlers │ ├── templates/ │ │ ├── health_visualization.html # Chart.js dashboard for health endpoint │ ├── init.py │ ├── questions.py # Question loading and validation logic │ ├── main.py # FastAPI app initialization and server ├── config.json # Configuration file ├── schema.json # JSON Schema for goal validation ├── api_tokens.json # API token for authentication ├── data/ │ ├── consolidated_questions_updated.json # Question bank ├── tests/ │ ├── test_goals.py # Tests for POST /goals endpoint ├── logs/ │ ├── app.log # Application logs │ ├── metrics.log # Metrics logs │ ├── performance.log # Performance logs ├── Dockerfile # Docker build instructions ├── docker-compose.yaml # Docker Compose configuration ├── performance_metrics.json # Performance metrics for health dashboard ├── README.md # Project documentation


## Features and Highlights

The Questions API offers a rich set of features, designed to deliver a reliable and developer-friendly experience:

### Flexible Question Management
- Retrieve all questions from a dataset with `GET /questions`, supporting both MCQ and short-answer formats.
- Generate tailored quizzes with `POST /generate`, allowing customization by goal, difficulty (beginner, intermediate, advanced), and number of questions (1–10).
- Validate questions rigorously using Pydantic models and custom validation logic to ensure data integrity (e.g., exactly 4 options for MCQs, null options for short answers).

### Goal Management
- Add or remove supported goals via `POST /goals`, updating `config.json` and generating `schema.json` with the JSON Schema for valid goals.
- Requires an API token (`api_token`) stored in `api_tokens.json` for authentication.
- For new goals, requires at least 10 questions in the question bank (`data/consolidated_questions_updated.json`) or provided in the request, ensuring sufficient content.
- For existing goals, appends provided questions to the question bank without modifying `supported_goals`.
- Prevents removal of goals with associated questions in the question bank, maintaining data integrity.
- Uses atomic file updates with `filelock` to prevent race conditions during configuration changes.

### Dynamic Question Generation
- **Retrieval Mode**: Uses TF-IDF (`tfidfGenerator.py`) to rank questions based on goal relevance, selecting high-quality questions from the question bank (`consolidated_questions_updated.json`).
- **Template Mode**: Generates formula-driven and logic-based questions (`QuizTemplateGenerator.py`) using Jinja2 templates defined in `templates.py`. Supports mathematical (e.g., quadratic equations, propulsion calculations), algorithmic (e.g., time complexity), and aptitude questions (e.g., probability, logical reasoning) with SymPy for accuracy.
- Configurable generation mode via `config.json` (`generator_mode`), with runtime toggling via the `mode` parameter in `POST /generate` (e.g., `retrieval`, `template`).
- Template-based generation creates dynamic questions for GATE AE (e.g., aerodynamics, mechanics), Amazon SDE (e.g., data structures, AWS), and CAT (e.g., quantitative ability, logical reasoning), ensuring variety and freshness.

### Optimized Response Structure
- Employs a Pydantic inheritance model for responses, with `QuestionResponseBase` as the base class and `McqQuestionResponse` and `ShortAnswerQuestionResponse` as subclasses.
- Ensures clean responses by excluding the `options` field for `short_answer` questions, improving readability and reducing payload size.
- Provides type safety and extensibility, allowing easy addition of new question types (e.g., coding questions) through new subclasses.

### Robust Infrastructure Monitoring
- Health checks via `GET /health`, providing detailed status reports on critical dependencies (question bank, configuration) and question counts by goal and type.
- Visualization dashboard via `GET /health?visualize=true`, displaying Chart.js charts (loaded via CDN: `https://cdn.jsdelivr.net/npm/chart.js`) for:
  - Question counts by goal (e.g., GATE AE, Amazon SDE).
  - Question counts by type (MCQ, short answer) per goal.
  - Performance metrics (request count, throughput, latency, error rate).
- Real-time metrics with `GET /local-metrics`, including request counts, average latencies, and error counts, stored in Redis for high performance.
- Aggregated performance metrics via `GET /performance-metrics`, offering insights into throughput, latency statistics (average, min, max, p95), and error rates, stored in `performance_metrics.json`.

### Configuration Management
- Expose configuration details with `GET /config`, including supported goals, generator mode, and version.
- Configurable via `config.json`, supporting settings for data paths, caching, logging, and monitoring intervals.
- Generates `schema.json` with JSON Schema for `GenerateQuestionsRequest.goal`, updated dynamically when goals are added or removed.
- Stores API token in `api_tokens.json` for `POST /goals` authentication.

### Modular Architecture
- Organized into an `api` package for routing, middleware, and models, separating HTTP concerns from business logic.
- Service layer with `QuestionService` for question/goal management and `InfraService` for health/metrics, enhancing modularity and testability.
- Dedicated `generators` package for question generation, supporting:
  - Retrieval (`tfidfGenerator.py`) for question bank selection.
  - Template-based (`QuizTemplateGenerator.py`, `templates.py`) for dynamic question creation.
- Dependency injection in FastAPI routes to provide service instances, supporting clean and reusable code.

### Performance Optimization
- Thread-safe caching with `TTLCache` for question loading and TF-IDF computations, configurable via `CACHE_MAXSIZE` and `CACHE_TTL`.
- Parallel processing for large datasets using `ThreadPoolExecutor`, controlled by `MAX_WORKERS`.
- Efficient JSON parsing with `orjson` for faster data loading.
- Redis-based metrics storage eliminates file locking overhead, improving throughput under high concurrency.

### Comprehensive Logging
- Structured JSON logging using `structlog` for application, metrics, and performance logs.
- Rotating log files (`logs/app.log`, `logs/metrics.log`, `logs/performance.log`) with daily rotation and 7-day retention, configurable in `config.json`.
- Detailed logging of requests, errors, and metrics updates, with enhanced validation logging to identify problematic question entries.

### Error Handling
- Standardized JSON error responses using a custom `ErrorResponse` model.
- Custom exception handlers for validation errors, HTTP exceptions, authentication failures, and service unavailability, ensuring consistent error reporting.
- Detailed error logging with request context for traceability.

### Developer-Friendly
- Interactive API documentation via Swagger UI (`/docs`) and ReDoc (`/redoc`).
- Clear endpoint descriptions with supported parameters, response models, and error codes.
- Extensible design for adding new endpoints or features with minimal changes.
- Dockerized deployment with `Dockerfile` and `docker-compose.yaml` for easy setup.

## Sequence Diagram

The following sequence diagram illustrates the `POST /goals` endpoint for adding a new goal with questions, including API token authentication, question validation, and file updates. It is represented in Mermaid syntax and can be rendered using tools like Mermaid Live Editor or GitHub.

```mermaid
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

Notes:





The diagram shows the flow for adding a new goal with questions, including validation, cache clearing, and file updates.



For existing goals, the flow skips config.json and schema.json updates, appending only questions.



For the remove action, the flow would validate the token, check for no questions in the bank, and update config.json/schema.json.

High-Level Design (HLD)

The Questions API is a modular, containerized FastAPI application designed for quiz question management and generation. Below is an overview of the system architecture and key components:

Architecture Overview

The system follows a layered architecture with clear separation of concerns, deployed as a Docker container:





Client Layer: External clients (e.g., web apps, CLI tools) interact with the API via HTTP requests (e.g., POST /goals, POST /generate).



API Layer: FastAPI handles HTTP routing, request validation, and response serialization, defined in app/api/routes.py and app/api/models.py.



Service Layer: Business logic is encapsulated in QuestionService (app/services/question_service.py) for question/goal management and InfraService (app/services/infra_service.py) for health/metrics.



Generator Layer: Question generation logic is abstracted into:





Retrieval (tfidfGenerator.py) for selecting questions from the question bank.



Template-based (QuizTemplateGenerator.py, templates.py) for dynamic question creation.



Data Layer: File-based storage using JSON files (config.json, schema.json, data/consolidated_questions_updated.json, api_tokens.json) for configuration, schema, questions, and authentication.



Cache Layer: TTLCache (app/questions.py) caches question bank data to optimize performance.



Logging/Monitoring: Structured logging (structlog) to logs/app.log and metrics to Redis/metrics.json for observability.

Components and Data Flow

Client Request





Clients send HTTP requests (e.g., POST /goals with api_token and questions).



FastAPI validates the request using Pydantic models (app/api/models.py).

Routing





app/api/routes.py routes requests to the appropriate service method (e.g., QuestionService.add_goal).

Business Logic





QuestionService handles authentication (api_tokens.json), question validation (questions.py), and file updates.



For POST /goals, it validates the api_token, checks question counts, appends questions, updates config.json/schema.json, and clears the cache.

Question Generation





TfidfGenerator retrieves questions from the cached question bank using TF-IDF ranking.



QuizTemplateGenerator generates questions using Jinja2 templates (templates.py) and SymPy for mathematical and logical accuracy.

Storage





Questions are stored in data/consolidated_questions_updated.json.



Configuration and schema are stored in config.json and schema.json.



File operations use filelock for thread safety.

Cache





question_cache (TTLCache) caches load_questions results, cleared when questions are appended.

Logging/Monitoring





Logs are written to logs/app.log, logs/metrics.log, and logs/performance.log.



Metrics are stored in Redis (optional) or metrics.json/performance_metrics.json.

Data Flow Example (POST /goals)





Client sends POST /goals with goal, action, api_token, and questions.



FastAPI validates the request and routes to QuestionService.add_goal.



QuestionService:





Validates api_token against api_tokens.json.



Validates questions using questions._validate_question_item.



Checks question count via questions.count_questions_for_goal.



Appends questions to consolidated_questions_updated.json via questions.append_questions_to_bank.



Clears question_cache and reloads questions_cache.



Updates config.json and schema.json if adding a new goal.



Response is returned to the client with updated supported_goals.

Low-Level Design (LLD)

The Low-Level Design focuses on the POST /goals endpoint, detailing its implementation, data structures, and error handling.

Endpoint: POST /goals





Path: /goals



Method: POST



Request Model: GoalRequest (app/api/models.py):

class GoalRequest(BaseModel):
    goal: str  # e.g., "New Goal"
    action: str  # "add" or "remove"
    api_token: str  # e.g., "secure-token-123"
    questions: Optional[List[QuizQuestion]]  # Optional questions to append



Response Model: GoalResponse (app/api/models.py):

class GoalResponse(BaseModel):
    message: str  # e.g., "Goal 'New Goal' added successfully with 10 questions"
    supported_goals: List[str]  # e.g., ["GATE AE", "Amazon SDE", "New Goal"]

Components

Router (app/api/routes.py)





Method: manage_goals



Validates GoalRequest using Pydantic.



Calls QuestionService.add_goal or remove_goal based on action.



Returns GoalResponse or raises HTTP exceptions (400, 401, 500).

QuestionService (app/services/question_service.py)





Initialization:





Loads api_token from api_tokens.json.



Initializes questions_cache with load_questions.



Sets up generators (TfidfGenerator, QuizTemplateGenerator).



add_goal:





Inputs: goal, questions (optional), api_token.



Steps:





Validate api_token against self.api_token.



Validate questions using questions._validate_question_item, ensuring goal matches and format is valid (e.g., 4 options for MCQ, null for short_answer).



Check if goal exists in CONFIG['supported_goals']:





If exists, append questions via append_questions_to_bank, clear question_cache, reload questions_cache, and return.



If new, proceed with further checks.



Count existing questions (count_questions_for_goal) and provided questions, requiring ≥10 total.



If no questions exist/provided, raise 400 error.



Append questions (if any) to consolidated_questions_updated.json.



Clear question_cache and reload questions_cache.



Update config.json (supported_goals) and schema.json (goal enum) with filelock.



Return GoalResponse.



Error Handling:





401: Invalid api_token.



400: Invalid goal, insufficient questions, mismatched question goal.



500: File I/O or validation errors.



remove_goal:





Validates api_token and checks if goal exists in supported_goals.



Ensures no questions exist in the bank (get_goals_in_question_bank).



Removes goal from config.json and updates schema.json.



Returns GoalResponse.

Questions Module (app/questions.py)





QuizQuestion: Pydantic model for question structure.



_validate_question_item: Validates question fields (type, options, difficulty, etc.).



load_questions: Loads and validates questions from consolidated_questions_updated.json, cached with question_cache.



get_goals_in_question_bank: Returns unique goals in the question bank.



count_questions_for_goal: Counts questions for a goal.



append_questions_to_bank: Appends questions to consolidated_questions_updated.json with filelock.

Cache (question_cache)





TTLCache with CACHE_MAXSIZE and CACHE_TTL from config.json.



Cleared in add_goal after appending questions to refresh the question bank.

File Storage





config.json: Stores supported_goals, DATA_DIR, etc.



schema.json: JSON Schema for goal validation.



consolidated_questions_updated.json: Question bank (list of question objects).



api_tokens.json: Stores api_token.

Data Structures





QuizQuestion:

class QuizQuestion(BaseModel):
    type: str  # "mcq" or "short_answer"
    question: str  # Question text
    options: Optional[List[str]]  # 4 options for MCQ, null for short_answer
    answer: str  # Correct answer
    difficulty: str  # "beginner", "intermediate", "advanced"
    topic: str  # Topic name
    goal: str  # Target goal (e.g., "GATE AE")



CONFIG: Dictionary loaded from config.json, containing supported_goals, supported_difficulties, etc.



question_cache: TTLCache storing List[QuizQuestion] from load_questions.

Error Handling





Validation Errors:





Invalid api_token: 401.



Invalid question format (e.g., MCQ with ≠4 options): 400.



Insufficient questions (<10): 400.



Goal not in bank/no questions provided: 400.



File I/O Errors:





Failed file reads/writes: 500 with logged error.



Cache Management:





Cache cleared safely; reload failures logged as 500.

Performance Considerations





Cache: TTLCache reduces file I/O (~10–20ms for 1000 questions).



File Operations: filelock ensures thread safety but may add latency (~1–2ms per write).



Validation: Pydantic and custom validation add minimal overhead (~1ms per question).



Parallel Processing: ThreadPoolExecutor for large question banks (>100 questions).

Installation

Prerequisites





Python 3.10 or higher (for local development)



pip (Python package manager)



Docker and Docker Compose (for containerized deployment)



Git (optional, for cloning the repository)



Redis (optional, for metrics storage)



Internet access (required for Chart.js CDN in the health dashboard)

Steps





Clone the Repository (if using Git):

git clone <repository-url>
cd <repository-directory>



Set Up Configuration Files:





Ensure the following files are present in the project root:





config.json: Configuration settings (see Configuration).



schema.json: JSON Schema for API inputs/outputs (see Configuration).



api_tokens.json: API token for POST /goals authentication (e.g., {"api_token": "secure-token-123"}).



performance_metrics.json: Performance metrics for the health dashboard (see Configuration).



Ensure data/consolidated_questions_updated.json exists in the data/ directory with a valid question bank.



Restrict permissions for api_tokens.json:

chmod 600 api_tokens.json



Local Development (Optional):





Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate



Install dependencies:

pip install -r requirements.txt



Run the application:

python app/main.py



The API will be available at http://127.0.0.1:8000.



Dockerized Deployment:





Build and run the application using Docker Compose:

docker-compose up -d --build



The API will be available at http://127.0.0.1:8000.



To stop the application:

docker-compose down



Access API Documentation:





Open http://127.0.0.1:8000/docs in a browser for interactive Swagger UI.



Alternatively, use http://127.0.0.1:8000/redoc for ReDoc documentation.

Configuration

The application uses config.json for configuration, schema.json for goal validation, api_tokens.json for authentication, and performance_metrics.json for performance metrics. Below are sample configurations:

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
    "title": "Smart Quiz API Input and Output Schema",
    "type": "object",
    "definitions": {
        "question": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["mcq", "short_answer"],
                    "description": "The type of question (multiple-choice or short-answer)."
                },
                "question": {
                    "type": "string",
                    "description": "The question text."
                },
                "options": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "string"
                    },
                    "description": "List of answer options for MCQ questions. Null for short-answer questions."
                },
                "answer": {
                    "type": "string",
                    "description": "The correct answer. For MCQ, format is 'option. text' (e.g., 'B. O(log n)'). For short-answer, the answer text or value."
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced"],
                    "description": "The difficulty level of the question."
                },
                "topic": {
                    "type": "string",
                    "description": "The subject or topic of the question."
                }
            },
            "required": ["type", "question", "options", "answer", "difficulty", "topic"],
            "additionalProperties": false
        },
        "inputRequest": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "enum": ["GATE AE", "Amazon SDE", "CAT", "MAT"],
                    "description": "The target exam or role for the quiz."
                },
                "num_questions": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Number of questions to generate."
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced"],
                    "description": "Filter for difficulty level."
                },
                "mode": {
                    "type": ["string", "null"],
                    "enum": ["retrieval", "template", null],
                    "description": "Generation mode: 'retrieval' (TF-IDF) or 'template' (formula-driven). Defaults to config.generator_mode."
                }
            },
            "required": ["goal", "num_questions", "difficulty"],
            "additionalProperties": false,
            "description": "Schema for POST /generate request."
        },
        "outputResponse": {
            "type": "object",
            "properties": {
                "quiz_id": {
                    "type": "string",
                    "pattern": "^quiz_[0-9]+$",
                    "description": "Unique identifier for the quiz."
                },
                "goal": {
                    "type": "string",
                    "enum": ["GATE AE", "Amazon SDE", "CAT", "MAT"],
                    "description": "The target exam or role for the quiz."
                },
                "questions": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/question"
                    },
                    "description": "List of generated questions."
                }
            },
            "required": ["quiz_id", "goal", "questions"],
            "additionalProperties": false,
            "description": "Schema for POST /generate response."
        }
    },
    "properties": {
        "inputRequest": {
            "$ref": "#/definitions/inputRequest"
        },
        "outputResponse": {
            "$ref": "#/definitions/outputResponse"
        }
    },
    "additionalProperties": false
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
    },
    {
        "timestamp": "2025-05-25T19:01:00",
        "request_count": 120,
        "throughput": 12.0,
        "avg_latency": 0.12,
        "min_latency": 0.06,
        "max_latency": 0.22,
        "p95_latency": 0.17,
        "error_rate": 0.02
    }
]

Configuration Notes





DATA_DIR and DATASET: Set DATA_DIR: "/data" to match the volume mount in docker-compose.yaml. Ensure data/consolidated_questions_updated.json exists in the mounted directory (e.g., E:/smart-quiz/data on the host). The dataset should be a JSON file containing a list of questions with fields like type, question, options (null for short_answer), answer, difficulty, topic, and goal.



supported_goals: Managed via POST /goals. Add goals with at least 10 questions in the question bank or provided; append questions to existing goals; remove goals only if they have no associated questions.



schema.json: Automatically updated by POST /goals to reflect the current supported_goals in the JSON Schema for GenerateQuestionsRequest.goal.



api_tokens.json: Stores the API token for POST /goals authentication. Ensure file permissions are restricted (e.g., chmod 600 api_tokens.json).



performance_metrics.json: Stores performance metrics for the /health?visualize=true dashboard. Create this file in the project root to ensure the performance metrics chart renders correctly.



Logging: Logs are written to logs/app.log, logs/metrics.log, and logs/performance.log with daily rotation (7-day retention).



Monitoring: Metrics are stored in Redis (if configured) for real-time access, with aggregated metrics in metrics.json and performance_metrics.json. The performance_aggregation_interval controls aggregation frequency (in seconds).



Chart.js: The health dashboard uses the Chart.js CDN (https://cdn.jsdelivr.net/npm/chart.js) for rendering charts, requiring internet access.

Usage

Endpoints





GET /questions: Retrieve all available questions from the question bank.



POST /generate:





Request body: {"goal": "GATE AE", "difficulty": "beginner", "num_questions": 5, "mode": "template"}



Generates a quiz with the specified parameters, using either retrieval (tfidfGenerator.py) or template-based (QuizTemplateGenerator.py, templates.py) generation. The goal must be in supported_goals (managed via POST /goals).



POST /goals:





Request body: {"goal": "GATE AE", "action": "add", "api_token": "secure-token-123", "questions": [...]} or {"goal": "GATE AE", "action": "remove", "api_token": "secure-token-123"}



Adds a new goal to supported_goals, appends questions to an existing goal, or removes a goal, updating config.json and schema.json as needed. Requires a valid api_token.



GET /health: Check API health (returns healthy or unhealthy with details). Use ?visualize=true to view a Chart.js dashboard with question counts by goal, question counts by type (MCQ, short answer) per goal, and performance metrics.



GET /config: Retrieve configuration details, including supported goals, generator mode, and version.



GET /local-metrics: View request counts, average latencies, and error counts.



GET /performance-metrics: View aggregated performance metrics (e.g., throughput, latency stats).

Example Request (POST /goals - Add New Goal with Questions)

Using curl to add a new goal with questions (assuming 8 existing questions for New Goal):

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
            "question": "(Logical Reasoning) In a group of 5 people, if A is friends with B and C, and B is not friends with D, who can be friends with E?",
            "options": ["A only", "B and C", "D only", "Anyone"],
            "answer": "Anyone",
            "difficulty": "intermediate",
            "topic": "Logical Reasoning"
        },
        {
            "goal": "New Goal",
            "type": "short_answer",
            "question": "Let f(x, y) = x^3 + y^3 - 3xy. The total number of critical points of the function is",
            "options": null,
            "answer": "2",
            "difficulty": "intermediate",
            "topic": "Mathematics"
        }
    ]
}'

Example Response

{
    "message": "Goal 'New Goal' added successfully with 10 questions",
    "supported_goals": ["GATE AE", "Amazon SDE", "CAT", "MAT", "New Goal"]
}

Example Request (POST /goals - Append Questions to Existing Goal)

curl -X POST "http://127.0.0.1:8000/goals" \
-H "Content-Type: application/json" \
-d '{
    "goal": "GATE AE",
    "action": "add",
    "api_token": "secure-token-123",
    "questions": [
        {
            "goal": "GATE AE",
            "type": "mcq",
            "question": "What is a sorting algorithm for GATE AE?",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
            "difficulty": "beginner",
            "topic": "algorithms"
        }
    ]
}'

Example Response

{
    "message": "Appended 1 questions to existing goal 'GATE AE'",
    "supported_goals": ["GATE AE", "Amazon SDE", "CAT", "MAT", "New Goal"]
}

Example Request (POST /goals - Remove Goal)

curl -X POST "http://127.0.0.1:8000/goals" \
-H "Content-Type: application/json" \
-d '{"goal": "CAT", "action": "remove", "api_token": "secure-token-123"}'

Example Response

{
    "message": "Goal 'CAT' removed successfully",
    "supported_goals": ["GATE AE", "Amazon SDE", "MAT", "New Goal"]
}

Example Request (POST /generate - Template Mode)

Using a supported goal with template-based generation:

curl -X POST "http://127.0.0.1:8000/generate" \
-H "Content-Type: application/json" \
-d '{"goal": "GATE AE", "difficulty": "beginner", "num_questions": 2, "mode": "template"}'

Example Response

{
    "quiz_id": "quiz_1234",
    "goal": "GATE AE",
    "questions": [
        {
            "type": "short_answer",
            "question": "Solve 2x² + 5x + 3 = 0 for x (round to 2 decimal places).",
            "answer": "-1.50, -1.00",
            "difficulty": "beginner",
            "topic": "algebra"
        },
        {
            "type": "short_answer",
            "question": "The thrust of a jet engine with mass flow rate 50 kg/s and exhaust velocity 600 m/s is (in kN, to two decimal places):",
            "answer": "30.00",
            "difficulty": "beginner",
            "topic": "propulsion"
        }
    ]
}

Example Request (POST /generate - Retrieval Mode)

curl -X POST "http://127.0.0.1:8000/generate" \
-H "Content-Type: application/json" \
-d '{"goal": "GATE AE", "difficulty": "beginner", "num_questions": 1, "mode": "retrieval"}'

Example Response (MCQ)

{
    "quiz_id": "quiz_1234",
    "goal": "GATE AE",
    "questions": [
        {
            "type": "mcq",
            "question": "What is a sorting algorithm for GATE AE?",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
            "difficulty": "beginner",
            "topic": "algorithms"
        }
    ]
}

Example Request (GET /health - Visualization Dashboard)

To view the Chart.js dashboard with question counts by goal, question counts by type per goal, and performance metrics:

curl http://127.0.0.1:8000/health?visualize=true

Or open in a browser:

http://127.0.0.1:8000/health?visualize=true

Example Response (Visualization)

Returns an HTML page with:





Bar Chart (Question Count by Goal): Displays total question counts per goal (e.g., GATE AE: 117, Amazon SDE: 144).



Bar Charts (Question Count by Type per Goal): For each goal, shows counts of MCQ and short-answer questions (e.g., GATE AE: 60 MCQ, 57 Short Answer).



Line Chart (Performance Metrics): Plots request count, throughput, average latency, and error rate over time, based on performance_metrics.json.



Description: The dashboard displays the API's health status, detailed statistics (e.g., question bank availability, question counts by goal/type), and three sets of interactive Chart.js charts (loaded via CDN: https://cdn.jsdelivr.net/npm/chart.js). The first bar chart shows the distribution of questions across goals. The per-goal bar charts break down question counts by type (MCQ, Short Answer) for each goal. The line chart tracks performance metrics over the last recorded intervals. A debug section (hidden by default) shows chart_data and errors if charts fail to render.

Testing





Run the Application:

docker-compose up -d --build



Test Endpoints:





Use tools like curl, Postman, or the Swagger UI (/docs).



Example: Add a new goal with questions (ensure ≥8 existing questions for New Goal):

curl -X POST "http://127.0.0.1:8000/goals" -H "Content-Type: application/json" -d '{"goal": "New Goal", "action": "add", "api_token": "secure-token-123", "questions": [{"goal": "New Goal", "type": "mcq", "question": "(Logical Reasoning) In a group of 5 people, if A is friends with B and C, and B is not friends with D, who can be friends with E?", "options": ["A only", "B and C", "D only", "Anyone"], "answer": "Anyone", "difficulty": "intermediate", "topic": "Logical Reasoning"}, {"goal": "New Goal", "type": "short_answer", "question": "Let f(x, y) = x^3 + y^3 - 3xy. The total number of critical points of the function is", "options": null, "answer": "2", "difficulty": "intermediate", "topic": "Mathematics"}]}'



Example: Append questions to existing goal:

curl -X POST "http://127.0.0.1:8000/goals" -H "Content-Type: application/json" -d '{"goal": "GATE AE", "action": "add", "api_token": "secure-token-123", "questions": [{"goal": "GATE AE", "type": "mcq", "question": "What is a sorting algorithm for GATE AE?", "options": ["A", "B", "C", "D"], "answer": "A", "difficulty": "beginner", "topic": "algorithms"}]}'



Example: Remove a goal (ensure no questions for CAT):

curl -X POST "http://127.0.0.1:8000/goals" -H "Content-Type: application/json" -d '{"goal": "CAT", "action": "remove", "api_token": "secure-token-123"}'



Example: Generate a quiz:

curl -X POST "http://127.0.0.1:8000/generate" -H "Content-Type: application/json" -d '{"goal": "GATE AE", "difficulty": "beginner", "num_questions": 2, "mode": "template"}'



Example: Check health with visualization:

curl http://127.0.0.1:8000/health?visualize=true

Or open http://127.0.0.1:8000/health?visualize=true in a browser (requires internet access for Chart.js CDN).



Verify Logs:





Check container logs for structured JSON entries:

docker logs <container_id>



Look for logs about goal additions/removals (e.g., "Goal 'New Goal' added to supported goals") and chart data generation (e.g., "Chart data generated: {...}").



Verify Metrics:





Check Redis (if configured) for real-time metrics via GET /local-metrics.



Inspect metrics.json and performance_metrics.json within the container:

docker exec <container_id> cat /app/metrics.json
docker exec <container_id> cat /app/performance_metrics.json



Run Unit Tests:





Access the container:

docker exec -it <container_id> bash



Run tests:

python -m unittest tests/test_goals.py -v

Debugging Blank Page Issues

If http://127.0.0.1:8000/health?visualize=true displays a blank page:





Check Internet Access: The Chart.js CDN (https://cdn.jsdelivr.net/npm/chart.js) requires internet access. Ensure your environment allows outbound connections.



Browser Console:





Open Developer Tools (F12) in the browser.



Check the Console tab for errors (e.g., Chart is not defined or CDN failures).



Check the Network tab to verify the CDN request (https://cdn.jsdelivr.net/npm/chart.js) returns 200.



Verify performance_metrics.json:





Ensure performance_metrics.json exists in the project root and contains valid data (see Configuration).



Copy to the container if needed:

docker cp performance_metrics.json <container_id>:/app/



Check Logs:





Inspect container logs for errors:

docker logs <container_id>



Look for issues loading consolidated_questions_updated.json or performance_metrics.json.



Test JSON Response:





Verify the health endpoint without visualization:

curl http://127.0.0.1:8000/health



Ensure it returns a healthy status with question counts.

Troubleshooting

Common Issues and Solutions





API Returns 500 Errors:





Cause: Missing or corrupt config.json, schema.json, or consolidated_questions_updated.json.



Solution: Verify files exist and are valid JSON. Check logs (logs/app.log) for specific errors.



Command:

docker exec <container_id> cat /app/config.json
docker exec <container_id> cat /app/schema.json
docker exec <container_id> cat /data/consolidated_questions_updated.json



POST /goals Fails with 401:





Cause: Invalid api_token in request.



Solution: Ensure api_token matches api_tokens.json (e.g., "secure-token-123").



Command:

docker exec <container_id> cat /app/api_tokens.json



POST /generate Returns No Questions:





Cause: No questions match the specified goal and difficulty in consolidated_questions_updated.json (retrieval mode) or no templates in templates.py (template mode).



Solution:





For retrieval mode, add questions to consolidated_questions_updated.json via POST /goals.



For template mode, verify templates.py has templates for the goal and difficulty.



Check logs for ValueError: No templates available or similar.



Command:

docker logs <container_id> | grep "No templates available"



Health Dashboard Shows No Charts:





Cause: Missing performance_metrics.json or failed CDN request.



Solution: Ensure performance_metrics.json is valid and accessible. Test CDN connectivity (curl https://cdn.jsdelivr.net/npm/chart.js). Check browser console for errors.



Command:

docker exec <container_id> cat /app/performance_metrics.json
curl https://cdn.jsdelivr.net/npm/chart.js



Docker Container Fails to Start:





Cause: Missing volume mounts or incorrect paths in docker-compose.yaml.



Solution: Verify DATA_DIR in config.json matches the volume mount (e.g., /data). Ensure data/ directory exists on the host.



Command:

docker-compose logs
ls -l data/

Logging and Debugging





View Logs:

docker exec <container_id> tail -f /app/logs/app.log
docker exec <container_id> tail -f /app/logs/metrics.log
docker exec <container_id> tail -f /app/logs/performance.log



Enable Debug Logging:





Edit config.json to set "level": "DEBUG" in the logging section.



Restart the container:

docker-compose down
docker-compose up -d



Inspect Cache:





Check cache hits/misses in logs (question_cache entries).



Clear cache manually by restarting the container or appending questions via POST /goals.

Contributing

Contributions are welcome to enhance the Questions API. To contribute:





Fork the Repository:

git clone <repository-url>
cd <repository-directory>
git checkout -b feature/<feature-name>



Make Changes:





Add new templates to templates.py for template-based generation.



Enhance tfidfGenerator.py for improved retrieval accuracy.



Update question_service.py for new features (e.g., new question types).



Ensure code follows PEP 8 and includes unit tests in tests/.



Test Changes:





Run unit tests:

python -m unittest discover tests/



Test API endpoints with curl or Postman.



Submit a Pull Request:





Push changes to your fork:

git push origin feature/<feature-name>





Create a pull request with a clear description of changes and test results.



Code Review:





Address feedback from maintainers.



Ensure all tests pass and documentation is updated (e.g., README.md).

Contribution Guidelines





Code Style: Follow PEP 8, use type hints, and include docstrings.



Testing: Add unit tests for new features in tests/. Aim for >80% coverage.



Documentation: Update README.md and inline comments for clarity.



Commit Messages: Use clear, descriptive messages (e.g., Add new templates for CAT logical reasoning).



Issues: Check existing issues or create new ones for bugs/features before starting work.

License

This project is licensed under the MIT License. See the LICENSE file for details.

Contact

For questions, issues, or support, please contact:

Email: t.raviteja@gmail.com