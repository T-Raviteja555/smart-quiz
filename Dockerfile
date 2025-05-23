# Use a slim Python 3.10 base image for a smaller footprint
FROM python:3.10.14-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and configuration
COPY app/ app/
COPY config.json .
COPY data/ data/
COPY tests/ tests/
COPY logs/ logs/


# Expose port 8000 for FastAPI
EXPOSE 8000

# Default command to run the FastAPI application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]