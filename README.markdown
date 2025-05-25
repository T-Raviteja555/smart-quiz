Questions API

The Questions API is a robust FastAPI-based application designed to serve quiz questions for specific educational and professional goals, such as GATE AE, Amazon SDE, CAT, and MAT. It supports multiple question types (MCQ and short answer) and difficulty levels (beginner, intermediate, advanced). The API provides endpoints for retrieving questions, generating customized quizzes, monitoring system health, and analyzing performance metrics, all built with a focus on modularity, scalability, and maintainability.

Project Structure

The codebase is organized to promote separation of concerns and ease of maintenance:

project_root/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # API endpoint definitions
│   │   ├── middleware.py      # Middleware and lifespan handlers
│   │   ├── models.py          # Pydantic models for request/response
│   ├── services/
│   │   ├── __init__.py
│   │   ├── question_service.py # Business logic for question-related operations
│   │   ├── infra_service.py    # Infrastructure-related logic (health, metrics)
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── base.py            # Base generator interface
│   │   ├── retrieval/
│   │   │   ├── __init__.py
│   │   │   ├── tfidf.py      # TF-IDF retrieval logic
│   │   │   ├── preprocess.py # Text preprocessing
│   │   ├── templates/
│   │   │   ├── __init__.py
│   │   │   ├── math.py       # Math formula-driven templates
│   ├── utils/
│   │   ├── config_loader.py   # Configuration loading and logging setup
│   │   ├── exceptions.py      # Custom exception handlers
│   ├── __init__.py
│   ├── questions.py           # Question loading and validation logic
│   ├── main.py                # FastAPI app initialization and server
├── config.json                # Configuration file
├── README.md                  # Project documentation

Features and Highlights

The Questions API offers a rich set of features, designed to deliver a reliable and developer-friendly experience:





Flexible Question Management:





Retrieve all questions from a dataset with GET /questions, supporting both MCQ and short-answer formats.



Generate tailored quizzes with POST /generate, allowing customization by goal (e.g., GATE AE, Amazon SDE), difficulty (beginner, intermediate, advanced), and number of questions (1–10).



Validate questions rigorously using Pydantic models and custom validation logic to ensure data integrity (e.g., exactly 4 options for MCQs, null options for short answers).



Dynamic Question Generation:





Retrieval Mode: Uses TF-IDF to rank questions based on goal relevance, ensuring high-quality question selection from the question bank.



Template Mode: Generates formula-driven questions (e.g., quadratic equations, propulsion calculations) using Jinja2 templates and SymPy for mathematical accuracy.



Configurable generation mode via config.json (generator_mode), with runtime toggling via the mode parameter in POST /generate (e.g., retrieval, template).



Optimized Response Structure:





Employs a Pydantic inheritance model for responses, with QuestionResponseBase as the base class and McqQuestionResponse and ShortAnswerQuestionResponse as subclasses.



Ensures clean responses by excluding the options field for short_answer questions, improving readability and reducing payload size (e.g., no "options": null in responses).



Provides type safety and extensibility, allowing easy addition of new question types (e.g., coding questions) through new subclasses.



Robust Infrastructure Monitoring:





Health checks via GET /health, providing detailed status reports on critical dependencies (question bank, configuration) and question counts by goal and type.



Real-time metrics with GET /local-metrics, including request counts, average latencies, and error counts, stored in Redis for high performance.



Aggregated performance metrics via GET /performance-metrics, offering insights into throughput, latency statistics (average, min, max, p95), and error rates, stored in performance_metrics.json.



Configuration Management:





Expose configuration details with GET /config, including generator mode, API version, supported goals, and question types.



Configurable via config.json, supporting settings for data paths, caching, logging, and monitoring intervals.



Modular Architecture:





Organized into an api package for routing, middleware, and models, separating HTTP concerns from business logic.



Service layer with QuestionService for question-related operations and InfraService for infrastructure tasks, enhancing modularity and testability.



Dedicated generators package for question generation, supporting both retrieval (TF-IDF) and template-based (formula-driven) methods.



Dependency injection in FastAPI routes to provide service instances, supporting clean and reusable code.



Performance Optimization:





Thread-safe caching with TTLCache for question loading and TF-IDF computations, configurable via CACHE_MAXSIZE and CACHE_TTL.



Parallel processing for large datasets using ThreadPoolExecutor, controlled by MAX_WORKERS.



Efficient JSON parsing with orjson for faster data loading.



Redis-based metrics storage eliminates file locking overhead, improving throughput under high concurrency.



Comprehensive Logging:





Structured JSON logging using structlog for application, metrics, and performance logs.



Rotating log files (app.log, metrics.log, performance.log) with daily rotation and 7-day retention, configurable in config.json.



Detailed logging of requests, errors, and metrics updates, with enhanced validation logging to identify problematic question entries.



Error Handling:





Standardized JSON error responses using a custom ErrorResponse model.



Custom exception handlers for validation errors, HTTP exceptions, and service unavailability, ensuring consistent error reporting.



Detailed error logging with request context for traceability.



Developer-Friendly:





Interactive API documentation via Swagger UI (/docs) and ReDoc (/redoc).



Clear endpoint descriptions with supported parameters, response models, and error codes.



Extensible design for adding new endpoints or features with minimal changes.

Installation

Prerequisites





Python 3.8 or higher



pip (Python package manager)



Git (optional, for cloning the repository)



Redis (optional, for metrics storage)

Steps





Clone the Repository (if using Git):

git clone <repository-url>
cd <repository-directory>



Create a Virtual Environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate



Install Dependencies: Create a requirements.txt file with the following content:

fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.8.2
structlog==24.4.0
orjson==3.10.7
cachetools==5.5.0
numpy==1.26.4
filelock==3.16.1
redis==5.0.8
scikit-learn==1.5.2
jinja2==3.1.4
sympy==1.13.3
typing-extensions==4.12.2

Then install:

pip install -r requirements.txt



Prepare Configuration:





Ensure config.json exists in the project root. A sample configuration is provided below under Configuration.



Verify the DATA_DIR and DATASET paths in config.json point to a valid question dataset (e.g., data/consolidated_questions_updated.json).



Run the Application:

python app/main.py

The API will be available at http://127.0.0.1:8000.



Access API Documentation:





Open http://127.0.0.1:8000/docs in a browser for interactive Swagger UI.



Alternatively, use http://127.0.0.1:8000/redoc for ReDoc documentation.

Configuration

The application uses a config.json file for configuration. Below is a sample configuration:

{
    "DATA_DIR": "data",
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
        "logpath": "app.log",
        "metrics_logpath": "metrics.log",
        "performance_logpath": "performance.log",
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

Configuration Notes





DATA_DIR and DATASET: Ensure the dataset file exists at the specified path (e.g., data/consolidated_questions_updated.json). The dataset should be a JSON file containing a list of questions with fields like type, question, options (null for short_answer), answer, difficulty, topic, and goal.



Logging: Logs are written to app.log, metrics.log, and performance.log with daily rotation (7-day retention).



Monitoring: Metrics are stored in Redis for real-time access, with aggregated metrics in performance_metrics.json. The performance_aggregation_interval controls aggregation frequency (in seconds).

Usage

Endpoints





GET /questions: Retrieve all available questions.



POST /generate:





Request body: {"goal": "GATE AE", "difficulty": "beginner", "num_questions": 5, "mode": "template"}



Generates a quiz with the specified parameters, using either retrieval (TF-IDF) or template-based (formula-driven) generation.



GET /health: Check API health (returns healthy or unhealthy with details).



GET /config: Retrieve configuration details (e.g., generator mode, version).



GET /local-metrics: View request counts, average latencies, and error counts.



GET /performance-metrics: View aggregated performance metrics (e.g., throughput, latency stats).

Example Request (POST /generate)

Using curl:

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
            "question": "Solve 2x² + 5x + 3 = 0 for x.",
            "answer": "-3/2, -1",
            "difficulty": "beginner",
            "topic": "algebra"
        },
        {
            "type": "short_answer",
            "question": "The thrust of a jet engine with mass flow rate 50 kg/s and exhaust velocity 600 m/s is (in kN, to one decimal place):",
            "answer": "30.0",
            "difficulty": "beginner",
            "topic": "propulsion"
        }
    ]
}

Example Request (MCQ Retrieval)

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

Testing





Run the Application:

python app/main.py



Test Endpoints:





Use tools like curl, Postman, or the Swagger UI (/docs).



Example: Test /health:

curl http://127.0.0.1:8000/health



Verify Logs:





Check app.log, metrics.log, and performance.log for structured JSON logs.



Ensure log rotation is working (new log files created daily).



Verify Metrics:





Check Redis for real-time metrics via GET /local-metrics.



Check performance_metrics.json for aggregated metrics (updated every 60 seconds by default).

Development

Adding New Endpoints





Define the endpoint in api/routes.py.



Add business logic to the appropriate service (QuestionService for question-related, InfraService for infrastructure-related).



Update Pydantic models in api/models.py if needed.



Register any new exception handlers in utils/exceptions.py.

Adding New Question Types





Extend the QuestionResponse union in api/models.py by adding a new subclass (e.g., CodingQuestionResponse) inheriting from QuestionResponseBase.



Update question_service.py to handle the new type in response construction.



Add corresponding validation in questions.py for the question bank.



Implement new generators in generators/templates/ if needed (e.g., coding.py).

Running Tests





Create a tests/ directory if not present.



Use pytest and httpx for unit and integration tests.



Example requirements.txt for testing:

pytest==8.3.3
httpx==0.27.2

Install:

pip install -r requirements.txt



Run tests:

pytest test_generate.py -v

Contributing





Fork the repository.



Create a feature branch (git checkout -b feature/<feature-name>).



Commit changes (git commit -m "Add feature").



Push to the branch (git push origin feature/<feature-name>).



Open a pull request.

License

This project is licensed under the MIT License. See the LICENSE file for details (create one if needed).

Contact

For issues or questions, please open an issue on the repository or contact the maintainer at t.raviteja@gmail.com.