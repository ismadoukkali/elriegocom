import streamlit as st
import sqlite3
import bcrypt
from config import Config
import logging
import io
import os

def init_db():
    conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS product_checks
                 (asin TEXT, price TEXT, check_date TIMESTAMP)''')
    conn.commit()
    return conn

def verify_password(password: str) -> bool:
    return password == Config.ADMIN_PASSWORD

def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def login(email: str, password: str) -> bool:
    if email == Config.ADMIN_EMAIL and verify_password(password):
        st.session_state.authenticated = True
        return True
    return False

def logout():
    st.session_state.authenticated = False

class StreamlitHandler(logging.StreamHandler):
    def __init__(self, placeholder):
        logging.StreamHandler.__init__(self)
        self.placeholder = placeholder
        self.log_text = io.StringIO()
        
    def emit(self, record):
        msg = self.format(record)
        self.log_text.write(msg + '\n')
        self.placeholder.text_area("Logs", self.log_text.getvalue(), height=100)

def add_logo_and_navigation():
    st.logo("images/logo.png", size="large")