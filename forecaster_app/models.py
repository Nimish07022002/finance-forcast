from pydantic import BaseModel, Field
from typing import List


class ForecastTask(BaseModel):
    """Schema for the input request."""

    company_name: str = Field(
        ...,
        example="Tata Consultancy Services (TCS)",
        description="The company for which to generate the forecast.",
    )
    task_description: str = Field(
        ...,
        example="Analyze the financial reports and transcripts for the last three quarters and provide a qualitative forecast for the upcoming quarter.",
        description="The specific analytical task for the AI agent.",
    )


class Source(BaseModel):
    """Schema for a single grounding source/citation."""

    uri: str
    title: str


class StructuredForecast(BaseModel):
    """The structured JSON output expected from the LLM."""

    key_financial_trends: str = Field(
        ...,
        description="Synthesis of revenue growth, margin pressure, and other key quantitative data points.",
    )
    management_stated_outlook: str = Field(
        ...,
        description="Summary of management's forward-looking statements and sentiment from earnings transcripts.",
    )
    risks_and_opportunities: str = Field(
        ...,
        description="Analysis of significant risks (e.g., global slowdown, currency risk) and opportunities (e.g., new partnerships, specific sector growth).",
    )
    qualitative_summary_forecast: str = Field(
        ...,
        description="A final 2-3 sentence qualitative summary of the business outlook for the upcoming quarter.",
    )


class ForecastResponse(BaseModel):
    """Schema for the final API response."""

    forecast_data: StructuredForecast
    sources: List[dict]
