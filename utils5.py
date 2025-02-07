# utils5.py
# utils3.py is
# utils2.py is
import json
import gradio as gr
from fpdf import FPDF
import tempfile
import os

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'AWS Exam Report', align='C', ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def add_question(self, index, question, user_answer, correct_answer, explanation):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'Question {index + 1}:', ln=True)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 10, question)
        self.ln(2)
        self.cell(0, 10, f'Your Answer: {user_answer}', ln=True)
        self.cell(0, 10, f'Correct Answer: {correct_answer}', ln=True)
        self.cell(0, 10, f'Explanation: {explanation}', ln=True) # Keep Explanation for PDF report if needed later
        self.ln(8)

def generate_exam_report(selected_questions, num_questions_to_perform):
    """
    Generates a report of the exam results in a structured JSON format.
    """
    report_data = {
        "questions": [],
        "score": ""
    }

    correct_answers = 0
    for i in range(num_questions_to_perform):
        question_data = selected_questions[i]
        question_text = question_data.get('question', 'No question text available.')
        options = question_data.get('options', [])
        user_answer = question_data.get('user_answer', 'N/A')
        correct_answer = question_data.get('correct', 'No correct answer provided.')
        explanation = question_data.get('explanation', 'No explanation available.')

        if user_answer == correct_answer:
            correct_answers += 1

        report_data["questions"].append({
            "question": question_text,
            "options": options,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "explanation": explanation
        })

    score = (correct_answers / num_questions_to_perform) * 100
    report_data["score"] = f"{score:.2f}% ({correct_answers} out of {num_questions_to_perform} correct)"

    return json.dumps(report_data) # Return JSON string directly


def generate_html_report_from_json(report_json):
    """
    Generates an HTML report from exam report JSON data.
    """
    try:
        data = json.loads(report_json)
    except json.JSONDecodeError:
        return "<p>Error: Invalid JSON data provided.</p>"

    questions = data.get("questions", [])
    score = data.get("score", "N/A")

    # Create the container for the report using an f-string
    report_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: auto;">
        <h2 style="color: #4CAF50; text-align: center;">Exam Report</h2>
        <p style="text-align: center; font-size: 18px;"><strong>Score:</strong> {score}</p>
    """

    # Loop through each question and add its details
    for q in questions:
        question = q.get("question", "")
        user_answer = q.get("user_answer", "")
        correct_answer = q.get("correct_answer", "")
        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        color = "#d4edda" if is_correct else "#f8d7da"
        icon = "✅" if is_correct else "❌"

        report_html += f"""
        <div style="border: 1px solid #ccc; padding: 15px; margin-bottom: 10px;
                        background-color: {color}; border-radius: 8px;">
            <p><strong>Question:</strong> {question}</p>
            <p><strong>Your Answer:</strong> {user_answer} {icon}</p>
            <p><strong>Correct Answer:</strong> {correct_answer}</p>
        </div>
        """

    report_html += "</div>"
    return report_html


def display_report(report_json, report_format='html'):
    """
    Displays the exam report in either JSON or HTML format.

    Parameters:
    - report_json (str): JSON string containing the report data.
    - report_format (str, optional): Format to display the report in. 
                                     Defaults to 'html'. Options: 'html', 'json'.
    """
    if report_json is None:
        return "Report data is not available.", gr.update(visible=False)

    try:
        report_data = json.loads(report_json) # Ensure it's valid JSON before proceeding
    except json.JSONDecodeError:
        return "Error decoding report data.", gr.update(visible=False)

    if report_format == 'json':
        formatted_report = json.dumps(report_data, indent=4)
        return formatted_report, gr.update(visible=True) # Show home button in report page
    elif report_format == 'html':
        html_report = generate_html_report_from_json(report_json)
        return html_report, gr.update(visible=True) # Show home button in report page
    else:
        return "Unsupported report format.", gr.update(visible=False) # Handle cases with invalid format



# such  is displayed  also this function
import json
import gradio as gr

def generate_report(json_data):
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError:
        return "<p>Error: Invalid JSON data provided.</p>"

    questions = data.get("questions", [])
    score = data.get("score", "N/A")

    # Create the container for the report using an f-string
    report_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: auto;">
        <h2 style="color: #4CAF50; text-align: center;">Exam Report</h2>
        <p style="text-align: center; font-size: 18px;"><strong>Score:</strong> {score}</p>
    """

    # Loop through each question and add its details
    for q in questions:
        question = q.get("question", "")
        user_answer = q.get("user_answer", "")
        correct_answer = q.get("correct_answer", "")
        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        color = "#d4edda" if is_correct else "#f8d7da"
        icon = "✅" if is_correct else "❌"

        report_html += f"""
        <div style="border: 1px solid #ccc; padding: 15px; margin-bottom: 10px;
                        background-color: {color}; border-radius: 8px;">
            <p><strong>Question:</strong> {question}</p>
            <p><strong>Your Answer:</strong> {user_answer} {icon}</p>
            <p><strong>Correct Answer:</strong> {correct_answer}</p>
        </div>
        """

    report_html += "</div>"
    return report_html