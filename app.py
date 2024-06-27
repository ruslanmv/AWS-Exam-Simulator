'''
AWS Exam Simulator v.02
Program Developed by Ruslan Magana Vsevolovna
The purpose of this program is help to practice the questions of AWS Exams.
'''

import gradio as gr
from gradio_client import Client
import os
import re
import json

# Function to load question sets from a directory
def load_question_sets_vce(directory='questions'):
    question_sets = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                question_sets.append(os.path.join( file)[:-5])  # remove the .json extension
    return question_sets

exams = load_question_sets_vce('questions/')
print("question_sets:", exams)


def select_exam_vce(exam_name):
    file_path = os.path.join(os.getcwd(), 'questions', f'{exam_name}.json')
    try:
        with open(file_path, 'r') as f:
            questions = json.load(f)
            print(f"Loaded {len(questions)} questions")
            return questions  # Ensure the questions are returned here
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return []  # Return an empty list to indicate no questions were found


# Text-to-speech function
def text_to_speech(text):
    client = Client("ruslanmv/Text-To-Speech")
    result = client.predict(
        text=text,
        api_name="/predict"
    )
    return result  # result is already the path to the audio file

# Global variable to store selected questions
selected_questions = []

# Function to start exam
def start_exam(exam_choice, audio_enabled):
    global selected_questions
    selected_questions = select_exam_vce(exam_choice)
    question, options, audio_path = display_question(0, audio_enabled)
    return (
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False),  # Hide the audio_checkbox
        gr.update(visible=True), question, gr.update(choices=options, visible=True), gr.update(visible=True),
        gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), 0, "", audio_path
    )

# Function to display a question
def display_question(index, audio_enabled):
    if index < 0 or index >= len(selected_questions):
        return "No more questions.", [], None
    question_text_ = selected_questions[index]['question']
                 
    question_text = f"**Question {index + 1}:** {question_text_}"  # Numbering added

    choices_options = selected_questions[index]['options']
    audio_path = text_to_speech(question_text_ + " " + " ".join(choices_options)) if audio_enabled else None
    return question_text, choices_options, audio_path

# Function to check the answer
def check_answer(index, answer):
    correct_answer = selected_questions[index]['correct']
    if answer == correct_answer:
        return f"Correct! The answer is: {correct_answer}"
    else:
        return f"Incorrect. The correct answer is: {correct_answer}"

# Function to update the question
def update_question(index, audio_enabled):
    question, options, audio_path = display_question(index, audio_enabled)
    return question, gr.update(choices=options), index, audio_path

# Function to handle the answer submission
def handle_answer(index, answer, audio_enabled):
    result = check_answer(index, answer)
    audio_path = text_to_speech(result) if audio_enabled else None
    return result, audio_path

# Function to handle the next question
def handle_next(index, audio_enabled):
    new_index = min(index + 1, len(selected_questions) - 1)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled)
    return question, options, new_index, "", audio_path

# Function to handle the previous question
def handle_previous(index, audio_enabled):
    new_index = max(index - 1, 0)
    question, options, new_index, audio_path = update_question(new_index, audio_enabled)
    return question, options, new_index, "", audio_path

# Function to return to the home page
def return_home():
    return (
        gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True),
        gr.update(visible=True),  # Show the audio_checkbox
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), "", ""
    )


description_str="""Developed by Ruslan Magana, this interactive quiz platform is designed to help you prepare and assess your knowledge in a variety of exams. 
For more information about the developer, please visit [ruslanmv.com](https://ruslanmv.com/).

**Get Started with Your Quiz** 

Select an exam from the dropdown menu below and start testing your skills. You can also choose to enable audio feedback to enhance your learning experience. Simply toggle the "Enable Audio" checkbox to turn it on or off."""

with gr.Blocks() as demo:
    # Home page elements
    title = gr.Markdown(value="**AWS Exam Simulator (Quiz)**")
    description = gr.Markdown(value=description_str)
    exam_selector = gr.Dropdown(label="Select an exam", choices=exams,value='CLF-C02-v1')
    audio_checkbox = gr.Checkbox(label="Enable Audio", value=True)
    start_button = gr.Button("Start Exam")

    #Quiz elements (initially hidden)
    question_state = gr.State(0)
    question_text = gr.Markdown(visible=False, elem_id="question-text")
    choices = gr.Radio(visible=False, label="Options")
    result_text = gr.Markdown(visible=True)
    answer_button = gr.Button("Submit Answer", visible=False)
    next_button = gr.Button("Next Question", visible=False)
    prev_button = gr.Button("Previous Question", visible=False)
    home_button = gr.Button("Return to Home", visible=False)
    question_audio = gr.Audio(visible=False, label="Question Audio", autoplay=True)
    answer_audio = gr.Audio(visible=False,label="Answer Audio",autoplay=True)
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
        gr.Column([result_text, answer_audio])
    with gr.Row():
        gr.Column([prev_button], scale=1)
        gr.Column([], scale=8)
        gr.Column([next_button], scale=1)
    with gr.Row():
        gr.Column([answer_button])
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
            next_button, prev_button, home_button, question_state, result_text, question_audio
        ]
    )
    # Connect the quiz buttons to their functions
    answer_button.click(fn=handle_answer, inputs=[question_state, choices, audio_checkbox], outputs=[result_text, answer_audio])
    next_button.click(fn=handle_next, inputs=[question_state, audio_checkbox], outputs=[question_text, choices, question_state, result_text, question_audio])
    prev_button.click(fn=handle_previous, inputs=[question_state, audio_checkbox], outputs=[question_text, choices, question_state, result_text, question_audio])
    home_button.click(fn=return_home, inputs=None, outputs=[
        title, description, exam_selector, start_button,
        audio_checkbox,  # Ensure the checkbox visibility is updated
        question_text, question_text, choices, answer_button, 
        next_button, prev_button, home_button, question_state, result_text
    ])

demo.launch()
