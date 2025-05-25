from app.api.models import HealthCheckResponse, LocalMetricsResponse, PerformanceMetricsResponse
from app.questions import load_questions
from app.utils.config_loader import CONFIG
import structlog
import json
from pathlib import Path
from typing import Dict, List
import orjson

logger = structlog.get_logger(__name__)

class InfraService:
    def __init__(self):
        self.metrics_file = Path(CONFIG.get('monitoring', {}).get('metrics_file', 'metrics.json'))
        self.performance_metrics_file = Path(CONFIG.get('monitoring', {}).get('performance_metrics_file', 'performance_metrics.json'))

    def health_check(self) -> HealthCheckResponse:
        """Check the health of critical dependencies and provide question statistics."""
        try:
            details = {}
            
            # Check question bank
            try:
                questions = load_questions()
                logger.info(f"Loaded {len(questions)} questions from question bank")
                details['question_bank'] = f"Available ({len(questions)} questions)"
                
                # Compute questions by goal
                goal_counts = {}
                for q in questions:
                    goal = q.goal
                    goal_counts[goal] = goal_counts.get(goal, 0) + 1
                details['questions_by_goal'] = ", ".join(f"{goal}: {count}" for goal, count in goal_counts.items())
                
                # Compute questions by type
                type_counts = {}
                for q in questions:
                    q_type = q.type
                    type_counts[q_type] = type_counts.get(q_type, 0) + 1
                details['questions_by_type'] = ", ".join(f"{q_type}: {count}" for q_type, count in type_counts.items())
            except Exception as e:
                logger.error(f"Question bank check failed: {str(e)}")
                details['question_bank'] = "Unavailable"
                return HealthCheckResponse(status="unhealthy", details=details)
            
            # Check configuration
            try:
                if CONFIG:
                    details['configuration'] = "Loaded successfully"
                else:
                    details['configuration'] = "Failed to load"
                    logger.error("Configuration not loaded")
                    return HealthCheckResponse(status="unhealthy", details=details)
            except Exception as e:
                logger.error(f"Configuration check failed: {str(e)}")
                details['configuration'] = "Failed to load"
                return HealthCheckResponse(status="unhealthy", details=details)

            return HealthCheckResponse(status="healthy", details=details)
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return HealthCheckResponse(status="unhealthy", details={"error": str(e)})

    def get_health_chart_data(self) -> Dict:
        """Generate data for Chart.js visualizations of question counts and performance metrics."""
        try:
            chart_data = {
                "question_count_by_goal": {"labels": [], "data": []},
                "question_count_by_goal_and_type": {},
                "performance_metrics": {
                    "timestamps": [],
                    "request_count": [],
                    "throughput": [],
                    "avg_latency": [],
                    "error_rate": []
                }
            }
            
            # Question count by goal and type
            try:
                questions = load_questions()
                logger.info(f"Generating chart data for {len(questions)} questions")
                goal_counts = {}
                goal_type_counts = {}
                for q in questions:
                    goal = q.goal
                    q_type = q.type
                    # Total count per goal
                    goal_counts[goal] = goal_counts.get(goal, 0) + 1
                    # Count per goal and type
                    if goal not in goal_type_counts:
                        goal_type_counts[goal] = {"mcq": 0, "short_answer": 0}
                    if q_type in goal_type_counts[goal]:
                        goal_type_counts[goal][q_type] += 1
                
                chart_data["question_count_by_goal"]["labels"] = list(goal_counts.keys())
                chart_data["question_count_by_goal"]["data"] = list(goal_counts.values())
                chart_data["question_count_by_goal_and_type"] = {
                    goal: {
                        "labels": ["MCQ", "Short Answer"],
                        "data": [counts["mcq"], counts["short_answer"]]
                    } for goal, counts in goal_type_counts.items()
                }
            except Exception as e:
                logger.error(f"Failed to generate question chart data: {str(e)}")
                chart_data["question_count_by_goal"] = {"labels": [], "data": []}
                chart_data["question_count_by_goal_and_type"] = {}
            
            # Performance metrics
            try:
                if self.performance_metrics_file.exists():
                    with open(self.performance_metrics_file, 'r', encoding='utf-8') as f:
                        metrics = orjson.loads(f.read())
                    logger.info(f"Loaded {len(metrics)} performance metrics")
                    for metric in metrics[-10:]:  # Last 10 entries for brevity
                        chart_data["performance_metrics"]["timestamps"].append(metric["timestamp"])
                        chart_data["performance_metrics"]["request_count"].append(metric["request_count"])
                        chart_data["performance_metrics"]["throughput"].append(metric["throughput"])
                        chart_data["performance_metrics"]["avg_latency"].append(metric["avg_latency"])
                        chart_data["performance_metrics"]["error_rate"].append(metric["error_rate"])
                else:
                    logger.warning("Performance metrics file not found")
            except Exception as e:
                logger.error(f"Failed to load performance metrics: {str(e)}")
                chart_data["performance_metrics"] = {
                    "timestamps": [],
                    "request_count": [],
                    "throughput": [],
                    "avg_latency": [],
                    "error_rate": []
                }
            
            logger.info(f"Chart data generated: {json.dumps(chart_data, indent=2)}")
            return chart_data
        except Exception as e:
            logger.error(f"Failed to generate chart data: {str(e)}")
            return {
                "question_count_by_goal": {"labels": [], "data": []},
                "question_count_by_goal_and_type": {},
                "performance_metrics": {
                    "timestamps": [],
                    "request_count": [],
                    "throughput": [],
                    "avg_latency": [],
                    "error_rate": []
                }
            }

    def get_local_metrics(self) -> LocalMetricsResponse:
        """Retrieve locally collected metrics."""
        try:
            with open(self.metrics_file, 'r') as f:
                metrics = json.load(f)
            
            average_latency = {}
            for key, latencies in metrics["request_latency"].items():
                average_latency[key] = sum(latencies) / len(latencies) if latencies else 0.0
            
            return LocalMetricsResponse(
                request_count=metrics["request_count"],
                average_latency=average_latency,
                error_count=metrics["error_count"]
            )
        except Exception as e:
            logger.error(f"Failed to retrieve local metrics: {str(e)}")
            return LocalMetricsResponse(
                request_count={},
                average_latency={},
                error_count={}
            )

    def get_performance_metrics(self) -> List[PerformanceMetricsResponse]:
        """Retrieve aggregated performance metrics."""
        try:
            with open(self.performance_metrics_file, 'r') as f:
                metrics = json.load(f)
            
            return [PerformanceMetricsResponse(**metric) for metric in metrics]
        except Exception as e:
            logger.error(f"Failed to retrieve performance metrics: {str(e)}")
            return []