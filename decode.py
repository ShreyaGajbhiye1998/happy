import streamlit as st
import os
import json
import time
from openai import AzureOpenAI
from PIL import Image

# #opening and reading the configuration file
# config_path = './config.json'
# with open(config_path, 'r') as config_file:
#     config = json.load(config_file)

# azure_api_key = config['azure_api_key']
# azure_api_version = config['azure_api_version']
# azure_endpoint = config['azure_endpoint']
# deployment_name = config['deployment_name']

azure_api_key = st.secrets['azure_api_key']
azure_api_version = st.secrets['azure_api_version']
azure_endpoint = st.secrets['azure_endpoint']
deployment_name = st.secrets['deployment_name']


client = AzureOpenAI(
    api_key=azure_api_key,  
    api_version=azure_api_version,
    azure_endpoint=azure_endpoint
)

##function to generate a response from the openai model. requesting openai to generate a response.
def generate_text(prompt):
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a math tutor."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.7
    )

    text = response.choices[0].message.content.strip()
    return text

def parse_questions_answers(text):
    questions = []
    answers = []

    parts = text.split('\n')
    for part in parts:
        if part.startswith('Q'):
            questions.append(part.split('Q:', 1)[1].strip())
        elif part.startswith('A'):
            answers.append(part.split('A:', 1)[1].strip())

    return questions, answers

def generate_quiz(grade, topic, number):
    if number < 3:
        number = 3
    elif number > 10:
        number = 10

    prompt_e = f"Generate {number} different easy level practice questions for grade {grade} on the topic of {topic}. Provide the question with heading Q:, the answer as just the number with heading A:. Do not add other headings and do not use LaTeX or special formatting"

    text_e = generate_text(prompt_e)
    questions_e, answers_e = parse_questions_answers(text_e)
    
    prompt_m = f"Generate {number-1} different medium level practice questions for grade {grade} on the topic of {topic}. Provide the question with heading Q:, the answer as just the number with heading A:. Do not add other headings and do not use LaTeX or special formatting"

    text_m = generate_text(prompt_m)
    questions_m, answers_m = parse_questions_answers(text_m)
    
    prompt_h = f"Generate {number-2} different hard level practice questions for grade {grade} on the topic of {topic}. Provide the question with heading Q:, the answer as just the number with heading A:. Do not add other headings and do not use LaTeX or special formatting"

    text_h = generate_text(prompt_h)
    questions_h, answers_h = parse_questions_answers(text_h)

    return (questions_e, answers_e), (questions_m, answers_m), (questions_h, answers_h)

def generate_solution(question):
    prompt = f"Generate a solution for the question {question}, do not give anything else or give any heading and do not use LaTeX or special formatting."

    text = generate_text(prompt)
    
    return text


# Streamlit app

st.set_page_config(
    page_title = "Happy Bug Academy"
    #page_icon = "page_icon.jpeg"
)

img=Image.open("logo.jpg")
st.image(img, width=100)

st.title('Happy Bug Academy')

##creating input containers for the end screen
input_placeholder = st.empty()
quiz_placeholder = st.empty()



if 'topic_submitted' not in st.session_state:
    st.session_state.topic_submitted = False

if 'topic' not in st.session_state:
    st.session_state.topic = ''

if 'current_level' not in st.session_state:
    st.session_state.current_level = 'easy'
if 'questions_asked' not in st.session_state:
    st.session_state.questions_asked = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'easy_questions' not in st.session_state:
    st.session_state.easy_questions = []
if 'medium_questions' not in st.session_state:
    st.session_state.medium_questions = []
if 'hard_questions' not in st.session_state:
    st.session_state.hard_questions = []   
if 'easy_answers' not in st.session_state:
    st.session_state.easy_answers = []
if 'medium_answers' not in st.session_state:
    st.session_state.medium_answers = []
if 'hard_answers' not in st.session_state:
    st.session_state.hard_answers = []
if 'question' not in st.session_state:
    st.session_state.question = ''
if 'answer' not in st.session_state:
    st.session_state.answer = ''
if 'user_answer_key' not in st.session_state:
    st.session_state.user_answer_key = ''
if 'feedback' not in st.session_state:
    st.session_state.feedback = None
if 'show_solution' not in st.session_state:
    st.session_state.show_solution = False
if 'solution' not in st.session_state:
    st.session_state.solution = '' 
if 'next_question_ready' not in st.session_state:
    st.session_state.next_question_ready = False

def reset_quiz():
    st.session_state.current_level = 'easy'
    st.session_state.questions_asked = 0
    st.session_state.score = 0
    st.session_state.easy_questions = []
    st.session_state.easy_answers = []
    st.session_state.hard_questions = []
    st.session_state.hard_answers = []
    st.session_state.medium_questions = []
    st.session_state.medium_answers = []
    st.session_state.question = ''
    st.session_state.answer = ''
    st.session_state.topic_submitted = False
    st.session_state.topic = ''
    st.session_state.user_answer_key = ''
    st.session_state.feedback = None
    st.session_state.show_solution = False
    st.session_state.solution = ''
    st.session_state.next_question_ready = False
    st.rerun()

    


with input_placeholder.container():
    grade = st.selectbox('Select Grade', list(range(1, 13)))
    topic = st.text_input('Enter Topic', max_chars=20, placeholder="Addition")
    number = st.slider('Number of Questions', min_value=3, max_value=10, value=5)
    if st.button('Submit') and not st.session_state.topic_submitted:
        st.session_state.topic = topic
        st.session_state.topic_submitted = True
        st.session_state.questions_asked = 0
        st.session_state.score = 0

        (easy_questions, easy_answers), (medium_questions, medium_answers), (hard_questions, hard_answers) = generate_quiz(grade, st.session_state.topic, number)

        # Print generated questions and answers
        # print("Easy Questions and Answers:", list(zip(easy_questions, easy_answers)))
        # print("Medium Questions and Answers:", list(zip(medium_questions, medium_answers)))
        # print("Hard Questions and Answers:", list(zip(hard_questions, hard_answers)))

        st.session_state.easy_questions = list(easy_questions)
        st.session_state.easy_answers = list(easy_answers)
        st.session_state.medium_questions = list(medium_questions)
        st.session_state.medium_answers = list(medium_answers)
        st.session_state.hard_questions = list(hard_questions)
        st.session_state.hard_answers = list(hard_answers)
    
with quiz_placeholder.container():
    if st.session_state.topic_submitted:
        if st.session_state.questions_asked < number and not st.session_state.next_question_ready:
            if st.session_state.current_level == 'easy' and st.session_state.easy_questions:
                st.session_state.question = st.session_state.easy_questions[0]
                st.session_state.answer = st.session_state.easy_answers[0]
            elif st.session_state.current_level == 'medium' and st.session_state.medium_questions:
                st.session_state.question = st.session_state.medium_questions[0]
                st.session_state.answer = st.session_state.medium_answers[0]
            elif st.session_state.current_level == 'hard' and st.session_state.hard_questions:
                st.session_state.question = st.session_state.hard_questions[0]
                st.session_state.answer = st.session_state.hard_answers[0]
            
            st.session_state.user_answer_key = f'user_answer_{st.session_state.questions_asked}'

        if st.session_state.question:
            st.markdown(f"**Current Difficulty Level:** {st.session_state.current_level.capitalize()}")
            st.markdown(f"**Question:** {st.session_state.question}")
            
            user_answer = st.text_input("Your Answer", key=st.session_state.user_answer_key)

            if st.button('Submit Answer') and not st.session_state.next_question_ready:
                if user_answer == st.session_state.answer:
                    st.session_state.feedback = 'success'
                    st.session_state.score += 1
                else:
                    st.session_state.feedback = 'error'
                st.session_state.next_question_ready = True
        

        if st.session_state.feedback and st.session_state.next_question_ready:
            expanded_state = st.session_state.questions_asked + 1 != number
            with st.expander("Feedback", expanded = True):
                if st.session_state.feedback == 'success':
                    st.success("Yay!! Your answer is correct!")
                elif st.session_state.feedback == 'error':
                    st.error("Sorry!! You missed it.")
            

                if st.button("Show Solution"):
                    st.session_state.show_solution = True
                    st.session_state.solution = generate_solution(st.session_state.question)

                if st.session_state.show_solution:
                    st.markdown(f"**Solution:** {st.session_state.solution}")
                    # print(st.session_state.solution)
                
                if st.session_state.questions_asked + 1 == number:
                    if st.button("End Quiz"):
                        st.session_state.questions_asked += 1
                        st.session_state.next_question_ready = False
                        st.rerun()
                else:
                    if st.button("Next Question!") and st.session_state.questions_asked <= number:
                        if st.session_state.feedback == 'success':
                            if st.session_state.current_level == 'easy':
                                st.session_state.easy_questions.pop(0)
                                st.session_state.easy_answers.pop(0)
                                st.session_state.current_level = 'medium'
                            elif st.session_state.current_level == 'medium':
                                st.session_state.medium_questions.pop(0)
                                st.session_state.medium_answers.pop(0)
                                st.session_state.current_level = 'hard'
                            elif st.session_state.current_level == 'hard':
                                st.session_state.hard_questions.pop(0)
                                st.session_state.hard_answers.pop(0)          
                        else:
                            st.session_state.feedback == 'error'
                            if st.session_state.current_level == 'easy':
                                st.session_state.easy_questions.pop(0)
                                st.session_state.easy_answers.pop(0)
                                st.session_state.current_level = 'easy'
                            elif st.session_state.current_level == 'medium':
                                st.session_state.medium_questions.pop(0)
                                st.session_state.medium_answers.pop(0)
                                st.session_state.current_level = 'easy'
                            elif st.session_state.current_level == 'hard':
                                st.session_state.hard_questions.pop(0)
                                st.session_state.hard_answers.pop(0)
                                st.session_state.current_level = 'medium'
                        st.session_state.feedback = None
                        st.session_state.show_solution = False
                        st.session_state.next_question_ready = False
                        st.session_state.questions_asked += 1
                        st.session_state.question = ''
                        st.session_state.answer = ''
                        st.rerun()


    if  st.session_state.questions_asked>=number:
        ###clearing the screen to show the final results only.
        input_placeholder.empty()
        quiz_placeholder.empty()
        with quiz_placeholder.container():
            st.markdown(f"### **Yay!!!You have successfully completed the quiz!**")
            st.balloons()
            score_percentage = int((st.session_state.score / number) * 100)
            #st.markdown(f"### **Your Score: {st.session_state.score}/{number}**")
            st.markdown(f"### **Your Score: {st.session_state.score}/{number} ({score_percentage}%)**")
            st.progress(score_percentage / 100)

            if st.button("Restart Quiz"):
                reset_quiz()



        
