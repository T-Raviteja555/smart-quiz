import json
import structlog
import logging
from fastapi import FastAPI, Request
from time import time
from pathlib import Path
from starlette.responses import JSONResponse
from app.utils.config_loader import CONFIG
from contextlib import asynccontextmanager
import asyncio
import numpy as np
from datetime import datetime
from filelock import FileLock

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

# Metrics file paths
METRICS_FILE = Path(CONFIG.get('monitoring', {}).get('metrics_file', 'metrics.json'))
PERFORMANCE_METRICS_FILE = Path(CONFIG.get('monitoring', {}).get('performance_metrics_file', 'performance_metrics.json'))

# Lock file paths
METRICS_LOCK = METRICS_FILE.with_suffix('.lock')
PERFORMANCE_METRICS_LOCK = PERFORMANCE_METRICS_FILE.with_suffix('.lock')

# Initialize metrics file if it doesn't exist
if not METRICS_FILE.exists():
    with FileLock(METRICS_LOCK):
        with open(METRICS_FILE, 'w') as f:
            json.dump({
                "request_count": {},
                "request_latency": {},
                "error_count": {}
            }, f, indent=2)

# Initialize performance metrics file if it doesn't exist
if not PERFORMANCE_METRICS_FILE.exists():
    with FileLock(PERFORMANCE_METRICS_LOCK):
        with open(PERFORMANCE_METRICS_FILE, 'w') as f:
            json.dump([], f, indent=2)

async def track_metrics(request: Request, call_next):
    start_time = time()
    method = request.method
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as e:
        status = 500
        logger.error("Request failed", error=str(e))
        raise

    # Update metrics in file
    try:
        with FileLock(METRICS_LOCK):
            with open(METRICS_FILE, 'r') as f:
                metrics = json.load(f)
            
            key = f"{method}:{endpoint}:{status}"
            
            # Update request count
            metrics["request_count"][key] = metrics["request_count"].get(key, 0) + 1
            
            # Update latency
            latency = time() - start_time
            metrics["request_latency"].setdefault(key, [])
            metrics["request_latency"][key].append(latency)
            
            # Update error count if applicable
            if status >= 400:
                metrics["error_count"][key] = metrics["error_count"].get(key, 0) + 1

            # Write back to file
            with open(METRICS_FILE, 'w') as f:
                json.dump(metrics, f, indent=2)
        
        # Log metrics update to metrics-specific logger
        metrics_logger = structlog.get_logger("metrics")
        metrics_logger.info(
            "Metrics updated",
            method=method,
            endpoint=endpoint,
            status=status,
            latency=latency
        )
    except Exception as e:
        logger.error("Failed to update metrics", error=str(e))

    return response

async def aggregate_performance_metrics():
    interval = CONFIG.get('monitoring', {}).get('performance_aggregation_interval', 60)  # Default: 60 seconds
    while True:
        try:
            # Read metrics with lock
            with FileLock(METRICS_LOCK):
                with open(METRICS_FILE, 'r') as f:
                    metrics = json.load(f)
            
            # Read performance metrics with lock
            with FileLock(PERFORMANCE_METRICS_LOCK):
                with open(PERFORMANCE_METRICS_FILE, 'r') as f:
                    perf_metrics = json.load(f)
            
            # Calculate performance metrics
            timestamp = datetime.utcnow().isoformat()
            request_count = sum(metrics["request_count"].values())
            error_count = sum(metrics["error_count"].values())
            latencies = []
            for latency_list in metrics["request_latency"].values():
                latencies.extend(latency_list)
            
            if not latencies:
                await asyncio.sleep(interval)
                continue
            
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = np.percentile(latencies, 95) if latencies else 0.0
            throughput = request_count / interval  # Requests per second
            error_rate = error_count / request_count if request_count > 0 else 0.0
            
            # Append to performance metrics
            perf_metrics.append({
                "timestamp": timestamp,
                "request_count": request_count,
                "throughput": throughput,
                "avg_latency": avg_latency,
                "min_latency": min_latency,
                "max_latency": max_latency,
                "p95_latency": p95_latency,
                "error_rate": error_rate
            })
            
            # Write back to performance metrics file with lock
            with FileLock(PERFORMANCE_METRICS_LOCK):
                with open(PERFORMANCE_METRICS_FILE, 'w') as f:
                    json.dump(perf_metrics, f, indent=2)
            
            # Log performance metrics
            perf_logger = structlog.get_logger("performance")
            perf_logger.info(
                "Performance metrics aggregated",
                timestamp=timestamp,
                request_count=request_count,
                throughput=throughput,
                avg_latency=avg_latency,
                min_latency=min_latency,
                max_latency=max_latency,
                p95_latency=p95_latency,
                error_rate=error_rate
            )
            
            # Reset metrics file to avoid unbounded growth
            with FileLock(METRICS_LOCK):
                with open(METRICS_FILE, 'w') as f:
                    json.dump({
                        "request_count": {},
                        "request_latency": {},
                        "error_count": {}
                    }, f, indent=2)
            
        except Exception as e:
            logger.error("Failed to aggregate performance metrics", error=str(e))
        
        await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the performance metrics aggregation task
    task = asyncio.create_task(aggregate_performance_metrics())
    try:
        yield
    finally:
        # Shutdown: Cancel the aggregation task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass