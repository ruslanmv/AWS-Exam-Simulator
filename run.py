import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.prompts import PromptTemplate
from langchain_ibm import WatsonxLLM
from dotenv import load_dotenv
from os import environ, getenv
from getpass import getpass
from pydantic import BaseModel
import os

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
    model_id="meta-llama/llama-3-70b-instruct",
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
    response = watsonx_llm.invoke(full_prompt)
    return response

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
    print("prompt:", prompt)
    explanation = qa(prompt)
    return explanation

def update_json_file(file_path):
    """Reads, processes, and updates the JSON file with explanations."""
    with open(file_path, 'r') as file:
        questions = json.load(file)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for question in questions:
            if "explanation" not in question:
                futures.append(executor.submit(process_question, question, exp=False))
            else:
                old_explanation = question["explanation"]
                futures.append(executor.submit(process_question, question, exp=True))

        for future, question in zip(as_completed(futures), questions):
            explanation = future.result()
            question["explanation"] = explanation
            print(f"Updated Explanation: {explanation}")

    # Write the updated questions back to the JSON file
    with open(file_path, 'w') as file:
        json.dump(questions, file, indent=4)

# Get the current working directory
json_file_paths = []
current_dir = os.getcwd()
directory = os.path.join(current_dir, "questions")
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith(".json"):
            json_file_paths.append(os.path.join(root, file))  # include the full path

json_file_paths=[
 'c:\\Blog\\AWS-Exam-Simulator\\questions\\GCP-ML-vA.json',
 'c:\\Blog\\AWS-Exam-Simulator\\questions\\GCP-ML-vB.json',  
 'c:\\Blog\\AWS-Exam-Simulator\\questions\\SAA-C03-v1.json',
 'c:\\Blog\\AWS-Exam-Simulator\\questions\\SAA-C03-v2.json',
 'c:\\Blog\\AWS-Exam-Simulator\\questions\\SAP-C02-v1.json',
 'c:\\Blog\\AWS-Exam-Simulator\\questions\\MLS-C01-v0624.json',
 'c:\\Blog\\AWS-Exam-Simulator\\questions\\MLS-C01-v4.json',
]

print("JSON files:", json_file_paths)

# --- Main Execution ---
for file_path in json_file_paths:
    file_name = os.path.basename(file_path)  # Extract file name with extension
    print("Working with:", file_name)
    update_json_file(file_path)
