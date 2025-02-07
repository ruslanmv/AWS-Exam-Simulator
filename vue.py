import gradio as gr
from tool2 import *  # Assuming this module contains your exam data and text-to-speech functionality
from backend1 import *

# Global variable to store the currently selected set of exam questions
selected_questions = []

description_str = """Developed by Ruslan Magana, this interactive quiz platform is designed to help you prepare and assess your knowledge in a variety of exams. 
For more information about the developer, please visit [ruslanmv.com](https://ruslanmv.com/).

**Get Started with Your Quiz**  
Select an exam from the dropdown menu below and start testing your skills. You can also choose to enable audio feedback to enhance your learning experience. Simply toggle the "Enable Audio" checkbox to turn it on or off."""

# --- FUNCTION DEFINITIONS ---

def start_exam(exam_choice, start_question, audio_enabled):
    """Starts the exam by selecting questions and setting up UI."""
    global selected_questions
    selected_questions = select_exam_vce(exam_choice)
    
    if start_question >= len(selected_questions):
        start_question = 0  # Default to the first question if slider value exceeds available questions
    
    question, options, audio_path = display_question(start_question, audio_enabled)
    
    return (
        # Hide home screen elements
        gr.update(visible=False),  # Hide title
        gr.update(visible=False),  # Hide description
        gr.update(visible=False),  # Hide exam_selector
        gr.update(visible=False),  # Hide start_button
        gr.update(visible=False),  # Hide the audio_checkbox
        gr.update(visible=False),  # Hide start_question_slider
        # Show quiz elements
        gr.update(visible=True),   # Show question_text
        question,                  # question_text content
        gr.update(choices=options, visible=True),  # Update Radio choices
        gr.update(visible=True),   # Show answer_button
        gr.update(visible=True),   # Show next_button
        gr.update(visible=True),   # Show prev_button
        gr.update(visible=True),   # Show home_button
        start_question, "",        # Update question_state and result_text
        audio_path,                # question_audio path
        gr.update(visible=True),   # Show explain_button
        gr.update(visible=True),
        None                       # current_audio_state => None to reset
    )

def display_question(index, audio_enabled):
    """Displays a question with options and generates audio if enabled."""
    if index < 0 or index >= len(selected_questions):
        return "No more questions.", [], None
    
    question_text_ = selected_questions[index].get('question', 'No question text available.')
    question_text = f"**Question {index}:** {question_text_}"
    choices_options = selected_questions[index].get('options', [])
    audio_path = text_to_speech(question_text_ + " " + " ".join(choices_options)) if audio_enabled else None
    return question_text, choices_options, audio_path

def show_explanation(index):
    """Shows the explanation for the current question."""
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
    """Updates the displayed question when navigating."""
    question, options, audio_path = display_question(index, audio_enabled)
    return question, gr.update(choices=options), index, audio_path

def handle_answer(index, answer, audio_enabled, current_audio):
    """Handles answer submission and generates answer feedback audio if enabled."""
    if answer is None:
        return "Please select an option before submitting.", None, None
    
    # Stop previous question audio
    stop_audio = True if current_audio else False
    result = check_answer(index, answer)
    answer_audio_path = text_to_speech(result) if audio_enabled else None
    return result, answer_audio_path, stop_audio

def handle_next(index, audio_enabled):
    """Moves to the next question."""
    new_index = min(index + 1, len(selected_questions) - 1)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled)
    # Hide explanation each time we move to a new question
    return question, options, new_index, "", audio_path, gr.update(visible=False)

def handle_previous(index, audio_enabled):
    """Moves to the previous question."""
    new_index = max(index - 1, 0)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled)
    # Hide explanation each time we move to a new question
    return question, options, new_index, "", audio_path, gr.update(visible=False)

def return_home():
    """Returns to the home screen."""
    return (
        # Show start screen elements
        gr.update(visible=True),  # title
        gr.update(visible=True),  # description
        gr.update(visible=True),  # exam_selector
        gr.update(visible=True),  # start_button
        gr.update(visible=True),  # audio_checkbox
        gr.update(visible=True),  # start_question_slider
        # Hide quiz elements
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False), 0, "", gr.update(visible=False), gr.update(visible=False), None
    )

with gr.Blocks(css="style1.css") as demo:  # <--- Include your custom CSS file here
    # Home page elements
    title = gr.Markdown(value="**Exam Simulator (Quiz)**")
    description = gr.Markdown(value=description_str)
    exam_selector = gr.Dropdown(label="Select an exam", choices=exams, value=None)
    audio_checkbox = gr.Checkbox(label="Enable Audio", value=True, visible=False)
    start_question_slider = gr.Slider(minimum=0, maximum=50, step=1, label="Select starting question", visible=False)
    start_button = gr.Button("Start Exam", visible=False)

    # Quiz elements (initially hidden)
    question_state = gr.State(0)
    current_audio_state = gr.State(None)
    
    # Use elem_id to link to our CSS for vertical display 
    question_text = gr.Markdown(visible=False, elem_id="question-text")
    choices = gr.Radio(visible=False, label="Options", elem_id="choices-radio")
    
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
        # When an exam is chosen, show the audio checkbox, slider, and start button
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)

    exam_selector.change(
        fn=show_settings, 
        inputs=[exam_selector], 
        outputs=[audio_checkbox, start_question_slider, start_button]
    )

    # Connect start button -> start_exam
    start_button.click(
        fn=start_exam, 
        inputs=[exam_selector, start_question_slider, audio_checkbox], 
        outputs=[
            title, description, exam_selector, start_button,
            audio_checkbox, start_question_slider,
            question_text, question_text, choices, answer_button, 
            next_button, prev_button, home_button, question_state, result_text, question_audio,
            explain_button, result_text, current_audio_state
        ]
    )

    # Connect quiz action buttons
    answer_button.click(
        fn=handle_answer, 
        inputs=[question_state, choices, audio_checkbox, current_audio_state], 
        outputs=[result_text, answer_audio, current_audio_state]
    )

    next_button.click(
        fn=handle_next, 
        inputs=[question_state, audio_checkbox], 
        outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text]
    )

    prev_button.click(
        fn=handle_previous, 
        inputs=[question_state, audio_checkbox], 
        outputs=[question_text, choices, question_state, result_text, question_audio, explanation_text]
    )

    explain_button.click(
        fn=show_explanation, 
        inputs=[question_state], 
        outputs=[explanation_text, result_text, explanation_text]
    )

    home_button.click(
        fn=return_home,
        inputs=None,
        outputs=[
            title, description, exam_selector, start_button,
            audio_checkbox, start_question_slider,
            question_text, question_text, choices, answer_button, 
            next_button, prev_button, home_button, question_state, 
            result_text, explanation_text, explain_button, current_audio_state
        ]
    )

demo.launch()
