import os
import streamlit as st
import pandas as pd
from datetime import datetime
from emojis import emojis

class ChatComponents:
    def __init__(self, user, tag, chat_history_path):
        self.user = user
        self.tag = tag
        self.chat_history_path = chat_history_path
        self.initialize_session_state()
        self.load_chat_history()

    def load_chat_history(self):
        if 'chat_histories' in st.session_state and not st.session_state['chat_histories'].empty:
            df = st.session_state['chat_histories']
            self.chatters = df[(df["MNDName"] == self.user) & (df["Tag"] == self.tag)]["Chatter"].unique().tolist()
            self.has_chats = True
        else:
            self.chatters = []
            self.has_chats = False
        
        if st.session_state['new_contact']:
            self.chatters.extend([new_contact['name'] for new_contact in st.session_state['new_contact'] if new_contact['tag'] == self.tag and new_contact['name'] not in self.chatters])

    def initialize_session_state(self):
        if 'current_message' not in st.session_state:
            st.session_state['current_message'] = ""
        if 'selected_emoji' not in st.session_state:
            st.session_state['selected_emoji'] = ""
        if 'new_contact' not in st.session_state:
            st.session_state['new_contact'] = []

    def handle_new_contact(self):
        with st.sidebar:
            if st.button("Add New Contact"):
                st.session_state['adding_new_contact'] = True

            if 'adding_new_contact' in st.session_state and st.session_state['adding_new_contact']:
                with st.form("add_contact_form"):
                    new_chatter_name = st.text_input("Enter new contact's name:")
                    new_chatter_subtag = st.text_input("Enter new contact's subtag:", "")
                    add_button = st.form_submit_button("Add")
                    if add_button:
                        st.session_state['adding_new_contact'] = False
                        # Check if new contact already exists
                        if new_chatter_name not in self.chatters: 
                            st.session_state['new_contact'].append({'name': new_chatter_name, 'subtag': new_chatter_subtag, 'tag': self.tag})
                            self.chatters.append(new_chatter_name)
                        else:
                            st.error("This contact already exists!")

    def render_chat_interface(self):
        st.header(f"Chat with {self.tag}")

        self.handle_new_contact()
            
        self.chatter_name = st.sidebar.selectbox("Select chatter:", self.chatters)
        
        if not self.chatter_name:
            st.sidebar.error("Please add a contact to start chatting!")
        else:
            self.subtag = ""
            for new_contact in st.session_state['new_contact']:
                if self.chatter_name == new_contact['name']:
                    self.subtag = new_contact['subtag']
                    break

            if self.subtag == "":
                if self.has_chats:
                    df = st.session_state['chat_histories']
                    chatter_record = df[df["Chatter"] == self.chatter_name]
                    chatter_uniques = chatter_record["SubTag"].unique().tolist()
                    if chatter_uniques:
                        self.subtag = chatter_uniques[0] if chatter_uniques else ""
                else:
                    self.subtag = "unknown"
            
            # Chat input fields
            self.selected_chatter = st.sidebar.selectbox("Select a sender: ", [self.user, self.chatter_name])
            self.chatter_dict = {self.user: "mnd_message", self.chatter_name: f"{self.tag}_message"}
            
            if not st.session_state['log_chat']:
                self.send_message_button = False
                message_key = self.chatter_dict[self.selected_chatter]
                self.chatter_message = st.chat_input("Type a message...", key=message_key)
                if self.chatter_message:
                    self.send_message_button = True
            else:
                self.input_emojis()
        
            # Voice input (placeholder for future implementation)
            st.sidebar.button("Voice Input")
    
    def sent_message(self):
        self.send_message_button = True
        print("Message sent!", self.send_message_button)

    def input_emojis(self):
        # Emoji selector in the sidebar
        selected_emoji = st.sidebar.selectbox("Choose an emoji:", list(emojis.keys()), index=0)

        # Add the selected emoji to the current message
        if st.sidebar.button("Add Emoji"):
            st.session_state['current_message'] += emojis[selected_emoji]
        
        # Chat input field with the current message (and emoji if added)
        message_key = self.chatter_dict[self.selected_chatter]
        self.chatter_message = st.text_input("Type your message here...", value=st.session_state['current_message'], key=message_key)
        self.send_message_button = st.button("Send")
        
        # Update the session state with the current input
        st.session_state['current_message'] = self.chatter_message

        # Handle sending the message
        if self.send_message_button:
            self.chatter_message = st.session_state['current_message']
            st.session_state['current_message'] = ""
        else:
            self.chatter_message = ""
    
    def display_chat_history(self):
        user_chats = st.session_state['chat_histories']
        relevant_chats = user_chats[(user_chats['MNDName'] == self.user) & (user_chats['Chatter'] == self.chatter_name)]
        for _, row in relevant_chats.iterrows():
            col1, col2 = st.columns([1, 5])
            with col1 if row['Sender'] != self.user else col2:
                st.markdown(f"""
                <div style='text-align: {"left" if row['Sender'] != self.user else "right"}; background-color: {"#FCEE98" if row['Sender'] != self.user else "#A4BF7B"}; padding: 10px; border-radius: 10px;'>
                    <p style='font-size: small; color: grey;'>{row['Timestamp']}</p>
                    <p>{row['Message']}</p>
                </div>
                """, unsafe_allow_html=True)

    def process_sending_message(self):
        if self.send_message_button and self.chatter_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_chat = {
                'MNDName': self.user,
                'Chatter': self.chatter_name,
                'Tag': self.tag,
                'SubTag': self.subtag,
                'Timestamp': timestamp,
                'Message': self.chatter_message,
                'Sender': self.selected_chatter
            }
            current_record = st.session_state['chat_histories'].to_dict('records')
            current_record.append(new_chat)
            st.session_state['chat_histories'] = pd.DataFrame(current_record)
            st.rerun()  

    def run(self):
        self.render_chat_interface()
        # self.input_emojis()
        self.display_chat_history()
        if self.chatter_name:
            self.process_sending_message()
