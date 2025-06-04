import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()

async def ask_clarifying_questions(topic: str):
    clarification_plan = await manager.clarify_query(topic)
    questions = clarification_plan.questions    
    questions += [""] * (3 - len(questions))
    return topic, questions[0], questions[1], questions[2]

async def run_research_with_answers(a1, a2, a3, topic, q1, q2, q3):
    """ Run the research manager with the provided answers and topic """
    answers = [a1, a2, a3]
    questions = [q1, q2, q3]
    async for chunk in manager.run(topic, questions, answers):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    # Step 1 - Topic input
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    ask_button = gr.Button("Next: Clarify", variant="primary")

    # Step 2 - Clarifying Questions (revealed later)
    with gr.Column(visible=False) as clarifier_ui:
        q1 = gr.Textbox(label="Question 1", interactive=False)
        a1 = gr.Textbox(label="Your answer to Q1")
        q2 = gr.Textbox(label="Question 2", interactive=False)
        a2 = gr.Textbox(label="Your answer to Q2")
        q3 = gr.Textbox(label="Question 3", interactive=False)
        a3 = gr.Textbox(label="Your answer to Q3")
        run_button = gr.Button("Run Deep Research", variant="primary")
        report = gr.Markdown(label="Report")

    # Step 1 action
    ask_button.click(
        fn=ask_clarifying_questions,
        inputs=query_textbox,
        outputs=[query_textbox, q1, q2, q3],
        show_progress=True,
    ).then(
        fn=lambda: gr.update(visible=True),
        inputs=[],
        outputs=[clarifier_ui]
    )

    # Step 2 action
    run_button.click(
        fn=run_research_with_answers,
        inputs=[a1, a2, a3, query_textbox, q1, q2, q3],
        outputs=report
    )

ui.launch(inbrowser=True)