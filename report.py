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

def upload_and_display(file):
    if file is None:
        return "<p>No file uploaded.</p>"
    
    # The uploaded file can be provided as a file path (string) or bytes.
    # If it's a string, we assume it is the file path and open it.
    if isinstance(file, str):
        try:
            with open(file, "r", encoding="utf-8") as f:
                json_data = f.read()
        except Exception as e:
            # If opening the file fails, assume the file is raw content
            json_data = file
    elif isinstance(file, bytes):
        json_data = file.decode("utf-8")
    else:
        json_data = str(file)
    
    return generate_report(json_data)

# Build the Gradio interface
iface = gr.Interface(
    fn=upload_and_display,
    inputs=gr.File(label="Upload Exam JSON"),
    outputs=gr.HTML(label="Exam Report"),
    title="Exam Report Generator",
    description="Upload a JSON file containing exam results to generate a report."
)

iface.launch(share=True)
