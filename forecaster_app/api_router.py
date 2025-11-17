from fastapi import APIRouter, HTTPException

from .models import ForecastTask, ForecastResponse, StructuredForecast, Source
from .agent_service import get_forecast_from_gemini

router = APIRouter()


@router.post("/forecast", response_model=ForecastResponse)
async def generate_business_outlook_forecast(request: ForecastTask):
    """
    Generates a structured, qualitative business outlook forecast for the specified company
    by analyzing grounded financial data and management sentiment using an AI agent.
    """

    print(f"REQUEST RECEIVED: Company={request.company_name}")

    try:
        # Pass the request to the core agent service function
        analysis_result = get_forecast_from_gemini(
            request.company_name, request.task_description
        )

        # Handle service-level errors returned by the agent
        if "Error" in analysis_result.get("forecast", ""):
            raise HTTPException(status_code=503, detail=analysis_result["forecast"])

        # Validate forecast data and sources using Pydantic models
        forecast_data = StructuredForecast(**analysis_result["forecast_data"].pop('sources_list'))
        sources = analysis_result["sources"]

        # Return the structured response
        return ForecastResponse(forecast_data=forecast_data, sources=sources)

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"CRITICAL ERROR processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
