import streamlit as st
import sqlite3
import os
import json
from datetime import datetime
import tempfile
from PyPDF2 import PdfReader
import docx2txt
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import io
import re

# Set page config at the very top
st.set_page_config(layout="wide")

# Database setup
DATABASE = 'app.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        user_type TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        analysis_score REAL,
        metadata TEXT,
        upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_title TEXT NOT NULL,
        description TEXT NOT NULL,
        upload_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# Initialize database if it doesn't exist
if not os.path.exists(DATABASE):
    init_db()

# Custom CSS with enhanced color usage
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        :root {
            --ice-cold: #a0d2eb;
            --freeze-purple: #e5eaf5;
            --medium-purple: #d0bdf4;
            --purple-pain: #8458B3;
            --heavy-purple: #a28089;
        }
        body {
            background: linear-gradient(135deg, var(--ice-cold) 0%, var(--freeze-purple) 50%, var(--medium-purple) 100%);
        }
        .gradient-bg {
            background: linear-gradient(135deg, var(--ice-cold) 0%, var(--medium-purple) 50%, var(--purple-pain) 100%);
            border-radius: 12px;
            padding: 1rem;
        }
        .card-hover {
            transition: all 0.3s ease;
            border: 3px solid var(--medium-purple);
            background: var(--freeze-purple);
        }
        .card-hover:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(132, 88, 179, 0.3);
            border-color: var(--purple-pain);
            background: var(--ice-cold);
        }
        .fade-in {
            animation: fadeIn 0.8s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .slide-in-left {
            animation: slideInLeft 0.8s ease-out;
        }
        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-50px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .slide-in-right {
            animation: slideInRight 0.8s ease-out;
        }
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(50px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .floating {
            animation: floating 3s ease-in-out infinite;
        }
        @keyframes floating {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .progress-bar {
            transition: width 2s ease-in-out;
            background: linear-gradient(90deg, var(--ice-cold), var(--purple-pain));
            border-radius: 8px;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--purple-pain), var(--heavy-purple));
            color: white;
            transition: all 0.3s ease;
            padding: 12px 24px;
            border-radius: 10px;
            border: none;
            font-weight: 600;
        }
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(132, 88, 179, 0.4);
            background: linear-gradient(135deg, var(--heavy-purple), var(--purple-pain));
        }
        .btn-secondary {
            background: var(--ice-cold);
            color: var(--purple-pain);
            border: 3px solid var(--purple-pain);
            padding: 12px 24px;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .btn-secondary:hover {
            background: var(--purple-pain);
            color: white;
            border-color: var(--ice-cold);
            transform: translateY(-3px);
        }
        .skill-tag {
            background: linear-gradient(45deg, var(--ice-cold), var(--medium-purple));
            border: 2px solid var(--purple-pain);
            padding: 6px 12px;
            border-radius: 14px;
            display: inline-block;
            margin: 3px;
            color: var(--heavy-purple);
            font-weight: 500;
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .navbar {
            background: linear-gradient(90deg, var(--freeze-purple), var(--ice-cold));
            backdrop-filter: blur(12px);
            border-bottom: 2px solid var(--medium-purple);
            padding: 1.5rem;
            position: sticky;
            top: 0;
            z-index: 100;
            border-radius: 0 0 12px 12px;
        }
        .hero-section {
            background: linear-gradient(135deg, var(--ice-cold) 0%, var(--medium-purple) 50%, var(--purple-pain) 100%);
            min-height: 100vh;
            padding: 4rem 2rem;
            border-radius: 12px;
        }
        .feature-card {
            background: var(--freeze-purple);
            border: 3px solid var(--medium-purple);
            border-radius: 18px;
            padding: 2rem;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 25px 50px rgba(132, 88, 179, 0.3);
            background: var(--ice-cold);
            border-color: var(--purple-pain);
        }
        .score-circle {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            background: conic-gradient(var(--purple-pain) 0deg, var(--ice-cold) 360deg);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            margin: 1.5rem auto;
            border: 4px solid var(--medium-purple);
        }
        .score-inner {
            width: 100px;
            height: 100px;
            background: var(--freeze-purple);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.8rem;
            color: var(--purple-pain);
            border: 2px solid var(--heavy-purple);
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            z-index: 1000;
        }
        .modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .modal-content {
            background: var(--freeze-purple);
            border-radius: 18px;
            padding: 2.5rem;
            max-width: 550px;
            width: 95%;
            max-height: 90vh;
            overflow-y: auto;
            animation: modalSlideIn 0.3s ease-out;
            border: 3px solid var(--medium-purple);
        }
        @keyframes modalSlideIn {
            from { opacity: 0; transform: scale(0.8); }
            to { opacity: 1; transform: scale(1); }
        }
        .tab-button {
            padding: 14px 28px;
            border: 3px solid var(--medium-purple);
            background: var(--ice-cold);
            color: var(--purple-pain);
            transition: all 0.3s ease;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
        }
        .tab-button.active {
            background: var(--purple-pain);
            color: white;
            border-color: var(--ice-cold);
        }
        .dropdown {
            position: relative;
        }
        .dropdown-content {
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            background: var(--freeze-purple);
            border: 3px solid var(--medium-purple);
            border-radius: 10px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
            z-index: 100;
            min-width: 220px;
        }
        .dropdown.show .dropdown-content {
            display: block;
        }
        .table-row:nth-child(even) {
            background: var(--ice-cold);
        }
        .table-row:nth-child(odd) {
            background: var(--freeze-purple);
        }
        .table-row:hover {
            background: var(--medium-purple);
            color: var(--purple-pain);
            transition: all 0.3s ease;
        }
        .status-high {
            background: linear-gradient(45deg, var(--ice-cold), var(--purple-pain));
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 500;
        }
        .status-medium {
            background: linear-gradient(45deg, var(--medium-purple), var(--heavy-purple));
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 500;
        }
        .status-low {
            background: linear-gradient(45deg, var(--heavy-purple), var(--purple-pain));
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 500;
        }
        .hero-section {
            position: relative;
            min-height: 100vh;
            padding: 4rem 2rem;
        }
        .hero-content {
            position: relative;
            z-index: 1;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            backdrop-filter: blur(8px);
        }
        .button-group {
            margin-top: 1.5rem;
        }
        .card-hover {
            position: relative;
            width: 100%;
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, var(--purple-pain), var(--heavy-purple));
            color: white;
            border-radius: 10px;
            padding: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, var(--heavy-purple), var(--purple-pain));
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(132, 88, 179, 0.4);
        }
        .stDataFrame table {
            width: 100%;
            border-collapse: collapse;
            border: 2px solid var(--medium-purple);
            background: var(--freeze-purple);
        }
        .stDataFrame th {
            background: var(--purple-pain);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        .stDataFrame td {
            padding: 12px;
            border: 1px solid var(--medium-purple);
            color: var(--heavy-purple);
        }
        .stDataFrame tr:nth-child(even) {
            background: var(--ice-cold);
        }
        .stDataFrame tr:hover {
            background: var(--medium-purple);
            color: var(--purple-pain);
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar for navigation with navbar style
st.markdown('<div class="navbar flex justify-between items-center">', unsafe_allow_html=True)
st.sidebar.title("Resume-Match Pro")
st.sidebar.markdown('<h3 class="text-lg font-semibold" style="color: var(--purple-pain);">Navigate</h3>', unsafe_allow_html=True)

# Determine available pages based on login status
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    pages = ["Home", "Features", "How It Works", "Login", "Sign Up"]
else:
    if st.session_state.user_type == 'student':
        pages = ["Dashboard", "Profile", "Logout"]
    elif st.session_state.user_type == 'placement':
        pages = ["Placement Dashboard", "Logout"]

page = st.sidebar.radio("Go to", pages, key="sidebar_nav")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Handle Logout
if page == "Logout":
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Home Page
if page == "Home":
    st.markdown("""
        <div class="hero-section">
            <div class="hero-content">
                <h1 class="text-5xl font-bold mb-6 slide-in-left" style="color: var(--purple-pain);">Smart Resume Analysis Platform</h1>
                <p class="text-xl text-gray-700 mb-8 leading-relaxed fade-in max-w-3xl" style="color: var(--heavy-purple);">Leverage AI-powered technology to analyze resumes, match candidates with job requirements, and make data-driven hiring decisions with precision and efficiency.</p>
                <div class="button-group">
                    <button class="btn-primary fade-in mr-4">Get Started Free</button>
                    <button class="btn-secondary fade-in">Learn More</button>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Features Page
elif page == "Features":
    st.markdown('<h2 class="text-4xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Powerful Features</h2>', unsafe_allow_html=True)
    st.markdown('<p class="text-xl text-gray-600 max-w-3xl mx-auto mb-6" style="color: var(--heavy-purple);">Comprehensive tools for both job seekers and recruiters to streamline the hiring process</p>', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
            <div class="feature-card card-hover fade-in p-6">
                <div class="w-16 h-16 rounded-lg flex items-center justify-center mb-6" style="background: linear-gradient(45deg, var(--ice-cold), var(--medium-purple));">
                    <i class="fas fa-brain text-3xl" style="color: var(--purple-pain);"></i>
                </div>
                <h3 class="text-xl font-bold mb-4" style="color: var(--purple-pain);">AI-Powered Analysis</h3>
                <p class="text-gray-600" style="color: var(--heavy-purple);">Advanced algorithms analyze resumes and job descriptions to provide accurate matching scores and insights.</p>
            </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown("""
            <div class="feature-card card-hover fade-in p-6" style="animation-delay: 0.2s;">
                <div class="w-16 h-16 rounded-lg flex items-center justify-center mb-6" style="background: linear-gradient(45deg, var(--ice-cold), var(--medium-purple));">
                    <i class="fas fa-chart-bar text-3xl" style="color: var(--purple-pain);"></i>
                </div>
                <h3 class="text-xl font-bold mb-4" style="color: var(--purple-pain);">Detailed Reports</h3>
                <p class="text-gray-600" style="color: var(--heavy-purple);">Get comprehensive analysis reports with skill matching, experience evaluation, and improvement recommendations.</p>
            </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown("""
            <div class="feature-card card-hover fade-in p-6" style="animation-delay: 0.4s;">
                <div class="w-16 h-16 rounded-lg flex items-center justify-center mb-6" style="background: linear-gradient(45deg, var(--ice-cold), var(--medium-purple));">
                    <i class="fas fa-users text-3xl" style="color: var(--purple-pain);"></i>
                </div>
                <h3 class="text-xl font-bold mb-4" style="color: var(--purple-pain);">Candidate Management</h3>
                <p class="text-gray-600" style="color: var(--heavy-purple);">Efficiently manage and filter candidates based on skills, experience, and job requirements.</p>
            </div>
        """, unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
            <div class="feature-card card-hover fade-in p-6" style="animation-delay: 0.6s;">
                <div class="w-16 h-16 rounded-lg flex items-center justify-center mb-6" style="background: linear-gradient(45deg, var(--ice-cold), var(--medium-purple));">
                    <i class="fas fa-file-alt text-3xl" style="color: var(--purple-pain);"></i>
                </div>
                <h3 class="text-xl font-bold mb-4" style="color: var(--purple-pain);">Resume Parsing</h3>
                <p class="text-gray-600" style="color: var(--heavy-purple);">Automatically extract and standardize information from various resume formats for easy comparison.</p>
            </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown("""
            <div class="feature-card card-hover fade-in p-6" style="animation-delay: 0.8s;">
                <div class="w-16 h-16 rounded-lg flex items-center justify-center mb-6" style="background: linear-gradient(45deg, var(--ice-cold), var(--medium-purple));">
                    <i class="fas fa-search text-3xl" style="color: var(--purple-pain);"></i>
                </div>
                <h3 class="text-xl font-bold mb-4" style="color: var(--purple-pain);">Smart Filtering</h3>
                <p class="text-gray-600" style="color: var(--heavy-purple);">Advanced search and filtering options to quickly find the most suitable candidates for your positions.</p>
            </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown("""
            <div class="feature-card card-hover fade-in p-6" style="animation-delay: 1s;">
                <div class="w-16 h-16 rounded-lg flex items-center justify-center mb-6" style="background: linear-gradient(45deg, var(--ice-cold), var(--medium-purple));">
                    <i class="fas fa-download text-3xl" style="color: var(--purple-pain);"></i>
                </div>
                <h3 class="text-xl font-bold mb-4" style="color: var(--purple-pain);">Export & Reports</h3>
                <p class="text-gray-600" style="color: var(--heavy-purple);">Export candidate lists and detailed reports in various formats for easy sharing and documentation.</p>
            </div>
        """, unsafe_allow_html=True)

# How It Works Page
elif page == "How It Works":
    st.markdown('<h2 class="text-4xl font-bold mb-6 slide-in-left" style="color: var(--purple-pain);">How It Works</h2>', unsafe_allow_html=True)
    st.markdown('<p class="text-xl mb-8 max-w-3xl" style="color: var(--heavy-purple);">Simple, efficient process for both job seekers and recruiters</p>', unsafe_allow_html=True)
    st.markdown('<h3 class="text-2xl font-semibold mb-4 slide-in-left" style="color: var(--purple-pain);">For Job Seekers</h3>', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
            <div class="flex items-start space-x-4 fade-in">
                <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0" style="background: linear-gradient(45deg, var(--purple-pain), var(--ice-cold));">
                    <span class="text-white font-bold">1</span>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-2" style="color: var(--purple-pain);">Upload Your Resume</h4>
                    <p style="color: var(--heavy-purple);">Upload your resume in PDF, DOC, or DOCX format for analysis.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown("""
            <div class="flex items-start space-x-4 fade-in" style="animation-delay: 0.2s;">
                <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0" style="background: linear-gradient(45deg, var(--purple-pain), var(--ice-cold));">
                    <span class="text-white font-bold">2</span>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-2" style="color: var(--purple-pain);">Add Job Description</h4>
                    <p style="color: var(--heavy-purple);">Paste or upload the job description you're interested in applying for.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown("""
            <div class="flex items-start space-x-4 fade-in" style="animation-delay: 0.4s;">
                <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0" style="background: linear-gradient(45deg, var(--purple-pain), var(--ice-cold));">
                    <span class="text-white font-bold">3</span>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-2" style="color: var(--purple-pain);">Get Analysis</h4>
                    <p style="color: var(--heavy-purple);">Receive detailed analysis with match score, skills gap, and improvement recommendations.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('<h3 class="text-2xl font-semibold mb-4 slide-in-right" style="color: var(--purple-pain);">For Recruiters</h3>', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
            <div class="flex items-start space-x-4 fade-in" style="animation-delay: 0.6s;">
                <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0" style="background: linear-gradient(45deg, var(--purple-pain), var(--ice-cold));">
                    <span class="text-white font-bold">1</span>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-2" style="color: var(--purple-pain);">Upload Job Requirements</h4>
                    <p style="color: var(--heavy-purple);">Define job roles, required skills, and qualifications for your positions.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown("""
            <div class="flex items-start space-x-4 fade-in" style="animation-delay: 0.8s;">
                <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0" style="background: linear-gradient(45deg, var(--purple-pain), var(--ice-cold));">
                    <span class="text-white font-bold">2</span>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-2" style="color: var(--purple-pain);">Analyze Resumes</h4>
                    <p style="color: var(--heavy-purple);">Automatically analyze and score all candidate resumes against your requirements.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown("""
            <div class="flex items-start space-x-4 fade-in" style="animation-delay: 1s;">
                <div class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0" style="background: linear-gradient(45deg, var(--purple-pain), var(--ice-cold));">
                    <span class="text-white font-bold">3</span>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-2" style="color: var(--purple-pain);">Review Candidates</h4>
                    <p style="color: var(--heavy-purple);">Review candidate resumes and analysis results to make informed hiring decisions.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

# Login Page
elif page == "Login":
    st.markdown('<h2 class="text-4xl font-bold mb-6 slide-in-left" style="color: var(--purple-pain);">Login</h2>', unsafe_allow_html=True)
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()
        if user:
            st.session_state.logged_in = True
            st.session_state.user_type = user['user_type']
            st.session_state.user_id = user['id']
            st.session_state.user_name = user['name']
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid email or password")

# Sign Up Page
elif page == "Sign Up":
    st.markdown('<h2 class="text-4xl font-bold mb-6 slide-in-left" style="color: var(--purple-pain);">Sign Up</h2>', unsafe_allow_html=True)
    name = st.text_input("Full Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    user_type = st.selectbox("Sign Up As", ["Job Seeker", "Placement Team"])
    if st.button("Sign Up"):
        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (name, email, password, user_type) VALUES (?, ?, ?, ?)",
                (name, email, password, 'student' if user_type == "Job Seeker" else 'placement')
            )
            conn.commit()
            st.success("Signed up successfully! Please login.")
        except sqlite3.IntegrityError:
            st.error("Email already exists")
        finally:
            conn.close()

# Dashboard Page (Student Dashboard)
elif page == "Dashboard":
    st.markdown('<h2 class="text-4xl font-bold mb-6 slide-in-left" style="color: var(--purple-pain);">Student Dashboard</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--heavy-purple);">Analyze your resume and get personalized recommendations</p>', unsafe_allow_html=True)

    # File Upload
    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "doc", "docx"])
    job_desc_file = st.file_uploader("Job Description", type=["pdf", "doc", "docx", "txt"])
    job_desc_text = st.text_area("Or paste job description manually", height=200)

    if st.button("Analyze Resume"):
        if uploaded_file is not None:
            progress = st.progress(0)
            st.markdown('<p style="color: var(--purple-pain);">Initializing analysis...</p>', unsafe_allow_html=True)
            progress.progress(20)
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                def extract_text(filepath):
                    if filepath.endswith('.pdf'):
                        reader = PdfReader(filepath)
                        text = " ".join([page.extract_text() or "" for page in reader.pages])
                    else:
                        text = docx2txt.process(filepath)
                    return text.strip() if text else ""

                text = extract_text(tmp_path)
                progress.progress(40)
                jd_text = job_desc_text or "Sample job description"
                if job_desc_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(job_desc_file.name)[1]) as tmp_jd:
                        tmp_jd.write(job_desc_file.getvalue())
                        jd_text = extract_text(tmp_jd.name)
                progress.progress(60)

                score = 0.0
                matched_skills_list = []
                missing_skills = []
                experience = "Not specified"
                keywords = 0
                if text and jd_text:
                    vectorizer = TfidfVectorizer(stop_words='english')
                    X = vectorizer.fit_transform([text, jd_text])
                    from sklearn.metrics.pairwise import cosine_similarity
                    cosine_sim = cosine_similarity(X[0:1], X[1:2])[0][0]
                    score = max(0.0, cosine_sim) * 100

                    features = vectorizer.get_feature_names_out()
                    resume_tfidf = X[0].toarray()[0]
                    jd_tfidf = X[1].toarray()[0]
                    matched_skills_list = [features[i] for i in range(len(features)) if resume_tfidf[i] > 0 and jd_tfidf[i] > 0]
                    missing_skills = [features[i] for i in range(len(features)) if resume_tfidf[i] == 0 and jd_tfidf[i] > 0]

                    total_skills = len(matched_skills_list) + len(missing_skills)
                    skills_matched = f"{len(matched_skills_list)}/{total_skills}" if total_skills > 0 else "0/0"
                    keywords = (len(matched_skills_list) / total_skills * 100) if total_skills > 0 else 0

                    # Extract experience
                    experience_years = re.findall(r'(\d+)\s*(?:year|yr)s?', text.lower())
                    if experience_years:
                        total_exp = sum(int(y) for y in experience_years)
                        experience = f"{total_exp} years"

                progress.progress(80)

                conn = get_db_connection()
                conn.execute(
                    'INSERT INTO files (user_id, filename, file_type, analysis_score, metadata) VALUES (?, ?, ?, ?, ?)',
                    (st.session_state.user_id, uploaded_file.name, 'resume', score, json.dumps({'text': text[:500], 'jd_text': jd_text[:500], 'matched_skills': matched_skills_list, 'missing_skills': missing_skills}))
                )
                conn.commit()
                conn.close()
                progress.progress(100)

                os.unlink(tmp_path)
                if job_desc_file:
                    os.unlink(tmp_jd.name)

                st.session_state.score = score
                st.session_state.skills_matched = skills_matched
                st.session_state.matched_skills_list = matched_skills_list
                st.session_state.missing_skills = missing_skills
                st.session_state.experience = experience
                st.session_state.keywords = keywords
                st.success("Analysis complete!")

            except Exception as e:
                st.error(f"Error: {e}")
                if 'tmp_path' in locals():
                    os.unlink(tmp_path)
                if 'tmp_jd' in locals():
                    os.unlink(tmp_jd.name)

        else:
            st.error("Please upload a resume!")

    # Display Results
    if "score" in st.session_state:
        st.markdown('<h3 class="text-2xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Match Analysis</h3>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: var(--heavy-purple);">Overall Match Score: <span style="color: var(--purple-pain); font-weight: bold;">{st.session_state.score:.0f}%</span></p>', unsafe_allow_html=True)
        st.markdown('<h3 class="text-2xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Quick Stats</h3>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="card-hover p-4"><p style="color: var(--purple-pain);">Skills Matched: <span style="color: var(--heavy-purple);">{st.session_state.skills_matched}</span></p></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="card-hover p-4"><p style="color: var(--purple-pain);">Experience: <span style="color: var(--heavy-purple);">{st.session_state.experience}</span></p></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="card-hover p-4"><p style="color: var(--purple-pain);">Keywords: <span style="color: var(--heavy-purple);">{st.session_state.keywords:.0f}%</span></p></div>', unsafe_allow_html=True)

        st.markdown('<h3 class="text-2xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Matched Skills</h3>', unsafe_allow_html=True)
        matched_skills = ", ".join([f'<span class="skill-tag">{skill}</span>' for skill in st.session_state.matched_skills_list[:20]]) if st.session_state.matched_skills_list else "None"
        st.markdown(f'<p style="color: var(--heavy-purple);">{matched_skills}</p>', unsafe_allow_html=True)

        st.markdown('<h3 class="text-2xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Missing Skills</h3>', unsafe_allow_html=True)
        missing_skills = ", ".join([f'<span class="skill-tag">{skill}</span>' for skill in st.session_state.missing_skills[:20]]) if st.session_state.missing_skills else "None"
        st.markdown(f'<p style="color: var(--heavy-purple);">{missing_skills}</p>', unsafe_allow_html=True)

        st.markdown('<h3 class="text-2xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Experience Match</h3>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: var(--heavy-purple);">{st.session_state.experience}</p>', unsafe_allow_html=True)
        st.markdown('<h3 class="text-2xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Recommendations for Improvement</h3>', unsafe_allow_html=True)
        recommendations = ", ".join([f'<span class="skill-tag">{skill}</span>' for skill in st.session_state.missing_skills[:20]]) if st.session_state.missing_skills else "No recommendations"
        st.markdown(f'<p style="color: var(--heavy-purple);">Consider adding skills like: {recommendations}</p>', unsafe_allow_html=True)

        col4, col5 = st.columns(2)
        with col4:
            if st.button("Get Resume Tips"):
                tips = [
                    "Highlight specific achievements with quantifiable results.",
                    "Tailor your skills to match the job description.",
                    "Use action verbs like 'developed' or 'optimized'.",
                    "Keep the resume to one page if under 10 years of experience.",
                    "Include a professional summary."
                ]
                st.markdown('<h3 class="text-2xl font-bold mb-4" style="color: var(--purple-pain);">Resume Tips</h3>', unsafe_allow_html=True)
                for tip in tips:
                    st.markdown(f'<p class="skill-tag" style="color: var(--heavy-purple);">{tip}</p>', unsafe_allow_html=True)
        with col5:
            if st.button("New Analysis"):
                for key in ['score', 'skills_matched', 'matched_skills_list', 'missing_skills', 'experience', 'keywords']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

# Profile Page
elif page == "Profile":
    st.markdown('<h2 class="text-4xl font-bold mb-6 slide-in-left" style="color: var(--purple-pain);">Profile</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--heavy-purple);">Manage your personal information and view analysis history</p>', unsafe_allow_html=True)
    st.markdown('<h3 class="text-xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Personal Information</h3>', unsafe_allow_html=True)
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (st.session_state.user_id,)).fetchone()
    conn.close()

    name = st.text_input("Full Name", value=user['name'])
    email = st.text_input("Email", value=user['email'], disabled=True)

    if st.button("Update Profile"):
        conn = get_db_connection()
        conn.execute("UPDATE users SET name=? WHERE id=?", (name, st.session_state.user_id))
        conn.commit()
        conn.close()
        st.success("Profile updated!")

    st.markdown('<h3 class="text-xl font-bold mb-4 slide-in-right" style="color: var(--purple-pain);">Uploaded Resumes</h3>', unsafe_allow_html=True)
    conn = get_db_connection()
    resumes = conn.execute("SELECT filename, upload_date, analysis_score FROM files WHERE user_id = ? AND file_type = 'resume'", (st.session_state.user_id,)).fetchall()
    conn.close()
    if resumes:
        for resume in resumes:
            st.markdown(f'<p class="skill-tag">{resume["filename"]} - Uploaded: {resume["upload_date"]} - Score: {resume["analysis_score"]:.0f}%</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color: var(--heavy-purple);">No resumes uploaded yet.</p>', unsafe_allow_html=True)

    st.markdown('<h3 class="text-xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Analysis History</h3>', unsafe_allow_html=True)
    if resumes:
        st.markdown('<p style="color: var(--purple-pain);">Date | Score | Verdict</p>', unsafe_allow_html=True)
        for resume in resumes:
            verdict = "High" if resume['analysis_score'] >= 80 else "Medium" if resume['analysis_score'] >= 60 else "Low"
            verdict_class = "status-high" if verdict == "High" else "status-medium" if verdict == "Medium" else "status-low"
            st.markdown(f'<p class="skill-tag">{resume["upload_date"]} | {resume["analysis_score"]:.0f}% | <span class="{verdict_class}">{verdict}</span></p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color: var(--heavy-purple);">No analysis history yet.</p>', unsafe_allow_html=True)

# Placement Dashboard Page
elif page == "Placement Dashboard":
    st.markdown('<h2 class="text-4xl font-bold mb-6 slide-in-left" style="color: var(--purple-pain);">Placement Dashboard</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--heavy-purple);">Manage and analyze candidate resumes</p>', unsafe_allow_html=True)

    # Stats Display
    conn = get_db_connection()
    total_candidates = conn.execute("SELECT COUNT(*) FROM files WHERE file_type = 'resume'").fetchone()[0]
    high_match = conn.execute("SELECT COUNT(*) FROM files WHERE analysis_score >= 80").fetchone()[0]
    avg_score = conn.execute("SELECT AVG(analysis_score) FROM files WHERE file_type = 'resume'").fetchone()[0] or 0
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.markdown(f'<div class="card-hover text-center p-4 rounded-lg"><div class="text-xl font-bold" style="color: var(--purple-pain);">{total_candidates}</div><div class="text-sm" style="color: var(--heavy-purple);">Total Candidates</div></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="card-hover text-center p-4 rounded-lg"><div class="text-xl font-bold" style="color: var(--purple-pain);">{high_match}</div><div class="text-sm" style="color: var(--heavy-purple);">High Match (80%+)</div></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="card-hover text-center p-4 rounded-lg"><div class="text-xl font-bold" style="color: var(--purple-pain);">{avg_score:.0f}%</div><div class="text-sm" style="color: var(--heavy-purple);">Avg. Match Score</div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["Resume Management", "Reports & Export"])
    with tabs[0]:
        st.markdown('<h3 class="text-xl font-bold mb-4 slide-in-right" style="color: var(--purple-pain);">Resume Management</h3>', unsafe_allow_html=True)
        if st.button("View All Resumes"):
            conn = get_db_connection()
            resumes = conn.execute("""
                SELECT f.filename, f.analysis_score, f.metadata, f.upload_date, u.name, u.email
                FROM files f JOIN users u ON f.user_id = u.id WHERE f.file_type = 'resume'
            """).fetchall()
            conn.close()
            if resumes:
                data = []
                for resume in resumes:
                    metadata = json.loads(resume['metadata'])
                    text_sample = metadata['text'][:100] + "..."
                    data.append({
                        'Name': resume['name'],
                        'Email': resume['email'],
                        'Filename': resume['filename'],
                        'Score': f"{resume['analysis_score']:.0f}%",
                        'Upload Date': resume['upload_date'],
                        'Text Sample': text_sample
                    })
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.markdown('<p style="color: var(--heavy-purple);">No resumes uploaded yet.</p>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<h3 class="text-xl font-bold mb-4 slide-in-right" style="color: var(--purple-pain);">Export All Students</h3>', unsafe_allow_html=True)
        if st.button("Export All Students (CSV)"):
            conn = get_db_connection()
            students = conn.execute("""
                SELECT u.name, u.email, f.filename, f.analysis_score, f.metadata, f.upload_date
                FROM users u JOIN files f ON u.id = f.user_id
                WHERE u.user_type = 'student' AND f.file_type = 'resume'
            """).fetchall()
            conn.close()
            if students:
                data = []
                for s in students:
                    metadata = json.loads(s['metadata'])
                    data.append({
                        'Name': s['name'],
                        'Email': s['email'],
                        'Filename': s['filename'],
                        'Score': f"{s['analysis_score']:.0f}%",
                        'Upload Date': s['upload_date'],
                        'Matched Skills': ', '.join(metadata['matched_skills'][:20]),
                        'Missing Skills': ', '.join(metadata['missing_skills'][:20]),
                        'Text Sample': metadata['text'][:100] + "..."
                    })
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)  # Display the table before download
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                st.download_button(
                    label="Download CSV",
                    data=buffer.getvalue(),
                    file_name="all_students.csv",
                    mime="text/csv",
                    key="download_csv"
                )
            else:
                st.markdown('<p style="color: var(--heavy-purple);">No students to export.</p>', unsafe_allow_html=True)

        st.markdown('<h3 class="text-xl font-bold mb-4 slide-in-left" style="color: var(--purple-pain);">Analytics Dashboard</h3>', unsafe_allow_html=True)
        col7, col8, col9, col10 = st.columns(4)
        col7.markdown(f'<div class="card-hover text-center p-4 rounded-lg"><div class="text-xl font-bold" style="color: var(--purple-pain);">{total_candidates}</div><div class="text-sm" style="color: var(--heavy-purple);">Total Applications</div></div>', unsafe_allow_html=True)
        col8.markdown(f'<div class="card-hover text-center p-4 rounded-lg"><div class="text-xl font-bold" style="color: var(--purple-pain);">{high_match}</div><div class="text-sm" style="color: var(--heavy-purple);">High Match (80%+)</div></div>', unsafe_allow_html=True)
        col9.markdown(f'<div class="card-hover text-center p-4 rounded-lg"><div class="text-xl font-bold" style="color: var(--purple-pain);">{total_candidates - high_match}</div><div class="text-sm" style="color: var(--heavy-purple);">Medium Match (60-79%)</div></div>', unsafe_allow_html=True)
        col10.markdown(f'<div class="card-hover text-center p-4 rounded-lg"><div class="text-xl font-bold" style="color: var(--purple-pain);">{total_candidates - high_match}</div><div class="text-sm" style="color: var(--heavy-purple);">Low Match</div></div>', unsafe_allow_html=True)