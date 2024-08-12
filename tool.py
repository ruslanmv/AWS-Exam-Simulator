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