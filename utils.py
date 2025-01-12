# utils.py

def format_time(seconds):
    """Formats seconds into MM:SS format."""
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02}:{seconds:02}"



# utils.py

def generate_exam_report(selected_questions, num_questions_to_perform):
    """
    Generates a report of the exam results, including:
    - Each question
    - User's answer
    - Correct answer
    - Explanation
    - Overall score
    """
    correct_answers = 0
    report = ""

    for i in range(num_questions_to_perform):
        question_data = selected_questions[i]
        question_text = question_data.get('question', 'No question text available.')
        user_answer = question_data.get('user_answer', 'N/A')
        correct_answer = question_data.get('correct', 'No correct answer provided.')
        explanation = question_data.get('explanation', 'No explanation available for this question.')
        
        if user_answer == correct_answer:
            correct_answers += 1

        report += f"**Question {i+1}:** {question_text}\n\n"
        report += f"- **Your Answer:** {user_answer}\n"
        report += f"- **Correct Answer:** {correct_answer}\n"
        report += f"- **Explanation:** {explanation}\n\n"
        report += "---\n\n"

    score = (correct_answers / num_questions_to_perform) * 100
    report += f"**Overall Score:** {score:.2f}% ({correct_answers} out of {num_questions_to_perform} correct)\n"

    return report