import json
from langchain.prompts import PromptTemplate
from langchain_ibm import WatsonxLLM
from dotenv import load_dotenv
from os import environ, getenv
from getpass import getpass
from pydantic import BaseModel
import datetime  # Import datetime for timestamp


# Load environment variables from .env file
load_dotenv()

# Function to set environment variables
def set_env(var: str):
    env_var = getenv(var)
    if not env_var:
        env_var = getpass(f"{var}: ")
        environ[var] = env_var
    return env_var

# Define IBM connection parameters
class IbmConnectionParams(BaseModel):
    api_key: str
    project_id: str
    url: str
    credentials: dict[str, str]

    def __init__(self, api_key: str, project_id: str, url: str) -> None:
        super().__init__(api_key=api_key, project_id=project_id, url=url, credentials={"url": url, "apikey": api_key})

# Load IBM connection parameters from environment variables
def load_connection_params() -> IbmConnectionParams:
    api_key = set_env("WATSONX_API_KEY")
    project_id = set_env("PROJECT_ID")
    url = set_env("WATSONX_URL")

    return IbmConnectionParams(api_key=api_key, project_id=project_id, url=url)

connection_params: IbmConnectionParams = load_connection_params()

# Define parameters for the model
parameters = {
    "decoding_method": "sample",
    "max_new_tokens": 300,
    "min_new_tokens": 1,
    "temperature": 0.5,
    "top_k": 50,
    "top_p": 1,
}

# Initialize the WatsonxLLM model
watsonx_llm = WatsonxLLM(
    model_id="meta-llama/llama-3-1-70b-instruct",
    apikey=connection_params.api_key,
    url=connection_params.url,
    project_id=connection_params.project_id,
    params=parameters,
)


# Define the system prompt
system_prompt = (
    "You are an expert in Cloud technologies. Your task is to provide an explanation about the "
    "correct answer and explain why the other options are incorrect. "
)

# Initialize the prompt template
prompt_template = PromptTemplate(input_variables=[], template=system_prompt)

# Combine the system prompt with the user's prompt
def create_full_prompt(user_prompt: str) -> str:
    return f"{system_prompt}\n\n{user_prompt}"

# Function to interact with the WatsonxLLM model
def qa(prompt):
    full_prompt = create_full_prompt(prompt)
    try:
        response = watsonx_llm.invoke(full_prompt)
        return response
    except Exception as e:  # Catching a broad exception for API errors
        print(f"Error during WatsonxLLM API call: {e}")
        return None  # Return None to indicate failure


def process_question(question_data, exp=False):
    """Constructs a string for LLM prompt and gets an explanation."""
    if exp:
        system = '''You are an expert in the Cloud. Your task is to give an explanation about the
    correct answer and explain why the other options are wrong. The question is the following:'''
    else:
        system = '''You are an expert in the Cloud. Your task is to give an explanation about the
    correct answer and explain why the other options are wrong.
    You will recieve additional explantion that maybe can help otherwise give your explanation.
    The question and explanation are the following:'''

    context = f"Question: {question_data['question']}\n"
    for i, option in enumerate(question_data['options']):
        context += f"{i+1}. {option}\n"
    context += f"Correct Answer: {question_data['correct']}\n\n"
    prompt = system + context
    print("prompt:",prompt)
    explanation = qa(prompt) # Call the qa function which now includes error handling
    return explanation

def update_json_file(file_path):
    """Reads, processes, and updates the JSON file with explanations."""
    attempt_data = []  # List to hold question data for the current attempt

    try: # Wrap the entire file processing in a try-except block
        with open(file_path, 'r') as file:
            questions = json.load(file)

        for i, question in enumerate(questions):
            current_question_data = question.copy() # Create a copy to store attempt data
            print(f"Processing question {i+1}/{len(questions)} in {file_path}...")

            # Check if the question already has an explanation
            if "explanation" not in question:
                explanation = process_question(question, exp=False)
                if explanation: # Only update if explanation is not None (no error)
                    print(f"New Explanation: {explanation}")
                    question["explanation"] = explanation
                else:
                    print(f"Failed to generate explanation for question {i+1}. Saving attempt...")
                    current_question_data["error"] = "Failed to generate new explanation" # Add error flag
                    attempt_data.append(current_question_data) # Save attempt data
                    save_attempt_json(file_path, questions, attempt_data) # Save attempt and continue
                    continue # Skip saving the question to the main json and proceed to next question.
            else:
                old_explanation = question["explanation"]
                explanation = process_question(question, exp=True)
                if explanation: # Only update if explanation is not None (no error)
                    print("Old Explanation:", old_explanation)
                    print("New Explanation:", explanation)
                    question["explanation"] = explanation
                else:
                    print(f"Failed to update explanation for question {i+1}. Saving attempt...")
                    current_question_data["error"] = "Failed to update explanation" # Add error flag
                    attempt_data.append(current_question_data) # Save attempt data
                    save_attempt_json(file_path, questions, attempt_data) # Save attempt and continue
                    continue # Skip saving the question to the main json and proceed to next question.


            # After processing each question, save the updated json (to save progress)
            with open(file_path, 'w') as file:
                json.dump(questions, file, indent=4)
            print(f"Progress saved to {file_path}")


    except Exception as file_error: # Catch file reading/writing errors too
        print(f"Error processing file {file_path}: {file_error}")
        save_attempt_json(file_path, questions, attempt_data, error=str(file_error)) # Save attempt with file error


def save_attempt_json(original_file_path, current_questions, attempt_data, error=None):
    """Saves the current state to an attempt JSON file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.basename(original_file_path)
    name_without_extension = os.path.splitext(base_filename)[0]
    attempt_filename = f"attempt_{name_without_extension}_{timestamp}.json"
    attempt_filepath = os.path.join(os.path.dirname(original_file_path), attempt_filename)

    data_to_save = {"questions_processed_until_error": current_questions, "attempt_data_for_failed_questions": attempt_data}
    if error:
        data_to_save["file_processing_error"] = error


    with open(attempt_filepath, 'w') as attempt_file:
        json.dump(data_to_save, attempt_file, indent=4)
    print(f"Attempt saved to {attempt_filepath}")


import os

# Get the current working directory
json_file_paths=[]
current_dir = os.getcwd()
directory = os.path.join(current_dir,"questions")
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith(".json"):
            json_file_paths.append(os.path.join(root, file))

print("JSON files:", json_file_paths)


json_file_paths=[
    'C:\\Dropbox\\23-GITHUB\\Projects\\AWS-Exam-Simulator\\questions\\MLS-C01-January.json',
    'C:\\Dropbox\\23-GITHUB\\Projects\\AWS-Exam-Simulator\\questions\\GCP-ML-vB.json',
    'C:\\Dropbox\\23-GITHUB\\Projects\\AWS-Exam-Simulator\\questions\\SAA-C03-v2.json',
    #'C:\\Dropbox\\23-GITHUB\\Projects\\AWS-Exam-Simulator\\questions\\SAP-C02-v1.json',

    'C:\\Dropbox\\23-GITHUB\\Projects\\AWS-Exam-Simulator\\questions\\AI-900-v3.json',
    #'C:\\Dropbox\\23-GITHUB\\Projects\\AWS-Exam-Simulator\\questions\\AI-102.json',
]

import os
# --- Main Execution ---
for file_path in json_file_paths:
    file_name = os.path.basename(file_path) # Extract file name with extension
    print("Working with:", file_name)
    update_json_file(file_path)

print("Finished processing all JSON files.")