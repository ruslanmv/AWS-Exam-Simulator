import gradio as gr
from gradio_client import Client
import os
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


# Text-to-speech function with rate limiting, retry mechanism, and client rotation
import time
import httpx
# Text-to-speech clients 
client_1 = Client("ruslanmv/text-to-speech-fast")
client_2 = Client("ruslanmv/Text-To-Speech")
client_3 = Client("ruslanmv/Text-to-Voice-Transformers")
clients = [client_1, client_2, client_3]
# Text-to-speech function with rate limiting, retry mechanism, and client rotation
def text_to_speech(text, retries=3, delay=5):
    client_index = 0  # Start with the first client
    for attempt in range(retries):
        try:
            client = clients[client_index]
            print(f"Attempt {attempt + 1}")
            if client_index == 0:
                result = client.predict(
                    language="English",
                    repo_id="csukuangfj/vits-piper-en_US-hfc_female-medium|1 speaker",
                    text=text,
                    sid="0",
                    speed=0.8,
                    api_name="/process"
                )
            else:
                result = client.predict(
                    text=text,
                    api_name="/predict"
                )
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                client_index = (client_index + 1) % len(clients)  # Rotate to the next client
                time.sleep(delay)
            else:
                raise e

    print("Max retries exceeded. Could not process the request.")
    return None
# Function to start exam


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
        gr.update(visible=True),  # Show result_text
        None,  # None for the audio stop signal
        gr.update(visible=True if exam_mode == "exam" else False),  # Timer visibility based on mode
        exam_mode,
        gr.update(visible=True if exam_mode == 'exam' and start_question == num_questions_to_perform - 1 else False),  # Finish button visibility
        selected_questions, num_questions_to_perform
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