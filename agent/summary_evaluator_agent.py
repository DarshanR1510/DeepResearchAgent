from pydantic import BaseModel, Field
from agents import Agent
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv

load_dotenv()

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)

INSTRUCTIONS = (
    "You are an expert evaluator tasked with assessing the quality of an agent-generated summary. "
    "You will be provided with the following information:\n"
    "- Main query\n"
    "- Search term\n"
    "- Reason for searching\n"
    "- Agent's summary\n\n"
    "Your responsibilities are:\n"
    "1. Determine if the summary accurately and sufficiently addresses the main query, considering the search term and reason for searching.\n"
    "2. Assess the clarity, relevance, and completeness of the summary.\n"
    "3. Decide if the summary meets an acceptable standard of quality (is it factually correct, concise, and useful?).\n"
    "4. Provide constructive feedback explaining your decision.\n\n"
    "Reply with whether the summary is acceptable (True/False) and include your feedback."    
)

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

summary_evaluator_agent = Agent(
    name="SummaryEvaluatorAgent",
    instructions=INSTRUCTIONS,
    model=gemini_model,
    output_type=Evaluation,
)