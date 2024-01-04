import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import json
import pyperclip
from io import BytesIO
import requests
from speech_to_text import recognize_speech

def get_image_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

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

    def subtag_value(self):
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

    def render_chat_interface(self):
        st.header(f"Chat with {self.tag}")

        self.handle_new_contact()

        self.chatter_name = st.sidebar.selectbox("Select chatter:", self.chatters)
        if not self.chatter_name:
            st.sidebar.error("Please add a contact to start chatting!")
        else:
            # Assign the subtag value
            self.subtag_value()
            # Chat input fields
            self.selected_chatter = st.sidebar.selectbox("Select a sender: ", [self.user, self.chatter_name])
            self.chatter_dict = {self.user: "mnd_message", self.chatter_name: f"{self.tag}_message"}
            # Select Emojis
            self.send_emojis()
            # Voice Input
            self.voice_input()
            # Send message button
            self.send_message()

    def read_emojis(self):
        with open('emojis.json', 'r', encoding='utf-8') as f:
            emojis = json.load(f)
        return emojis
    
    def send_emojis(self):
        emoji_json = self.read_emojis()
        emoji_keys = list(emoji_json.keys())
        emoji_keys.insert(0, "None")
        emoji_selecter = st.sidebar.selectbox("Choose an emoji:", emoji_keys, index=0)
        if emoji_selecter != "None":
            emoji_unicode = emoji_json[emoji_selecter]
            st.sidebar.markdown(f"copy the emoji: \n{emoji_unicode}")
    
    def send_message(self):
        self.send_message_button = False
        message_key = self.chatter_dict[self.selected_chatter]
        self.chatter_message = st.chat_input("Type a message...", key=message_key)
        if self.chatter_message:
            self.send_message_button = True
    
    def voice_input(self):
        voice_input = st.sidebar.checkbox("Enable Voice Input")
        if voice_input:
            audio_upload_type = st.sidebar.radio("Upload audio file from:", ("Local", "URL"))
            if audio_upload_type == "Local":
                audio_file = st.sidebar.file_uploader("Upload an audio file", type=['wav', 'mp3'])
            else:
                audio_url = st.sidebar.text_input("Enter audio URL:")
                if audio_url:
                    response = requests.get(audio_url)
                    audio_file = response.content
                else:
                    audio_file = None

            if audio_file is not None:
                st.sidebar.audio(audio_file)
                # Convert the uploaded file to BytesIO
                audio_data = BytesIO(audio_file.getvalue())
                # Process the audio file
                recognized_text = recognize_speech(audio_data)
                # Button to copy text to clipboard
                if st.sidebar.button("Copy recognized text to Clipboard"):
                    pyperclip.copy(recognized_text)
                    st.sidebar.success("Copied to clipboard!")
    
    def display_chat_history(self):
        user_chats = st.session_state['chat_histories']
        relevant_chats = user_chats[(user_chats['MNDName'] == self.user) & (user_chats['Chatter'] == self.chatter_name)]
        for _, row in relevant_chats.iterrows():
            col1, col2 = st.columns([5, 5])
            with col1 if row['Sender'] != self.user else col2:
                man_img_base64 = get_image_base64('assets/man.png')
                woman_img_base64 = get_image_base64('assets/woman.png')
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; {('justify-content: flex-start;' if row['Sender'] != self.user else 'justify-content: flex-end;')}">
                    <div style="{('order: 2;' if row['Sender'] == self.user else '')} border-radius: 50%; width: 40px; height: 40px; overflow: hidden; margin-right: 10px; {('margin-left: 10px;' if row['Sender'] == self.user else '')}">
                        <img src='data:image/png;base64,{man_img_base64 if row['Sender'] == self.user else woman_img_base64}' style="width: 100%; height: auto;">
                    </div>
                    <div style="background-color: {'#3399CC' if row['Sender'] != self.user else '#009966'}; color: white; padding: 5px; border-radius: 10px; max-width: 50%; word-wrap: break-word; white-space: normal;">
                        <div style='font-size: small; color: #CCCCCC;'>{row['Timestamp']}</div>
                        <div>{row['Message']}</div>
                    </div>
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
        self.display_chat_history()
        if self.chatter_name:
            self.process_sending_message()