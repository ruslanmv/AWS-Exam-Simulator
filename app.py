'''
AWS Exam Simulator v.05
Program Developed by Ruslan Magana Vsevolovna
The purpose of this program is help to practice the questions of AWS Exams.
'''
import gradio as gr
from tool import *  # Assuming this module contains your exam data and text-to-speech functionality
from backend1 import *


# Global variable to store the currently selected set of exam questions
selected_questions = []

description_str = """Developed by Ruslan Magana, this interactive quiz platform is designed to help you prepare and assess your knowledge in a variety of exams. 
For more information about the developer, please visit [ruslanmv.com](https://ruslanmv.com/).
**Get Started with Your Quiz** 
Select an exam from the dropdown menu below and start testing your skills. You can also choose to enable audio feedback to enhance your learning experience. Simply toggle the "Enable Audio" checkbox to turn it on or off."""

# --- FUNCTION DEFINITIONS ---

def start_exam(exam_choice, audio_enabled):
    """Starts the exam by selecting questions, setting up UI."""
    global selected_questions
    selected_questions = select_exam_vce(exam_choice)
    question, options, audio_path = display_question(0, audio_enabled)
    return (
        # Hide start screen elements
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False), # Hide the audio_checkbox
        # Show quiz elements
        gr.update(visible=True), question, gr.update(choices=options, visible=True), gr.update(visible=True),
        gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), 0, "", audio_path, gr.update(visible=True),
        gr.update(visible=True), None  # None for the audio stop signal
    )

def display_question(index, audio_enabled):
    """Displays a question with options and generates audio (if enabled)."""
    if index < 0 or index >= len(selected_questions):
        return "No more questions.", [], None
    question_text_ = selected_questions[index].get('question', 'No question text available.')
    question_text = f"**Question {index + 1}:** {question_text_}"
    choices_options = selected_questions[index].get('options', [])
    audio_path = text_to_speech(question_text_ + " " + " ".join(choices_options)) if audio_enabled else None
    return question_text, choices_options, audio_path

def show_explanation(index):
    """Shows the explanation for the current question and hides previous results."""
    if 0 <= index < len(selected_questions):
        explanation = selected_questions[index].get('explanation', 'No explanation available for this question.')
        return (
            f"**Explanation:** {explanation}", 
            gr.update(visible=True),  # Show explanation_text
            gr.update(visible=True)   # Show result_text
        )
    else:
        return "No explanation available for this question.", gr.update(visible=False), gr.update(visible=False)

def check_answer(index, answer):
    """Checks the given answer against the correct answer."""
    correct_answer = selected_questions[index].get('correct', 'No correct answer provided.')
    if answer == correct_answer:
        return f"Correct! The answer is: {correct_answer}"
    else:
        return f"Incorrect. The correct answer is: {correct_answer}"

def update_question(index, audio_enabled):
    """Updates the displayed question when the index changes."""
    question, options, audio_path = display_question(index, audio_enabled)
    return question, gr.update(choices=options), index, audio_path

def handle_answer(index, answer, audio_enabled, current_audio):
    """Handles answer submission, provides feedback, and generates audio."""
    # Handle the case when no answer is selected
    if answer is None:
        return "Please select an option before submitting.", None, None
    
    # Stop the current question audio before playing the answer audio
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
        gr.update(visible=True), # Show the audio_checkbox
        # Hide quiz elements
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), "", "", gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False)  # Hide explain button
    )

with gr.Blocks() as demo:
    # Home page elements
    title = gr.Markdown(value="**AWS Exam Simulator (Quiz)**")
    description = gr.Markdown(value=description_str)
    exam_selector = gr.Dropdown(label="Select an exam", choices=exams, value='CLF-C02-v1')
    audio_checkbox = gr.Checkbox(label="Enable Audio", value=True)
    start_button = gr.Button("Start Exam")

    # Quiz elements (initially hidden)
    question_state = gr.State(0)
    current_audio_state = gr.State(None)  # State to track the current audio playing
    question_text = gr.Markdown(visible=False, elem_id="question-text")
    choices = gr.Radio(visible=False, label="Options")
    result_text = gr.Markdown(visible=True)
    explanation_text = gr.Markdown(visible=False)
    answer_button = gr.Button("Submit Answer", visible=False)
    next_button = gr.Button("Next Question", visible=False)
    prev_button = gr.Button("Previous Question", visible=False)
    home_button = gr.Button("Return to Home", visible=False)
    explain_button = gr.Button("Explain", visible=False)
    question_audio = gr.Audio(visible=False, label="Question Audio", autoplay=True)
    answer_audio = gr.Audio(visible=False, label="Answer Audio", autoplay=True)

    # Layout for the home page
    with gr.Row():
        gr.Column([title])
    with gr.Row():
        gr.Column([description])
    with gr.Row():
        gr.Column([exam_selector, audio_checkbox])
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
    
    # Connect the start button to start the exam
    start_button.click(
        fn=start_exam, 
        inputs=[exam_selector, audio_checkbox], 
        outputs=[
            title, description, exam_selector, start_button,
            audio_checkbox,  # Ensure the checkbox visibility is updated
            question_text, question_text, choices, answer_button, 
            next_button, prev_button, home_button, question_state, result_text, question_audio,
            explain_button, current_audio_state  # Add current_audio_state to the outputs
        ]
    )
    
    # Connect the quiz buttons to their functions
    answer_button.click(fn=handle_answer, inputs=[question_state, choices, audio_checkbox, current_audio_state], outputs=[result_text, answer_audio, current_audio_state])
    next_button.click(fn=handle_next, inputs=[question_state, audio_checkbox], outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text])
    prev_button.click(fn=handle_previous, inputs=[question_state, audio_checkbox], outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text])

    explain_button.click(fn=show_explanation, inputs=[question_state], outputs=[explanation_text, result_text, explanation_text])  # Output to both to toggle visibility

    home_button.click(fn=return_home, inputs=None, outputs=[
        title, description, exam_selector, start_button,
        audio_checkbox,  # Ensure the checkbox visibility is updated
        question_text, question_text, choices, answer_button, 
        next_button, prev_button, home_button, question_state, result_text, explanation_text, explain_button
    ])

demo.launch()
