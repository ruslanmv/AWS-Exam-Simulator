**AWS Exam Simulator**
=========================

**Version 0.1**

Developed by Ruslan Magana Vsevolovna

**Introduction**
---------------

The AWS Exam Simulator is an interactive quiz platform designed to help you prepare and assess your knowledge in a variety of AWS exams. This program id to simulate the actual exam experience, providing you with a comprehensive assessment of your skills and knowledge in AWS services.

**Features**
------------

* Select from a range of AWS exams to practice and assess your knowledge
* Enable audio feedback to enhance your learning experience
* Interactive quiz interface with multiple-choice questions and instant feedback
* Ability to navigate through questions, review previous questions, and return to the home page

**How to Use**
--------------

1. Select an exam from the dropdown menu on the home page
2. Choose to enable or disable audio feedback
3. Click the "Start Exam" button to begin the quiz
4. Answer questions and receive instant feedback
5. Navigate through questions using the "Next Question" and "Previous Question" buttons
6. Return to the home page by clicking the "Return to Home" button

**Technical Details**
--------------------

The AWS Exam Simulator is built using the Gradio library, which provides a simple and intuitive interface for building interactive machine learning models. The program loads question sets from a directory and parses them into individual questions with options and correct answers. The text-to-speech function uses the Hugging Face API to convert text to audio.

**Code Structure**
-----------------

The code is organized into the following functions:

* `load_question_sets`: loads question sets from a directory
* `parse_questions`: parses questions from a file into individual questions with options and correct answers
* `select_exam`: selects a set of questions based on the exam choice
* `start_exam`: starts the exam and initializes the quiz interface
* `display_question`: displays a question and its options
* `check_answer`: checks the user's answer and provides feedback
* `update_question`: updates the question and its options
* `handle_answer`: handles the user's answer submission
* `handle_next`: handles the next question button click
* `handle_previous`: handles the previous question button click
* `return_home`: returns to the home page

**License**
----------

The AWS Exam Simulator is licensed under the MIT License.

**Acknowledgments**
----------------

The AWS Exam Simulator is developed by Ruslan Magana Vsevolovna. For more information about the developer, please visi[ruslanmv.com](https://ruslanmv.com/).

**Conclusion**
--------------

The AWS Exam Simulator is a valuable tool for anyone preparing for an AWS exam. Its interactive quiz interface and instant feedback provide a comprehensive assessment of your skills and knowledge in AWS services. We hope you find this program helpful in your exam preparation journey!