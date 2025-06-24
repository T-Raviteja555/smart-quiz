from fastapi import FastAPI
import uvicorn
from app.api.routes import router
from app.api.middleware import track_metrics, lifespan
from app.utils.exceptions import exception_handlers

app = FastAPI(
    title="Questions API",
    description="API for retrieving GATE , CAT and Amazon SDE questions",
    version="1.0.0",
    lifespan=lifespan
)

# Register global exception handlers
for exc_type, handler in exception_handlers.items():
    app.add_exception_handler(exc_type, handler)

# Add middleware
app.middleware("http")(track_metrics)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, workers=4) 