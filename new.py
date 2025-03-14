import streamlit as st
import re
import requests
from pymongo import MongoClient
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from openai import AzureOpenAI

# Azure and database credentials
azure_api_key = st.secrets['azure_api_key']
azure_api_version = st.secrets['azure_api_version']
azure_endpoint = st.secrets['azure_endpoint']
deployment_name = st.secrets['deployment_name']
#database_url = st.secrets['conString']
mongo_uri = st.secrets['mongo_uri']

client = MongoClient(mongo_uri)
db = client['learning_academy']
quiz_collection = db['quiz']

# client = AzureOpenAI(
#     api_key=azure_api_key,
#     api_version=azure_api_version,
#     azure_endpoint=azure_endpoint
# )


# def get_connection():
#     conn = psycopg2.connect(database_url)
#     return conn

def get_connection():
    return quiz_collection

def is_valid_email(email):
    email_regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(email_regex, email)

def get_ip_address():
    try:
        response = requests.get('https://httpbin.org/ip')
        if response.status_code == 200:
            return response.json()['origin']
        else:
            return None
    except requests.RequestException:
        return None

# def count_entries(userid):
#     conn = get_connection()
#     cur = conn.cursor()
#     query = "SELECT COUNT(*) FROM quiz WHERE userid = %s"
#     cur.execute(query, (userid,))
#     count = cur.fetchone()[0]
#     cur.close()
#     conn.close()
#     return count
def count_entries(userid):
    collection = get_connection()
    count = collection.count_documents({"userid": userid})
    return count

# def save_user_info(userid, name, phone, ip_address, user_password):
#     hashed_password = generate_password_hash(user_password, method='pbkdf2:sha256')
#     user_info_entry = {
#         'userid': userid,
#         'name': name,
#         'phone': phone,
#         'date': datetime.now(timezone.utc),
#         'ip_address': ip_address,
#         'user_password': hashed_password
#     }
#     conn = get_connection()
#     cur = conn.cursor(cursor_factory=DictCursor)
#     insert_query = """
#     INSERT INTO quiz (userid, name, phone, date, ip_address, user_password)
#     VALUES (%(userid)s, %(name)s, %(phone)s, %(date)s, %(ip_address)s, %(user_password)s)
#     """
#     cur.execute(insert_query, user_info_entry)
#     conn.commit()
#     cur.close()
#     conn.close()

def save_user_info(userid, name, phone, ip_address, user_password):
    hashed_password = generate_password_hash(user_password, method='pbkdf2:sha256')
    user_info_entry = {
        'userid': userid,
        'name': name,
        'phone': phone,
        'date': datetime.now(timezone.utc),
        'ip_address': ip_address,
        'user_password': hashed_password
    }
    collection = get_connection()
    collection.insert_one(user_info_entry)

# def get_user_name(email):
#     conn = get_connection()
#     cur = conn.cursor(cursor_factory=DictCursor)
#     query = """
#     SELECT name FROM quiz WHERE userid = %s
#     """
#     cur.execute(query, (email,))
#     user = cur.fetchone()
#     cur.close()
#     conn.close()
#     if user:
#         return user['name']
#     return None

def get_user_name(email):
    collection = get_connection()
    user = collection.find_one({"userid": email})
    return user['name'] if user else None

def verify_user(email, password):
    collection = get_connection()
    user = collection.find_one({"userid": email})
    if user and user.get('user_password'):
        return check_password_hash(user['user_password'], password)
    return False



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
st.set_page_config(page_title="My Learning Academy")

# Custom CSS styles
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #FF4B4B;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 18px;
        border: none;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        margin: 10px;
        width: 150px;
    }
    .stButton>button:hover {
        background-color: #FF7373;
        color: white;
    }
    .title {
        font-size: 48px;
        font-weight: bold;
        color: #333;
        text-align: center;
        margin-top: 50px;
        margin-bottom: 50px;
    }
    .stButton>button-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items:center;
        gap: 20px;
        width: 100%;
        margin-top: 20px;
        height: calc(100vh - 200px);
        
    }
    
    </style>
    """,
    unsafe_allow_html=True
)



img = Image.open("logo.jpg")
st.image(img, width=100)

# st.title('My Learning Academy')

st.markdown('<div class="title">My Learning Academy</div>', unsafe_allow_html=True)


if 'view' not in st.session_state:
    st.session_state.view = 'home'
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

if 'balloons_displayed' not in st.session_state:
    st.session_state.balloons_displayed = False




def go_to(view):
    st.session_state.view = view

def reset_quiz_state():
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
        st.session_state.balloons_displayed = False
        # st.session_state.view = 'home'
        # st.session_state.logged_in = False
        # st.rerun()
def reset_quiz():
    reset_quiz_state()  # Reset quiz state
    st.session_state.view = 'home'  # Go back to the home view
    st.session_state.logged_in = False


if st.session_state.view == 'home':
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    if st.button('Sign Up', key='home_signup'):
        st.session_state.view = 'signup'
    if st.button('Login', key='home_login'):
        st.session_state.view = 'login'
    st.markdown('</div>', unsafe_allow_html=True)


if st.session_state.view == 'signup':
    userid = st.text_input('**Enter your Email ID:**', max_chars=200, placeholder="Email ID", key='signup_email')
    name = st.text_input('**Enter your Full Name:**', max_chars=100, placeholder="Full Name", key='signup_name')
    phone = st.text_input('**Enter your Phone Number:**', max_chars=15, placeholder="Phone Number", key='signup_phone')
    password = st.text_input('Password', type='password', key='signup_password')
    confirm_password = st.text_input('Confirm Password', type='password', key='signup_confirm_password')
    if st.button('Sign Up', key='signup_submit'):
        if password != confirm_password:
            st.error("Passwords do not match")
        elif not is_valid_email(userid):
            st.error("Please enter a valid email address")
        elif count_entries(userid)>0:
            st.error("Email ID already exists!")
        else:
            ip_address = get_ip_address()
            save_user_info(userid, name, phone, ip_address, password)
            st.success("Account created successfully")
            st.session_state.view = 'login'  # Change view to login after successful sign-up

if st.session_state.view == 'login':
    email = st.text_input('Email', key='login_email')
    password = st.text_input('Password', type='password', key='login_password')
    if st.button('Login', key='login_submit'):
        if verify_user(email, password):
            st.success("Login successful")
            st.session_state.logged_in = True
            st.session_state.username = get_user_name(email)  # Store the username
            st.session_state.view = 'quiz'
        else:
            st.error("Invalid email or password")

if st.session_state.view == 'quiz' and st.session_state.logged_in:
    
    # st.title(f'Welcome, {st.session_state.username}')
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

    # def reset_quiz_state():
    #     st.session_state.current_level = 'easy'
    #     st.session_state.questions_asked = 0
    #     st.session_state.score = 0
    #     st.session_state.easy_questions = []
    #     st.session_state.easy_answers = []
    #     st.session_state.hard_questions = []
    #     st.session_state.hard_answers = []
    #     st.session_state.medium_questions = []
    #     st.session_state.medium_answers = []
    #     st.session_state.question = ''
    #     st.session_state.answer = ''
    #     st.session_state.topic_submitted = False
    #     st.session_state.topic = ''
    #     st.session_state.user_answer_key = ''
    #     st.session_state.feedback = None
    #     st.session_state.show_solution = False
    #     st.session_state.solution = ''
    #     st.session_state.next_question_ready = False
    #     # st.session_state.view = 'home'
    #     # st.session_state.logged_in = False
    #     # st.rerun()
    # def reset_quiz():
    #     reset_quiz_state()  # Reset quiz state
    #     st.session_state.view = 'home'  # Go back to the home view
    #     st.session_state.logged_in = False

    with input_placeholder.container():
        grade = st.selectbox('Select Grade', list(range(1, 13)), key='quiz_grade')
        topic = st.text_input('Enter Topic', max_chars=20, placeholder="Addition", key='quiz_topic')
        number = st.slider('Number of Questions', min_value=3, max_value=10, value=5, key='quiz_number')
        if st.button('Submit', key='quiz_submit') and not st.session_state.topic_submitted:
            st.session_state.topic = topic
            st.session_state.topic_submitted = True
            st.session_state.questions_asked = 0
            st.session_state.score = 0
            (easy_questions, easy_answers), (medium_questions, medium_answers), (hard_questions, hard_answers) = generate_quiz(grade, st.session_state.topic, number)
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
                if st.button('Submit Answer', key=f'submit_answer_{st.session_state.questions_asked}') and not st.session_state.next_question_ready:
                    if user_answer == st.session_state.answer:
                        st.session_state.feedback = 'success'
                        st.session_state.score += 1
                    else:
                        st.session_state.feedback = 'error'
                    st.session_state.next_question_ready = True
            if st.session_state.feedback and st.session_state.next_question_ready:
                expanded_state = st.session_state.questions_asked + 1 != number
                with st.expander("Feedback", expanded=True):
                    if st.session_state.feedback == 'success':
                        st.success("Yay!! Your answer is correct!")
                    elif st.session_state.feedback == 'error':
                        st.error("Sorry!! You missed it.")
                    if st.button("Show Solution", key=f'show_solution_{st.session_state.questions_asked}'):
                        st.session_state.show_solution = True
                        st.session_state.solution = generate_solution(st.session_state.question)
                    if st.session_state.show_solution:
                        st.markdown(f"**Solution:** {st.session_state.solution}")
                    if st.session_state.questions_asked + 1 == number:
                        if st.button("End Quiz", key='end_quiz'):
                            st.session_state.questions_asked += 1
                            st.session_state.next_question_ready = False
                            st.rerun()
                    else:
                        if st.button("Next Question!", key=f'next_question_{st.session_state.questions_asked}') and st.session_state.questions_asked <= number:
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
        if st.session_state.questions_asked >= number:
            input_placeholder.empty()
            quiz_placeholder.empty()
            with quiz_placeholder.container():
                st.markdown(f"### **Yay {st.session_state.username}!!! You have successfully completed the quiz!**")
                # st.balloons()
                score_percentage = int((st.session_state.score / number) * 100)
                st.markdown(f"### **Your Score: {st.session_state.score}/{number} ({score_percentage}%)**")
                st.progress(score_percentage / 100)
                if not st.session_state.balloons_displayed:
                    st.balloons()
                    st.session_state.balloons_displayed = True
                if st.button("Restart Quiz", key='restart_quiz'):
                    reset_quiz_state()  # Reset quiz state without logging out
                    st.session_state.view = 'quiz'  # Stay on the quiz view
                    st.session_state.balloons_displayed = False
                if st.button("Logout", key='logout_button'):
                    st.session_state.balloons_displayed = False
                    reset_quiz()  # Reset quiz state and log out

            
