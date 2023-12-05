import streamlit as st
import pandas as pd

"""
The session state is importand in Streamlit. 
It allows us to store information after refreshing the page or submit buttons or forms.
"""


if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'chat_histories' not in st.session_state:
    st.session_state['chat_histories'] = pd.DataFrame(columns=['MND Patient Name', 'Chatting To', 'Tag', 'Timestamp', 'Message Content'])


def login():
    st.session_state['current_user'] = st.text_input("Enter MND patient's name to login:")
    if st.button("Login"):
        st.experimental_rerun()

if not st.session_state['current_user']:
    login()
else:
    st.write(f"Logged in as: {st.session_state['current_user']}")

