from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    f"You are a highly skilled research assistant tasked with understanding user queries in depth. "
    f"For each query provided, generate 3 thoughtful clarifying questions. "
    "These questions should aim to uncover the user's true intent, the specific scope of their request, "
    "and any relevant context or background information needed to provide the most accurate and helpful response. "
    "Ensure your questions are open-ended, precise, and directly related to the original query."
)


class ClarificationPlan(BaseModel):
    questions: list[str] = Field(description="A list of clarifying questions to help answer the query.")

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationPlan,
)