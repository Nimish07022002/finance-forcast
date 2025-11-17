import requests
import json
import time
from typing import Dict, Any, List
from fastapi import HTTPException

from .config import API_KEY, GEMINI_API_URL
from .models import Source
from .db_logger import DB_LOGGER  # Global logger instance


def get_forecast_from_gemini(company_name: str, task: str) -> Dict[str, Any]:
    """
    The core agent function. Simulates tool orchestration (Financial/Qualitative Analysis)
    using Gemini's Google Search grounding to generate a structured forecast.
    """

    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API_KEY is missing. Please set the GEMINI_API_KEY environment variable.",
        )

    # Use a simpler, more common name for prompt clarity
    simple_company_name = company_name.replace(" (TCS)", "")

    # 1. Master Prompt Construction
    # --- THIS GOES INTO systemInstruction FIELD ---
    system_instruction_text = (
        "You are a senior financial analyst and AI agent specializing in technology services. "
        "Your primary function is to fulfill the user's analytical task. "
        "CRITICAL RULE: You MUST use the Google Search grounding tool to find and analyze public documents. Output that is not grounded is unacceptable."
    )

    # --- THIS GOES INTO contents FIELD ---
    user_query_lines = [
        f"Perform a comprehensive financial and qualitative analysis for {simple_company_name}.",
        "Your analysis must be based **ONLY** on verifiable, CURRENT public documents found via your search tool. Specifically, find and use the latest quarterly report and earnings call transcript.",
        "Ensure the facts you state are directly linked to the search sources. Do not make statements the search tool cannot verify.",
        "1. Financial Data Extraction & Trend Analysis: Use the latest 2-3 quarterly financial reports and public documents available on the web to identify the major financial trends (revenue growth, margin changes, deal wins).",
        "2. Qualitative Sentiment Analysis: Use the most recent earnings call transcripts or investor relations press releases to summarize management's forward-looking statements, strategic focus, and any risks/opportunities.",
        f"3. Synthesis: Integrate the quantitative and qualitative findings to fulfill the specific task: '{task}'",
        "",
        # --- EXTREME PROMPT MODIFIER ---
        "ACKNOWLEDGE: You must start your response with the phrase 'Search complete and data analyzed.' followed immediately by the required JSON object.",
        (
            "CRITICAL OUTPUT FORMAT: YOUR FINAL RESPONSE MUST BE A SINGLE, RAW JSON OBJECT (no markdown, no commentary outside the JSON) "
            "with ONLY the following five keys and their corresponding string values: "
            "'key_financial_trends', 'management_stated_outlook', 'risks_and_opportunities', 'sources_list' "
            "and 'qualitative_summary_forecast'. Failure to use this format or failure to use grounding results in failure. sources_list is the list of json containing uri, title,snippet,sourceId of the sources that llm referenced during the retireval"
            """ Example of one element in the sources_list
                {
                "web": {
                "uri": "https://www.apple.com/investor/earnings-release-Q3-2024.pdf",
                "title": "Apple Reports Q3 2024 Results",
                "snippet": "Apple Inc. reported quarterly revenue of $81.8 billion, down 1% year over year...",
                "sourceId": "source_0" 
                },
                "segmentId": "0" 
            }
            """
        ),
    ]
    user_query = " ".join(user_query_lines)

    # 2. API Payload Construction (Enabling Grounding Tool)
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        # Separate the system instruction for stronger enforcement
        "systemInstruction": {"parts": [{"text": system_instruction_text}]},
        # This line is essential for enabling the search tool
        "tools": [{"google_search": {}}],
    }

    headers = {"Content-Type": "application/json"}
    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            api_call_url = f"{GEMINI_API_URL}?key={API_KEY}"
            response = requests.post(
                api_call_url, headers=headers, data=json.dumps(payload), timeout=45
            )
            import pdb

            pdb.set_trace()
            response.raise_for_status()
            result = response.json()

            candidate = result.get("candidates", [{}])[0]
            json_text = (
                candidate.get("content", {}).get("parts", [{}])[1].get("text", "")
            )

            if not json_text:
                return {
                    "forecast": "Error: AI failed to generate any text.",
                    "sources": [],
                }

            # --- START: Robust JSON Parsing Logic ---

            # Step 1: Replace non-standard characters (like non-breaking space \xa0)
            sanitized_text = json_text.replace("\xa0", " ")

            # Step 2: Ensure all content is processed to find the JSON braces
            # We don't strip aggressively here, as the content might contain the ACKNOWLEDGE phrase.

            # Step 3: Find the first '{' and the last '}' to isolate the JSON object
            start_index = sanitized_text.find("{")
            end_index = sanitized_text.rfind("}")

            if start_index != -1 and end_index != -1 and end_index > start_index:
                # Extract the pure JSON string, including the closing brace
                json_string = sanitized_text[start_index : end_index + 1]

                # Attempt to load the cleaned string
                forecast_data = json.loads(json_string)
            else:
                # If braces can't be isolated, consider it a parsing failure
                print(f"Failed to isolate JSON object. Raw LLM response:\n{json_text}")
                # Re-raise the JSONDecodeError handled below for consistent error reporting
                raise json.JSONDecodeError(
                    "Could not isolate valid JSON braces.", json_text, 0
                )

            # --- END: Robust JSON Parsing Logic ---

            sources: List[dict] = []

            # Extract Sources (This is the correct extraction method)

            for attribution in forecast_data["sources_list"]:
                web = attribution.get("web")
                if web and web.get("uri") and web.get("title"):
                    sources.append(dict(uri=web["uri"], title=web["title"]))

            # 3. Log the successful result before returning
            DB_LOGGER.log_result(
                company=company_name,
                task=task,
                output=forecast_data,
                sources=sources,
            )

            # --- Check and handle zero sources ---
            if not sources:
                # Log a strong warning if the search tool failed to return citations
                print(
                    "WARNING: Forecast generated with 0 citations (Not Grounded). Check prompt or company name."
                )

            return {
                "forecast_data": forecast_data,
                "sources": sources,
            }

        except json.JSONDecodeError:
            # This block now catches both initial syntax errors and the custom brace isolation failure
            print(f"JSONDecodeError: Raw AI Output:\n{json_text}")
            return {"forecast": "Error: AI generated invalid JSON.", "sources": []}
        except requests.exceptions.HTTPError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                time.sleep(delay)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"AI service failed after multiple retries: {e}",
                )
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                time.sleep(delay)
            else:
                raise HTTPException(
                    status_code=500, detail=f"An unexpected error occurred: {str(e)}"
                )

    return {"forecast": "Error: Max retries exceeded.", "sources": []}
