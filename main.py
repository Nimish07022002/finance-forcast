from fastapi import FastAPI

# Imports the router from the new 'forecaster_app' package structure
from forecaster_app.api_router import router

app = FastAPI(
    title="TCS Financial Forecasting Agent (AI-First)",
    description="A purpose-built AI agent that performs grounded financial and qualitative analysis and delivers structured JSON forecasts.",
)

# Includes all defined routes (like /forecast) from the router file
app.include_router(router, tags=["Forecast"])

# Note: The logger is initialized implicitly in db_logger.py and used in agent_service.py
