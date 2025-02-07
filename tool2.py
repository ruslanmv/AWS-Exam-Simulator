# tool2.py
from gradio_client import Client
import os
import json

# Function to load question sets from a directory
def load_question_sets_vce(directory='questions'):
    question_sets = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                question_sets.append(os.path.join(file)[:-5])  # remove the .json extension
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


def display_question(index, audio_enabled, selected_questions):
    """Displays the question, options, and generates audio if enabled."""
    if 0 <= index < len(selected_questions):
        question_data = selected_questions[index]
        question_text = question_data["question"]
        options = question_data["options"]
        audio_path = text_to_speech(question_text) if audio_enabled else None
        return question_text, options, audio_path
    else:
        return "Question index out of range.", [], None

def get_explanation_and_answer(index, selected_questions):
    """Retrieves the explanation and correct answer for a given question index, handling missing keys."""
    if 0 <= index < len(selected_questions):
        question_data = selected_questions[index]
        # Use get() with a default value to handle missing keys
        explanation = question_data.get("explanation", "No explanation available.")
        correct_answer = question_data.get("answer", "No answer available.") # Also handle missing answer key
        return explanation, correct_answer
    return "No explanation available.", "No answer available."

# Text-to-speech function with rate limiting, retry mechanism, and client rotation
import time
import httpx

# Text-to-speech clients
client_fast = None  # Initialize client_fast to None
client_2 = None
client_3 = None
clients = []

# Initialize client_fast with error handling
try:
    client_fast = Client("https://ruslanmv-text-to-speech-fast.hf.space/")
    clients.append(client_fast)
    print("Loaded fast TTS client (client_fast) ✔")
except ValueError as e:
    print(f"Error loading fast TTS client (client_fast): {e}")
    print("Fast Text-to-Speech will be unavailable.")
except Exception as e: # Catch other potential exceptions during client initialization
    print(f"An unexpected error occurred during fast TTS client (client_fast) initialization: {e}")
    print("Fast Text-to-Speech will be unavailable.")

# Retry logic for client_2 initialization
max_retries = 3
retry_delay = 5  # seconds
for attempt in range(max_retries):
    try:
        client_2 = Client("ruslanmv/Text-To-Speech")
        clients.append(client_2)
        print("Loaded TTS client (client_2) ✔")
        break  # If successful, break out of the retry loop
    except httpx.ReadTimeout as e:
        print(f"Attempt {attempt + 1} failed with ReadTimeout: {e}")
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("Max retries reached for TTS client (client_2). It may not be available.")
            client_2 = None # Ensure client_2 is None if all retries fail
    except ValueError as e:
        print(f"Error loading TTS client (client_2): {e}")
        client_2 = None
        break # No point retrying if it's a ValueError, break out of the loop
    except Exception as e: # Catch other potential exceptions during client initialization
        print(f"An unexpected error occurred during TTS client (client_2) initialization: {e}")
        client_2 = None # Ensure client_2 is None if initialization fails
        break # No point retrying if it's not a timeout issue, break out of the loop

# Initialize client_3 with error handling
try:
    client_3 = Client("ruslanmv/Text-to-Voice-Transformers")
    clients.append(client_3)
    print("Loaded voice transformer TTS client (client_3) ✔")
except ValueError as e:
    print(f"Error loading voice transformer TTS client (client_3): {e}")
    print("Voice Transformer Text-to-Speech (client_3) will be unavailable.")
except Exception as e: # Catch other potential exceptions during client initialization
    print(f"An unexpected error occurred during voice transformer TTS client (client_3) initialization: {e}")
    print("Voice Transformer Text-to-Speech (client_3) will be unavailable.")

if not clients:
    print("No Text-to-speech clients loaded due to errors. Audio functionality will be disabled.")
else:
    print(f"Loaded {len(clients)} TTS clients.")

# Text-to-speech function with rate limiting, retry mechanism, and client rotation
def text_to_speech(text, retries=3, delay=5):
    global clients # Ensure we are using the global clients list
    if not clients: # If no clients are loaded, return None immediately
        print("Warning: No Text-to-speech clients available.")
        return None

    client_index = 0  # Start with the first available client
    for attempt in range(retries):
        try:
            client = clients[client_index % len(clients)] # Use modulo to cycle through available clients
            client_index += 1 # Increment client_index for the next attempt in case of rate limit
            print(f"Attempt {attempt + 1} using client: {client_index % len(clients) + 1}") # Client index for logging (1-based)
            if client == client_fast: # Check if using client_fast
                result = client.predict(
                    language="English",
                    repo_id="csukuangfj/vits-piper-en_US-hfc_female-medium|1 speaker",
                    text=text,
                    sid="0",
                    speed=0.8,
                    api_name="/process"
                )
            else: # Assuming client_2 or client_3 or any other client in the future
                result = client.predict(
                    text=text,
                    api_name="/predict"
                )
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"Rate limit exceeded using client {client_index % len(clients) + 1}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise e
        except Exception as e: # Catch any other potential errors during prediction
            print(f"Error during text-to-speech prediction using client {client_index % len(clients) + 1}: {e}")
            # Consider rotating client on any error, not just rate limits, to try other clients if available
            client_index += 1 # Rotate to the next client for the next attempt
    print("Max retries exceeded for all TTS clients. Could not process the request.")
    return None