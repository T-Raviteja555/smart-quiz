import structlog
from typing import List, Dict
from app.utils.config_loader import CONFIG
from app.api.models import HealthCheckResponse, LocalMetricsResponse, PerformanceMetricsResponse
from app.questions import load_questions
from pathlib import Path
import json
import numpy as np
from fastapi import HTTPException

logger = structlog.get_logger(__name__)

class InfraService:
    def health_check(self) -> HealthCheckResponse:
        """Perform a health check on the API dependencies."""
        details = {}
        is_healthy = True

        # Check question bank
        try:
            questions_cache = load_questions()
            question_count = len(questions_cache)
            details["question_bank"] = f"Available ({question_count} questions)"

            # Count questions by goal
            questions_by_goal = {}
            for question in questions_cache:
                goal = getattr(question, 'goal', 'Unknown')
                questions_by_goal[goal] = questions_by_goal.get(goal, 0) + 1
            details["questions_by_goal"] = ", ".join(f"{goal}: {count}" for goal, count in questions_by_goal.items())

            # Count questions by type
            questions_by_type = {}
            for question in questions_cache:
                q_type = getattr(question, 'type', 'Unknown')
                questions_by_type[q_type] = questions_by_type.get(q_type, 0) + 1
            details["questions_by_type"] = ", ".join(f"{q_type}: {count}" for q_type, count in questions_by_type.items())
        except Exception as e:
            details["question_bank"] = f"Not available: {str(e)}"
            details["questions_by_goal"] = "Not available"
            details["questions_by_type"] = "Not available"
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

    def get_local_metrics(self) -> LocalMetricsResponse:
        """Retrieve local metrics from the metrics file."""
        try:
            with open(Path(CONFIG.get('monitoring', {}).get('metrics_file', 'metrics.json')), 'r') as f:
                metrics = json.load(f)
            
            # Calculate average latencies
            avg_latencies = {
                key: sum(latencies) / len(latencies) if latencies else 0.0
                for key, latencies in metrics["request_latency"].items()
            }
            
            return LocalMetricsResponse(
                request_count=metrics["request_count"],
                average_latency=avg_latencies,
                error_count=metrics["error_count"]
            )
        except Exception as e:
            logger.error("Failed to retrieve metrics", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

    def get_performance_metrics(self) -> List[PerformanceMetricsResponse]:
        """Retrieve performance metrics from the performance metrics file."""
        try:
            with open(Path(CONFIG.get('monitoring', {}).get('performance_metrics_file', 'performance_metrics.json')), 'r') as f:
                perf_metrics = json.load(f)
            return [PerformanceMetricsResponse(**metric) for metric in perf_metrics]
        except Exception as e:
            logger.error("Failed to retrieve performance metrics", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")