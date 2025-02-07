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
    Generates a report of the exam results in a structured format.
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

    return report_data


def display_report(report_json):
    """
    Displays the exam report in a new page-like format and includes a return home button.
    Modified to display JSON. Cleaned up and removed unused HTML and PDF report generation functions.
    """
    if report_json is None:
        return "Report data is not available.", gr.update(visible=False)
    try:
        report_data = json.loads(report_json)
        print("report_data:", report_data)
    except json.JSONDecodeError:
        return "Error decoding report data.", gr.update(visible=False)

    # Format JSON data for display - Directly create formatted JSON string
    formatted_json = json.dumps(report_data, indent=4)
    return formatted_json, gr.update(visible=True) # Show home button in report page