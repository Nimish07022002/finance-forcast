TCS Financial Forecasting Agent (AI-First)

This project implements an AI-First financial forecasting agent using FastAPI, designed to perform multi-step analysis by leveraging Google's Gemini API with Search Grounding. The agent synthesizes quantitative data from financial reports and qualitative sentiment from earnings transcripts to generate a structured, qualitative business outlook forecast.

1. Project Overview: Architectural Approach

The architecture follows a lean LLM-as-Orchestrator pattern, prioritizing efficiency and speed by consolidating complex RAG workflows into a single, grounded API call.

Agent Chain of Thought

Request Ingestion: The FastAPI endpoint (/forecast) receives the request, including company_name (e.g., TCS) and the complex task_description.

Prompt Construction: The agent dynamically constructs a Master Prompt that defines the expert persona and embeds the analytical task, explicitly instructing the LLM to use its tools and structure the output as JSON.

Tool Orchestration (Gemini): The Gemini API is called with the Google Search Grounding tool enabled.

The LLM uses grounding to "chain" its thought: first, it resourcefully searches the web for the latest, verified quarterly financial reports and transcripts (simulating the FinancialDataExtractorTool).

It then searches for management commentary and transcripts (simulating the QualitativeAnalysisTool).

Synthesis: The LLM internally synthesizes the gathered data into the four required structured fields: trends, outlook, risks/opportunities, and a final summary forecast.

Structured Output & Grounding Extraction: The response text (pure JSON) and all associated citation metadata (groundingAttributions) are extracted and validated using Pydantic models.

Logging: The full input, structured forecast data, and all citation sources are logged to a MySQL database via the DatabaseLogger utility.

Final Response: The validated structured JSON and sources are returned to the user.

2. Agent & Tool Design

Conceptual Tools

The agent achieves the required functionality of the two conceptual tools—FinancialDataExtractorTool and QualitativeAnalysisTool—without building separate microservices for each.

Conceptual Tool

Purpose

Master Prompt Instruction

FinancialDataExtractorTool

Extract quantitative metrics (revenue, margin, TCV).

1. Financial Data Extraction & Trend Analysis: Use the latest 2-3 quarterly financial reports and public documents available on the web...

QualitativeAnalysisTool

Analyze management sentiment and forward-looking statements.

2. Qualitative Sentiment Analysis: Use the most recent earnings call transcripts or investor relations press releases...

Master Prompt Strategy

The prompt is the most critical component, serving as both the instruction manual and the schema enforcer.

System Instruction (Persona & Mandate):

"You are a senior financial analyst and AI agent specializing in technology services. Your primary function is to fulfill the user's analytical task using information found via Google Search grounding."

User Query (Task Chaining & Output Control):

Integration of all tool instructions into a three-step analytical process.
CRITICAL: YOUR FINAL RESPONSE MUST BE A SINGLE, RAW JSON OBJECT... with ONLY the following four keys...

3. Setup Instructions

Prerequisites

Python 3.10+

pip (Python package installer)

Git (for cloning the repository)

(Optional but Recommended) A local MySQL 8.0+ instance running (e.g., via XAMPP or Docker). If MySQL is not running, the application will default to console logging.

Step 1: Clone Repository and Setup Environment

git clone [YOUR_REPOSITORY_LINK]
cd tcs-forecasting-agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Step 2: Install Dependencies

pip install -r requirements.txt


Step 3: Configure Credentials

Create a file named .env in the project root directory and add your Gemini API key.

.env

# Get your key from the Google AI Studio documentation
GEMINI_API_KEY="YOUR_API_KEY_HERE" 


Step 4: Database Configuration (MySQL)

The main.py is configured with default local MySQL credentials (host: localhost, user: root, password: '').

If your MySQL setup is different, update the DB_CONFIG dictionary in main.py before running. The DatabaseLogger will automatically create the database (tcs_forecast_db) and the forecasts table upon first connection.

4. How to Run

Execute the following command to start the FastAPI service using Uvicorn:

uvicorn main:app --reload
