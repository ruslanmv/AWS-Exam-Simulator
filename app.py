import gradio as gr
from backend1 import *

# Global variable
selected_questions = []

description_str = """Welcome to the AWS Certification Exam Simulator, powered by Ruslan Magana. This interactive platform mirrors a testing environment, providing a realistic simulation to help you prepare for your AWS certification exams.

**Key Features:**

-   **Realistic Exam Interface:** Experience a testing environment that closely resembles the actual OnVUE platform.
-   **Audio Support:** Enhance your learning with optional audio narration for questions and answers.
-   **Detailed Explanations:** Understand the reasoning behind each answer with comprehensive explanations.
-   **Progress Tracking:** Monitor your performance and identify areas for improvement.

**Getting Started:**

1.  Select your desired AWS exam from the dropdown menu.
2.  Choose whether to enable audio narration.
3.  Click "Start Exam" to begin your simulated exam experience.

For more information about the developer or to explore other projects, please visit [ruslanmv.com](https://ruslanmv.com/)."""

# --- FUNCTION DEFINITIONS ---

def start_exam(exam_choice, start_question, audio_enabled):
    """Starts the exam, selects questions, and sets up the UI."""
    global selected_questions
    selected_questions = select_exam_vce(exam_choice)

    if start_question >= len(selected_questions):
        start_question = 0

    question, options, audio_path = display_question(start_question, audio_enabled)

    return (
        # Hide start screen elements
        gr.update(visible=False),  # Hide title
        gr.update(visible=False),  # Hide description
        gr.update(visible=False),  # Hide exam_selector
        gr.update(visible=False),  # Hide start_button
        gr.update(visible=False),  # Hide the audio_checkbox
        gr.update(visible=False),  # Hide start_question_slider

        # Show quiz elements
        gr.update(visible=True),  # Show question_text
        question,  # Question to display
        gr.update(choices=options, visible=True, interactive=True),  # Update Radio choices, make visible and interactive
        gr.update(visible=True),  # Show answer_button
        gr.update(visible=True),  # Show next_button
        gr.update(visible=True),  # Show prev_button
        gr.update(visible=True),  # Show home_button
        start_question, "",  # Update the question state
        audio_path,  # Provide the audio_path
        gr.update(visible=True),  # Show explain_button
        gr.update(visible=True),
        None  # None for the audio stop signal
    )

def display_question_old(index, audio_enabled):
    """Displays a question with options and generates audio (if enabled)."""
    if index < 0 or index >= len(selected_questions):
        return "No more questions.", [], None

    question_text_ = selected_questions[index].get('question', 'No question text available.')
    
    # Format the question text
    question_text = f"<div class='question-text'>Question {index + 1}: {question_text_}</div>"

    choices_options = selected_questions[index].get('options', [])
    audio_path = text_to_speech(question_text_ + " " + " ".join(choices_options)) if audio_enabled else None

    return question_text, choices_options, audio_path


def display_question(index, audio_enabled):
    """Displays a question with options and generates audio (if enabled)."""
    if index < 0 or index >= len(selected_questions):
        return "No more questions.", [], None

    question_text_ = selected_questions[index].get('question', 'No question text available.')
    
    # Format the question text
    question_text = f"<div class='question-text'>Question {index + 1}: {question_text_}</div>"

    choices_options = selected_questions[index].get('options', [])

    # Instead of HTML, return choices list directly
    audio_path = text_to_speech(question_text_ + " " + " ".join(choices_options)) if audio_enabled else None

    return question_text, choices_options, audio_path  # Return choices directly for `gr.Radio`



def show_explanation(index):
    """Shows the explanation for the current question."""
    if 0 <= index < len(selected_questions):
        explanation = selected_questions[index].get('explanation', 'No explanation available for this question.')
        return (
            f"<div class='explanation-text'>{explanation}</div>",
            gr.update(visible=True),  # Show explanation_text
            gr.update(visible=True)  # Show result_text
        )
    else:
        return "No explanation available.", gr.update(visible=False), gr.update(visible=False)

def check_answer(index, answer):
    """Checks the given answer against the correct answer."""
    correct_answer = selected_questions[index].get('correct', 'No correct answer provided.')
    if answer == correct_answer:
        return f"<div class='result-text'>Correct! The answer is: {correct_answer}</div>"
    else:
        return f"<div class='result-text'>Incorrect. The correct answer is: {correct_answer}</div>"

def update_question(index, audio_enabled):
    """Updates the displayed question when the index changes."""
    question, options, audio_path = display_question(index, audio_enabled)
    return question, gr.update(choices=options, visible=True, interactive=True), index, audio_path

def handle_answer(index, answer, audio_enabled, current_audio):
    """Handles answer submission, provides feedback, and generates audio."""
    if answer is None:
        return "<div class='result-text'>Please select an option before submitting.</div>", None, None

    stop_audio = True if current_audio else False
    result = check_answer(index, answer)
    answer_audio_path = text_to_speech(result) if audio_enabled else None

    return result, answer_audio_path, stop_audio

def handle_next(index, audio_enabled):
    """Moves to the next question and updates the UI."""
    new_index = min(index + 1, len(selected_questions) - 1)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled)
    return question, options, new_index, "", audio_path, gr.update(visible=False)  # Hide explanation

def handle_previous(index, audio_enabled):
    """Moves to the previous question and updates the UI."""
    new_index = max(index - 1, 0)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled)
    return question, options, new_index, "", audio_path, gr.update(visible=False)  # Hide explanation

def return_home():
    """Returns to the home screen."""
    return (
        # Show start screen elements
        gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True),
        gr.update(visible=True),  # Show the audio_checkbox
        gr.update(visible=False), gr.update(visible=False), gr.update(choices=[], visible=False, interactive=False), gr.update(visible=False),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), "", "", gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False)  # Hide explain button
    )

# Main Gradio Interface
with gr.Blocks(css="style.css", title="Exam Simulator") as demo:
    # Home page elements
    title = gr.Markdown(value="**AWS Exam Simulator (Quiz)**", elem_classes="title")
    description = gr.Markdown(value=description_str, elem_classes="description")
    exam_selector = gr.Dropdown(label="Select an exam", choices=exams, value=None, elem_classes="exam_selector")
    audio_checkbox = gr.Checkbox(label="Enable Audio", value=True, elem_classes="audio_checkbox")
    start_question_slider = gr.Slider(minimum=0, maximum=50, step=1, label="Select starting question", visible=False, elem_classes="start_question_slider")
    start_button = gr.Button("Start Exam", elem_classes="start_button")

    # Quiz elements (initially hidden)
    question_state = gr.State(0)
    current_audio_state = gr.State(None)
    question_text = gr.Markdown(visible=False, elem_classes="question-text")
    choices = gr.Radio(label="Options", visible=False, interactive=True, elem_classes="options-list")
    result_text = gr.Markdown(visible=False, elem_classes="result-text")
    explanation_text = gr.Markdown(visible=False, elem_classes="explanation-text")
    answer_button = gr.Button("Submit Answer", visible=False, elem_classes="answer_button")
    next_button = gr.Button("Next Question", visible=False, elem_classes="next_button")
    prev_button = gr.Button("Previous Question", visible=False, elem_classes="prev_button")
    home_button = gr.Button("Return to Home", visible=False, elem_classes="home_button")
    explain_button = gr.Button("Explain", visible=False, elem_classes="explain_button")
    question_audio = gr.Audio(visible=False, label="Question Audio", autoplay=True, elem_classes="question_audio")
    answer_audio = gr.Audio(visible=False, label="Answer Audio", autoplay=True, elem_classes="answer_audio")

    # Layout for the home page
    with gr.Row():
        gr.Column([title])

    with gr.Row():
        gr.Column([description])

    with gr.Row():
        gr.Column([exam_selector])

    with gr.Row():
        gr.Column([audio_checkbox, start_question_slider])

    with gr.Row():
        gr.Column([start_button])

    # Layout for the quiz
    with gr.Row():
        gr.Column([question_text, question_audio])

    with gr.Row():
        gr.Column([choices])

    with gr.Row():
        gr.Column([result_text, explanation_text, answer_audio])

    with gr.Row():
        gr.Column([prev_button], scale=1)
        gr.Column([], scale=8)
        gr.Column([next_button], scale=1)

    with gr.Row():
        gr.Column([answer_button, explain_button])

    with gr.Row():
        gr.Column([home_button])

    # Show settings after exam selection
    def show_settings(exam_choice):
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)

    # Connect exam selection to display settings section
    exam_selector.change(fn=show_settings, inputs=[exam_selector], outputs=[audio_checkbox, start_question_slider, start_button])

    # Connect the start button to start the exam
    start_button.click(
        fn=start_exam,
        inputs=[exam_selector, start_question_slider, audio_checkbox],
        outputs=[
            title, description, exam_selector, start_button,
            audio_checkbox,  # Ensure the checkbox visibility is updated
            start_question_slider,  # Ensure the slider is hidden
            question_text, question_text, choices, answer_button,
            next_button, prev_button, home_button, question_state, result_text, question_audio,
            explain_button, result_text, current_audio_state  # Add current_audio_state to the outputs
        ]
    )


# Connect the quiz buttons to their functions
    answer_button.click(fn=handle_answer, inputs=[question_state, choices, audio_checkbox, current_audio_state], outputs=[result_text, answer_audio, current_audio_state])
    next_button.click(fn=handle_next, inputs=[question_state, audio_checkbox], outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text])
    prev_button.click(fn=handle_previous, inputs=[question_state, audio_checkbox], outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text])
    explain_button.click(fn=show_explanation, inputs=[question_state], outputs=[explanation_text, result_text, explanation_text])
    home_button.click(fn=return_home, inputs=None, outputs=[
        title, description, exam_selector, start_button,
        audio_checkbox,  # Ensure the checkbox visibility is updated
        question_text, question_text, choices, answer_button,
        next_button, prev_button, home_button, question_state, result_text, explanation_text, explain_button
    ])

demo.launch()        