import streamlit as st
import pandas as pd
from datetime import datetime

if 'current_user' not in st.session_state or not st.session_state['current_user']:
    st.error("Please log in to access the chat.")
else:
    if 'chat_histories' not in st.session_state:
        st.session_state['chat_histories'] = pd.DataFrame(columns=['MND Patient Name', 'Chatting To', 'Tag', 'Timestamp', 'Message Content', 'Sender'])

    # Chat interface
    st.header("Chat with Family")
    tag = "family"
    chatter_name = st.text_input("Enter Family Member's Name:")

    # Creating two columns for MND patient and the specific family member
    col_family, col_mnd = st.columns(2)

    # Family Member's message input
    with col_family:
        if chatter_name:
            st.subheader(f"Chat from {chatter_name}")
        family_message = st.text_area(f"Message from {chatter_name}:", key="family_message")
        if st.button("Send as Family Member", key="send_family") and chatter_name:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_chat = {
                'MND Patient Name': st.session_state['current_user'],
                'Chatting To': chatter_name,
                'Tag': tag,
                'Timestamp': timestamp,
                'Message Content': family_message,
                'Sender': chatter_name
            }
            chat_histories = st.session_state['chat_histories'].to_dict('records')
            chat_histories.append(new_chat)
            st.session_state['chat_histories'] = pd.DataFrame(chat_histories)
            st.experimental_rerun()

    # MND Patient's message input
    with col_mnd:
        st.subheader(f"Chat from {st.session_state['current_user']}")
        mnd_message = st.text_area("MND Patient's message:", key="mnd_message")
        if st.button("Send as MND Patient", key="send_mnd") and chatter_name:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_chat = {
                'MND Patient Name': st.session_state['current_user'],
                'Chatting To': chatter_name,
                'Tag': tag,
                'Timestamp': timestamp,
                'Message Content': mnd_message,
                'Sender': st.session_state['current_user']
            }
            chat_histories = st.session_state['chat_histories'].to_dict('records')
            chat_histories.append(new_chat)
            st.session_state['chat_histories'] = pd.DataFrame(chat_histories)
            st.experimental_rerun()

    # Save chat history to CSV file
    if st.button("Save Chat History to CSV"):
        st.session_state['chat_histories'].to_csv('chat_history.csv', index=False)
        st.success("Chat history saved to chat_history.csv")

    # Display chat history
    st.subheader("Chat History")
    user_chats = st.session_state['chat_histories']
    relevant_chats = user_chats[(user_chats['MND Patient Name'] == st.session_state['current_user']) & (user_chats['Chatting To'] == chatter_name)]
    for _, row in relevant_chats.iterrows():
        sender = row['Sender'] if row['Sender'] != 'MND Patient' else st.session_state['current_user']
        st.text(f"{sender} ({row['Timestamp']}): {row['Message Content']}")
