import streamlit as st
from chat_components import ChatComponents

# Check for current user and load or initialize chat history
if 'current_user' in st.session_state and st.session_state['current_user']:
    chat = ChatComponents(st.session_state['current_user'], "schoolmate", "./chat_history.csv")
    chat.run()
else:
    st.error("Please log in to access the chat.")
