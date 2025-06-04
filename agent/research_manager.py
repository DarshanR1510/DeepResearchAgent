from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifier_agent import clarifier_agent, ClarificationPlan   
from summary_evaluator_agent import summary_evaluator_agent, Evaluation
import asyncio

class ResearchManager:

    async def run(self, query: str, questions: list[str], answers: list[str]):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            print("Asking clarifying questions...")
            enriched_query = f"{query}\n\nClarifying Questions:\n" + "\n".join(
                f"Q{i+1}: {q}\nA{i+1}: {a}" for i, (q, a) in enumerate(zip(questions, answers))
            )
            yield "Clarifying questions answered, query enhanced..."
            
            print("Starting research...")            
            search_plan = await self.plan_searches(enriched_query)
            yield "Searches planned, starting to search..."     
            
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, evaluating summaries..."

            final_search_results = []
            final_search_results = await self.evaluate_search_results(query, search_plan, search_results)
            yield "Summaries evaluated, writing report..."
            
            report = await self.write_report(query, final_search_results)
            yield "Report written, sending email..."
            
            await self.send_email(report)
            yield "Email sent, research complete"
            
            yield report.markdown_report
        

    async def clarify_query(self, query: str) -> ClarificationPlan:
        """ Clarify the query to understand what the user is really asking for """
        print("Clarifying query...")
        result = await Runner.run(
            clarifier_agent,
            f"Query: {query}",
        )
        print(f"Clarified query with {len(result.final_output.questions)} questions")
        return result.final_output_as(ClarificationPlan)

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query, clarifying questions and their answers: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None
        
    async def summary_evaluate(self, query: str, search_term: str, reason: str, summary: str) -> Evaluation:
        """ Evaluate the summary for the search term """
        print("Evaluating summary...")
        input = f"Query: {query}\nSearch term: {search_term}\nReason for searching: {reason}\nSummary: {summary}"
        result = await Runner.run(
            summary_evaluator_agent,
            input,
        )
        print(f"Summary evaluation complete, acceptable: {result.final_output.is_acceptable}")
        return result.final_output

    async def evaluate_search_results(self, query, search_plan, search_results):
        """Evaluate search results with retries, returning only successful results."""
        final_search_results = []
        
        for idx, item in enumerate(search_plan.searches):
            attempt = 0
            success = False
            feedback = ""
            result = search_results[idx] if idx < len(search_results) else None

            while attempt < 3 and not success:
                if attempt > 0:
                    print(f"Retrying search for '{item.query}', attempt {attempt + 1}")
                    # Provide feedback to the search agent
                    input_text = (
                        f"Search term: {item.query}\n"
                        f"Reason for searching: {item.reason}\n"
                        f"Feedback from evaluator: {feedback}"
                    )
                    try:
                        search_result = await Runner.run(search_agent, input_text)
                        result = str(search_result.final_output)
                    except Exception:
                        result = None

                if result is None:
                    print(f"Search for '{item.query}' failed, skipping evaluation")
                    attempt += 1
                    continue

                print(f"Evaluating summary for search term: {item.query} (attempt {attempt + 1})")
                
                evaluation = await self.summary_evaluate(query, item.query, item.reason, result)
                
                if evaluation.is_acceptable:
                    print(f"Summary for '{item.query}' was acceptable")
                    final_search_results.append(result)
                    success = True
                
                else:
                    print(f"Summary for '{item.query}' was not acceptable, retrying...")
                    feedback = evaluation.feedback
                    attempt += 1
                    if attempt == 3:
                        print(f"Summary for '{item.query}' failed after 3 attempts, skipping report writing")                        

        return final_search_results

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report