# Smart Quiz Generator Microservice

![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-green.svg)
![Docker](https://img.shields.io/badge/Docker-enabled-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

The Smart Quiz Generator Microservice is a production-ready, FastAPI-based REST API designed to generate and manage quiz questions for educational and professional goals, including GATE, Amazon Software Development Engineer (SDE), and Common Admission Test (CAT). It supports multiple-choice (MCQ) and short-answer questions with TF-IDF retrieval and template-based generation, Dockerized deployment, structured JSON logging with daily rotation, JSON schema validation, and comprehensive unit testing. The project is modular, scalable, and extensible, ready for integration with advanced question generation models.

## Features

- **RESTful API**: Endpoints for retrieving questions, generating customized quizzes, managing goals, and monitoring health/performance.
- **Question Generation**: TF-IDF-based retrieval (`tfidfGenerator.py`) and template-based generation (`templateGenerator.py`) for dynamic questions.
- **Dataset**: 657 questions (GATE: 219, Amazon SDE: 225, CAT: 213) in `consolidated_questions_updated.json`.
- **Production-Ready**:
  - Thread-safe file operations with `filelock`.
  - Structured JSON logging with daily rotation (`structlog`).
  - Real-time and aggregated performance metrics (`metrics.json`, `performance_metrics.json`).
  - Robust input/output validation using Pydantic and JSON schema.
- **Dockerized Deployment**: Consistent environment with volume mounts for data and logs.
- **Testing**: Unit tests for `/generate` and `/goals` endpoints with success/failure reporting.
- **Health Monitoring**: Interactive Chart.js dashboard for question counts and performance metrics.

## Project Structure

```
smart-quiz/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # API endpoint definitions
│   │   ├── middleware.py          # Middleware for metrics tracking
│   │   ├── models.py             # Pydantic models for requests/responses
│   ├── services/
│   │   ├── __init__.py
│   │   ├── question_service.py    # Business logic for question operations
│   │   ├── infra_service.py       # Health and metrics logic
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── base.py               # Base generator interface
│   │   ├── tfidfRetrieval/
│   │   │   ├── __init__.py
│   │   │   ├── tfidfGenerator.py  # TF-IDF retrieval logic
│   │   ├── templateRetrieval/
│   │   │   ├── __init__.py
│   │   │   ├── templateGenerator.py  # Template-based question generator
│   │   │   ├── questionTemplates.py  # Question template definitions
│   ├── utils/
│   │   ├── config_loader.py      # Configuration and logging setup
│   │   ├── exceptions.py         # Custom exception handlers
│   ├── templates/
│   │   ├── health_visualization.html  # Chart.js dashboard for health endpoint
│   ├── __init__.py
│   ├── questions.py              # Question loading and validation logic
│   ├── main.py                   # FastAPI app initialization
├── config.json                   # Runtime configuration
├── schema.json                   # JSON schema for validation
├── api_tokens.json               # API token for authentication
├── data/
│   ├── consolidated_questions_updated.json  # Question bank (672 questions)
├── logs/
│   ├── app.log                   # Application logs
│   ├── metrics.log               # Metrics logs
│   ├── performance.log           # Performance logs
├── Dockerfile                    # Docker build instructions
├── docker-compose.yaml           # Docker Compose configuration
├── performance_metrics.json      # Performance metrics for health dashboard
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── tests/
│   ├── test_goals.py             # Unit tests for endpoints
```

## Prerequisites

- **Docker**: Docker Desktop (Windows/Mac) or Docker (Linux).
- **Python**: 3.10+ (optional for local development).
- **Git**: For cloning the repository.
- **Host Directories**:
  - `E:/smart-quiz/data/`: Contains `consolidated_questions_updated.json`.
  - `E:/smart-quiz/logs/`: Stores `app.log`, `metrics.log`, `performance.log`.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/smart-quiz-generator.git
   cd smart-quiz-generator
   ```

2. **Create Host Directories**:
   ```bash
   mkdir -p E:/smart-quiz/data E:/smart-quiz/logs
   ```
   - Place `consolidated_questions_updated.json` in `E:/smart-quiz/data/`.
   - Ensure `config.json`, `schema.json`, `api_tokens.json`, and `performance_metrics.json` are in the project root.

3. **Build and Run with Docker**:
   ```bash
   docker-compose up --build -d
   ```
   - Access the API at `http://localhost:8000`.

4. **Run Tests**:
   ```bash
   docker-compose run --rm smartquiz-app python -m unittest tests/test_goals.py
   ```
   - Expect “Success: All tests passed!” if all tests pass.

5. **Stop the Application**:
   ```bash
   docker-compose down
   ```

## Usage

- **API Endpoints** (available at `http://localhost:8000/docs`):
  - `GET /questions`: Retrieve all 672 questions.
  - `GET /questions/{question_id}`: Fetch a specific question by ID (if implemented).
  - `POST /generate`: Generate a quiz based on `goal`, `num_questions`, and `difficulty`.
    ```json
    {
      "goal": "GATE",
      "num_questions": 5,
      "difficulty": "intermediate",
      "mode": "template"
    }
    ```
  - `POST /goals`: Manage goals with authentication.
    ```json
    {
      "goal": "New Goal",
      "action": "add",
      "api_token": "secure-token-123",
      "questions": [{...}]
    }
    ```
  - `GET /health`: Check API health; `?visualize=true` for Chart.js dashboard.
  - `GET /config`: View configuration details.
  - `GET /local-metrics`: Real-time metrics.
  - `GET /performance-metrics`: Aggregated performance metrics.

- **Logs**: Check `E:/smart-quiz/logs/` for `app.log`, `metrics.log`, and `performance.log`, rotated daily.

## Configuration

- **config.json**: Defines:
  - Data paths (`DATA_DIR: /data`, `DATASET: consolidated_questions_updated.json`).
  - Logging (`logpath: /app/logs/app.log`, daily rotation, 7-day retention).
  - Question limits (`default_num_questions: 5`, `max_questions: 10`).
  - Supported goals (`GATE`, `Amazon SDE`, `CAT`).
- **schema.json**: Validates question bank and API responses.
- **api_tokens.json**: Stores `api_token` for `/goals` authentication.
- **performance_metrics.json**: Stores metrics for health dashboard.

## Development

- **Local Development**:
  ```bash
  python -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate
  pip install -r requirements.txt
  python app/main.py
  ```

- **Testing Locally**:
  ```bash
  python -m unittest tests/test_goals.py
  ```

- **Adding Features**:
  - Enhance `tfidfGenerator.py` for improved retrieval accuracy.
  - Add templates to `questionTemplates.py` for new question types.
  - Extend `question_service.py` for additional endpoints.

## Contributing

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit changes:
   ```bash
   git commit -m 'Add YourFeature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a pull request with a detailed description.

**Guidelines**:
- Follow PEP 8 and include type hints.
- Add unit tests in `tests/`.
- Update `README.md` for new features.

## Troubleshooting

- **Log Errors**: Verify `E:/smart-quiz/logs` exists and is writable.
- **Data Issues**: Ensure `E:/smart-quiz/data/consolidated_questions_updated.json` matches `schema.json`.
- **Docker Issues**: Check logs with `docker-compose logs` or rebuild with `docker-compose build`.
- **Health Dashboard Blank**: Confirm `performance_metrics.json` exists and internet access for Chart.js CDN (`https://cdn.jsdelivr.net/npm/chart.js`).
- **API Errors**: Inspect `app.log` for details; enable debug logging by setting `"level": "DEBUG"` in `config.json`.

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Contact

For questions or feedback, contact Ravi Teja at [229x1a3363@gprec.ac.in](mailto:229x1a3363@gprec.ac.in).
