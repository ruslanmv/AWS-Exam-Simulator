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

def generate_html_report(report_data):
    """Generates an HTML formatted report from the report data."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Exam Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .report-container {{ max-height: 700px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; }}
            table {{ width: 100%; margin: 20px auto; border-collapse: collapse; }}
            th, td {{ text-align: left; padding: 8px; border: 1px solid #ddd; }}
            th {{ background-color: #f0f0f0; }}
            .return-home {{ text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1 style="text-align: center;">Exam Report</h1>
        <p style="text-align: center;"><strong>Overall Score:</strong> {report_data['score']}</p>
        <div class="report-container">
        <table>
            <thead>
                <tr>
                    <th>Question</th>
                    <th>Your Answer</th>
                    <th>Correct Answer</th>
                </tr> 
            </thead>
            <tbody>
    """

    for item in report_data['questions']:
        html_content += f"""
                <tr>
                    <td>{item['question']}</td>
                    <td>{item['user_answer']}</td>
                    <td>{item['correct_answer']}</td>
                </tr> 
        """

    html_content += f"""
            </tbody>
        </table>
        </div>
        <div class="return-home">
            <button onclick="window.location.reload();">Return to Home & Start New Exam</button>
        </div>
    </body>
    </html>
    """

    return html_content


def save_report_to_pdf(report_data):
    """
    Saves the report as a PDF file and returns the file path.
    """
    pdf = PDFReport()
    pdf.add_page()

    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Overall Score: {report_data['score']}", align='C', ln=True)
    pdf.ln(10)

    for i, question_data in enumerate(report_data['questions']):
        pdf.add_question(
            index=i,
            question=question_data['question'],
            user_answer=question_data['user_answer'],
            correct_answer=question_data['correct_answer'],
            explanation=question_data['explanation'] # Keep Explanation for PDF report if needed later
        )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_file_path = temp_file.name
    pdf.output(pdf_file_path)
    temp_file.close()

    return pdf_file_path

def display_report(report_json):
    """
    Displays the exam report in a new page-like format and includes a return home button.
    """
    if report_json is None:
        return "Report data is not available.", gr.update(visible=False)
    try:
        report_data = json.loads(report_json)
    except json.JSONDecodeError:
         return "Error decoding report data.", gr.update(visible=False)  # Return an error message and hide the home button

    # Generate HTML report
    html_content = generate_html_report(report_data)

    return html_content, gr.update(visible=True) # Show home button in report page