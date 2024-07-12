import streamlit as st
import os
import json
import pandas as pd
import traceback
from openai import AzureOpenAI
#from datetime import datetime
#from logger import logger


import sys
import os

#sys.path.append('/Users/shreyagajbhiye/Desktop/MyPay/HappyBug')

config_path = 'config.json'
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

azure_api_key = config['azure_api_key']
azure_api_version = config['azure_api_version']
azure_endpoint = config['azure_endpoint']
deployment_name = config['deployment_name']


client = AzureOpenAI(
    api_key=azure_api_key,  
    api_version=azure_api_version,
    azure_endpoint=azure_endpoint
)

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

    prompt_e = f"Generate {number} easy level practice questions for grade {grade} on the topic of {topic}. Provide the question with heading Q:, the answer as just the number with heading A:. Do not add other headings and do not use LaTeX or special formatting"

    text_e = generate_text(prompt_e)
    questions_e, answers_e = parse_questions_answers(text_e)

    prompt_m = f"Generate {number-1} medium level practice questions for grade {grade} on the topic of {topic}. Provide the question with heading Q:, the answer as just the number with heading A:. Do not add other headings and do not use LaTeX or special formatting"

    text_m = generate_text(prompt_m)
    questions_m, answers_m = parse_questions_answers(text_m)

    prompt_h = f"Generate {number-2} hard level practice questions for grade {grade} on the topic of {topic}. Provide the question with heading Q:, the answer as just the number with heading A:. Do not add other headings and do not use LaTeX or special formatting"

    text_h = generate_text(prompt_h)
    questions_h, answers_h = parse_questions_answers(text_h)

    return (questions_e, answers_e), (questions_m, answers_m), (questions_h, answers_h)


st.title('Quiz Generator')

grade = st.selectbox('Select Grade', list(range(1, 13)))
topic = st.text_input('Enter Topic',max_chars=20,placeholder="Addition")
number = st.slider('Number of Questions', min_value=3, max_value=10, value=5)

if st.button('Generate Quiz'):
    with st.spinner('Generating quiz...'):
        easy, medium, hard = generate_quiz(grade, topic, number)
    questions_e, answers_e = easy
    questions_m, answers_m = medium
    questions_h, answers_h = hard

    st.subheader('Easy Questions')
    for q, a in zip(questions_e, answers_e):
        st.markdown(f"Question: {q}")
        st.markdown(f"Answer: {a}")

    st.subheader('Medium Questions')
    for q, a in zip(questions_m, answers_m):
        st.markdown(f"Question: {q}")
        st.markdown(f"Answer: {a}")

    st.subheader('Hard Questions')
    for q, a in zip(questions_h, answers_h):
        st.markdown(f"Question: {q}")
        st.markdown(f"Answer: {a}")

