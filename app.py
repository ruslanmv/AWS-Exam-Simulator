import gradio as gr
from backend1 import *
import time
from utils import generate_exam_report, save_report_to_pdf, generate_html_report, display_report
import json

# --- Global Variables ---
selected_questions = []
exam_start_time = 0
exam_mode = "training"  # Default mode
num_questions_to_perform = 0

description_str = """Welcome to the AWS Certification Exam Simulator, powered by Ruslan Magana. This interactive platform mirrors a testing environment, providing a realistic simulation to help you prepare for your AWS certification exams.

**Key Features:**

-   **Realistic Exam Interface:** Experience a testing environment that closely resembles the actual OnVUE platform.
-   **Exam Mode:** Simulate the real exam with a timer, limited number of questions and no audio support.
-   **Audio Support:** Enhance your learning with optional audio narration for questions and answers.
-   **Detailed Explanations:** Understand the reasoning behind each answer with comprehensive explanations.
-   **Progress Tracking:** Monitor your performance and identify areas for improvement.

**Getting Started:**

1.  Select your desired AWS exam from the dropdown menu.
2.  Choose the exam mode: Training or Exam.
3.  If you choose Exam mode, set the number of questions.
4.  Choose whether to enable audio narration (Training mode only).
5.  Click "Start Exam" to begin your simulated exam experience.

For more information about the developer or to explore other projects, please visit [ruslanmv.com](https://ruslanmv.com/)."""

# --- FUNCTION DEFINITIONS ---

def start_exam(exam_choice, start_question, audio_enabled, exam_mode, num_questions):
    """Starts the exam, selects questions, and sets up the UI."""
    global selected_questions, exam_start_time, num_questions_to_perform
    selected_questions = select_exam_vce(exam_choice)
    num_questions_to_perform = num_questions if exam_mode == "exam" else len(selected_questions)

    # Reset user answers for a new exam
    for q in selected_questions:
        q['user_answer'] = None

    if start_question >= len(selected_questions):
        start_question = 0

    exam_start_time = time.time()

    question, options, audio_path = display_question(start_question, audio_enabled and exam_mode == "training")

    return (
        # Hide start screen elements
        gr.update(visible=False),  # Hide title
        gr.update(visible=False),  # Hide description
        gr.update(visible=False),  # Hide exam_selector
        gr.update(visible=False),  # Hide start_button
        gr.update(visible=False),  # Hide the audio_checkbox
        gr.update(visible=False),  # Hide start_question_slider
        gr.update(visible=False),  # Hide exam_mode_radio
        gr.update(visible=False),  # Hide num_questions_slider

        # Show quiz elements
        gr.update(visible=True),  # Show question_text
        question,  # Question to display
        gr.update(choices=options, visible=True, interactive=True),  # Update Radio choices, make visible and interactive
        gr.update(visible=True),  # Show answer_button
        gr.update(visible=True if exam_mode == 'training' or start_question < num_questions_to_perform - 1 else False),  # Show next_button
        gr.update(visible=True),  # Show prev_button
        gr.update(visible=True),  # Show home_button
        start_question, "",  # Update the question state
        audio_path if exam_mode == "training" else None,  # Provide the audio_path based on mode
        gr.update(visible=True),  # Show explain_button
        gr.update(visible=True), #result text
        None,  # None for the audio stop signal
        gr.update(visible=True if exam_mode == "exam" else False),  # Timer visibility based on mode
        exam_mode,
        gr.update(visible=True if exam_mode == 'exam' and start_question == num_questions_to_perform - 1 else False),  # Show finish button if on the last question in exam mode
        selected_questions, num_questions_to_perform
    )


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
    selected_questions[index]['user_answer'] = answer  # Store user's answer
    if answer == correct_answer:
        return f"<div class='result-text'>Correct! The answer is: {correct_answer}</div>"
    else:
        return f"<div class='result-text'>Incorrect. The correct answer is: {correct_answer}</div>"

def update_question(index, audio_enabled):
    """Updates the displayed question when the index changes."""
    question, options, audio_path = display_question(index, audio_enabled)
    return question, gr.update(choices=options, visible=True, interactive=True), index, audio_path

def handle_answer(index, answer, audio_enabled, current_audio, exam_mode):
    """Handles answer submission, provides feedback, and generates audio."""
    if answer is None:
        return "<div class='result-text'>Please select an option before submitting.</div>", None, None

    stop_audio = True if current_audio else False
    result = check_answer(index, answer)
    answer_audio_path = text_to_speech(result) if audio_enabled and exam_mode == "training" else None

    return result, answer_audio_path, stop_audio

def handle_next(index, audio_enabled, exam_mode):
    """Moves to the next question and updates the UI."""
    new_index = min(index + 1, num_questions_to_perform - 1)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled and exam_mode == "training")

    # Update finish button visibility for the last question
    show_finish = gr.update(visible=True if exam_mode == "exam" and new_index == num_questions_to_perform - 1 else False)
    show_next = gr.update(visible=False if new_index == num_questions_to_perform - 1 else True)
    show_prev = gr.update(visible=True)

    return question, options, new_index, "", audio_path, gr.update(visible=False), show_finish, show_next, show_prev


def handle_previous(index, audio_enabled, exam_mode):
    """Moves to the previous question and updates the UI."""
    new_index = max(index - 1, 0)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled and exam_mode == "training")

    # Update finish button visibility
    show_finish = gr.update(visible=True if exam_mode == "exam" and new_index == num_questions_to_perform - 1 else False)
    show_next = gr.update(visible=True)
    show_prev = gr.update(visible=True if new_index > 0 else False)

    return question, options, new_index, "", audio_path, gr.update(visible=False), show_finish, show_next, show_prev


def return_home():
    """Returns to the home screen."""
    return (
        # Show start screen elements
        gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True),
        gr.update(visible=True),  # Show the audio_checkbox
        gr.update(visible=False), gr.update(choices=[], visible=False, interactive=False), gr.update(visible=False),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 0, "", "", gr.update(visible=False),
        gr.update(visible=False),  # Hide explain button
        gr.update(visible=False),  # Hide timer
        gr.update(visible=True),  # Show exam mode
        gr.update(visible=False),  # Hide num_questions
        gr.update(visible=False) # Hide result_text
    )

def update_timer():
    """Updates the timer display every second."""
    global exam_start_time
    elapsed_time = int(time.time() - exam_start_time)
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    return f"Time: {minutes:02d}:{seconds:02d}"



def on_exam_mode_change(exam_mode):
    """Shows or hides the number of questions slider based on the exam mode."""
    if exam_mode == "exam":
        return gr.update(visible=True), gr.update(visible=False)  # Show num_questions, hide audio
    else:
        return gr.update(visible=False), gr.update(visible=True)  # Hide num_questions, show audio

def finish_exam(selected_questions, num_questions_to_perform):
    """Displays the final results using generate_exam_report and hides the quiz elements."""
    report_data = generate_exam_report(selected_questions, num_questions_to_perform)

    # Convert the report data to JSON
    report_json = json.dumps(report_data)

    # Hide quiz elements
    return (
        gr.update(visible=False),  # question_text
        gr.update(choices=[], visible=False, interactive=False),  # choices
        gr.update(visible=False),  # answer_button
        gr.update(visible=False),  # next_button
        gr.update(visible=False),  # prev_button
        gr.update(visible=False),  # explain_button
        gr.update(visible=False),  # question_audio
        gr.update(visible=False),  # answer_audio
        gr.update(visible=False),  # timer_text
        gr.update(visible=False),  # finish_button
        gr.update(visible=False),  # home_button
        gr.update(visible=False),  # explanation_text
        report_json  # Return the report data to update report_data_state
    )

# --- Gradio Interface ---
with gr.Blocks(css="style.css", title="Exam Simulator") as demo:
    # Home page elements
    title = gr.Markdown(value="**AWS Exam Simulator (Quiz)**", elem_classes="title")
    description = gr.Markdown(value=description_str, elem_classes="description")
    exam_selector = gr.Dropdown(label="Select an exam", choices=exams, value=None, elem_classes="exam_selector")
    exam_mode_radio = gr.Radio(label="Exam Mode", choices=["training", "exam"], value="training", elem_classes="exam_mode_radio")
    num_questions_slider = gr.Slider(minimum=1, maximum=50, step=1, label="Number of Questions (Exam Mode)", visible=False, elem_classes="num_questions_slider")
    audio_checkbox = gr.Checkbox(label="Enable Audio (Training Mode)", value=True, elem_classes="audio_checkbox")
    start_question_slider = gr.Slider(minimum=0, maximum=50, step=1, label="Select starting question", visible=False, elem_classes="start_question_slider")
    start_button = gr.Button("Start Exam", elem_classes="start_button")

    # Quiz elements (initially hidden)
    question_state = gr.State(0)
    exam_mode_state = gr.State("training")
    current_audio_state = gr.State(None)
    question_text = gr.Markdown(visible=False, elem_classes="question-text")
    choices = gr.Radio(label="Options", visible=False, interactive=True, elem_classes="options-list")
    result_text = gr.Markdown(visible=False, elem_classes="result-text")
    explanation_text = gr.Markdown(visible=False, elem_classes="explanation-text")
    answer_button = gr.Button("Submit Answer", visible=False, elem_classes="answer_button")
    next_button = gr.Button("Next Question", visible=False, elem_classes="next_button")
    prev_button = gr.Button("Previous Question", visible=False, elem_classes="prev_button")
    finish_button = gr.Button("Finish Exam", visible=False, elem_classes="finish_button")
    home_button = gr.Button("Return to Home", visible=False, elem_classes="home_button")
    explain_button = gr.Button("Explain", visible=False, elem_classes="explain_button")
    question_audio = gr.Audio(visible=False, label="Question Audio", autoplay=True, elem_classes="question_audio")
    answer_audio = gr.Audio(visible=False, label="Answer Audio", autoplay=True, elem_classes="answer_audio")
    timer_text = gr.Textbox(label="Timer", visible=False, elem_classes="timer_text")

    # Hidden State components to store selected_questions and num_questions_to_perform
    selected_questions_state = gr.State(value=[])
    num_questions_to_perform_state = gr.State(value=0)

    # --- Layout ---
    # Layout for the home page
    with gr.Row():
        gr.Column([title])

    with gr.Row():
        gr.Column([description])

    with gr.Row():
        gr.Column([exam_selector])

    with gr.Row():
        gr.Column([exam_mode_radio])

    with gr.Row():
        gr.Column([num_questions_slider])

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
        gr.Column([finish_button], scale=1)

    with gr.Row():
        gr.Column([answer_button, explain_button])

    with gr.Row():
        gr.Column([home_button])

    with gr.Row():
        gr.Column([timer_text])

    # --- Event Handlers ---

    # Show settings after exam selection
    def show_settings(exam_choice):
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)

    # Connect exam selection to display settings section
    exam_selector.change(fn=show_settings, inputs=[exam_selector], outputs=[exam_mode_radio, audio_checkbox, start_question_slider, start_button])

    # Connect the start button to start the exam and update hidden states
    start_button.click(
        fn=start_exam,
        inputs=[exam_selector, start_question_slider, audio_checkbox, exam_mode_radio, num_questions_slider],
        outputs=[
            title, description, exam_selector, start_button,
            audio_checkbox,  # Ensure the checkbox visibility is updated
            start_question_slider,  # Ensure the slider is hidden
            exam_mode_radio,
            num_questions_slider,
            question_text, question_text, choices, answer_button,
            next_button, prev_button, home_button, question_state, result_text, question_audio,
            explain_button, result_text, current_audio_state, timer_text, exam_mode_state, finish_button,
            selected_questions_state, num_questions_to_perform_state
        ]
    )

    # Connect the quiz buttons to their functions
    answer_button.click(fn=handle_answer, inputs=[question_state, choices, audio_checkbox, current_audio_state, exam_mode_state], outputs=[result_text, answer_audio, current_audio_state])
    next_button.click(fn=handle_next, inputs=[question_state, audio_checkbox, exam_mode_state], outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text, finish_button, next_button, prev_button])
    prev_button.click(fn=handle_previous, inputs=[question_state, audio_checkbox, exam_mode_state], outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text, finish_button, next_button, prev_button])
    explain_button.click(fn=show_explanation, inputs=[question_state], outputs=[explanation_text, result_text, explanation_text])

    report_data_state = gr.State()

    finish_button.click(
        fn=finish_exam,
        inputs=[selected_questions_state, num_questions_to_perform_state],
        outputs=[
            question_text, choices, answer_button, next_button, prev_button,
            explain_button, question_audio, answer_audio, timer_text, finish_button,
            home_button, explanation_text, report_data_state
        ]
    )

    # Attach the display_report function to report_data_state change
    demo.load(
        fn=lambda report_json: display_report(report_json) if report_json else (gr.update(value=""), gr.update(visible=False)),
        inputs=report_data_state,
        outputs=[result_text, home_button]
    )

    home_button.click(
        fn=return_home,
        inputs=None,
        outputs=[
            title, description, exam_selector, start_button,
            audio_checkbox,
            question_text, choices, answer_button,
            next_button, prev_button, home_button, question_state, result_text, explanation_text, explain_button, timer_text,
            exam_mode_radio, num_questions_slider, result_text
        ]
    )

    # Update timer periodically
    demo.load(fn=update_timer, inputs=None, outputs=timer_text, every=1)

    # Handle exam mode changes
    exam_mode_radio.change(fn=on_exam_mode_change, inputs=exam_mode_radio, outputs=[num_questions_slider, audio_checkbox])

demo.launch()