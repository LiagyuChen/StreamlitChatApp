import streamlit as st
import pandas as pd
from datetime import datetime
import pyperclip
from io import BytesIO
import requests
import json
import asyncio
from speech_to_text import recognize_speech
from llamaapi import LlamaAPI

def experimental_file_uploader():
    mnd_persona_file = st.sidebar.file_uploader("Upload MND Persona JSON", type="json")
    chatter_persona_file = st.sidebar.file_uploader("Upload Chatter Persona JSON", type="json")
    example_mnd_msgs_file = st.sidebar.file_uploader("Upload Example MND Messages", type="txt")
    example_chat_msgs_file = st.sidebar.file_uploader("Upload Example Chat Messages", type="txt")
    
    if mnd_persona_file is None or chatter_persona_file is None or example_mnd_msgs_file is None or example_chat_msgs_file is None:
        st.sidebar.warning("Please upload all the required files!")
    
    mnd_persona, chatter_persona, example_mnd_msgs, example_chat_msgs = None, None, None, None
    
    if mnd_persona_file:
        mnd_persona = json.load(mnd_persona_file)
        mnd_persona = json.dumps(mnd_persona)
    
    if chatter_persona_file:
        chatter_persona = json.load(chatter_persona_file)
        chatter_persona = json.dumps(chatter_persona)

    # Processing the uploaded text files
    if example_mnd_msgs_file:
        example_mnd_msgs = example_mnd_msgs_file.getvalue().decode("utf-8").split("\n")
    
    if example_chat_msgs_file:
        example_chat_msgs = example_chat_msgs_file.getvalue().decode("utf-8").split("\n")
        example_chat_msgs = [{
            "chatter": m.split(":")[0],
            "content": m.split(":")[1].strip().replace('"', "")
        } for m in example_chat_msgs if m.strip() != ""]
    return mnd_persona, chatter_persona, example_mnd_msgs, example_chat_msgs

def send_emojis():
    with open('emojis.json', 'r', encoding='utf-8') as f:
        emoji_json = json.load(f)
    emoji_keys = list(emoji_json.keys())
    emoji_keys.insert(0, "None")
    emoji_selecter = st.sidebar.selectbox("Choose an emoji:", emoji_keys, index=0)
    if emoji_selecter != "None":
        emoji_unicode = emoji_json[emoji_selecter]
        st.sidebar.markdown(f"copy the emoji: \n{emoji_unicode}")

def voice_input():
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

def load_chat_history(mnd, chatter):
    if 'chat_histories' in st.session_state and not st.session_state['chat_histories'].empty:
        df = st.session_state['chat_histories']
        his_chats = df[(df['MNDName'] == mnd) & (df['Chatter'] == chatter)]
        for _, row in his_chats.iterrows():
            if row['Sender'] == mnd:
                st.chat_message('user').write(row['Message'])
            else:
                st.chat_message('assistant').write(row['Message'])

def store_message(mnd, chatter, tag, subtag, message, sender):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_chat = {
        'MNDName': mnd,
        'Chatter': chatter,
        'Tag': tag,
        'SubTag': subtag,
        'Timestamp': timestamp,
        'Message': message,
        'Sender': sender
    }
    current_record = st.session_state['chat_histories'].to_dict('records')
    current_record.append(new_chat)
    st.session_state['chat_histories'] = pd.DataFrame(current_record)
    # st.rerun()
                    
def chat_setup():
    tag = st.sidebar.text_input("Enter the tag:", "Family")
    subtag = st.sidebar.text_input("Enter the subtag:", "Wife")
    mnd_name = st.session_state['current_user']
    chatter_name = st.sidebar.text_input("Enter the chatter's name:", "Emily")
    
    # Select Emojis
    send_emojis()
    # Voice Input
    voice_input()
    return tag, subtag, mnd_name, chatter_name

def llama_chat(llama):
    # Select the chat mode
    chat_mode = st.sidebar.radio("Select Chat Mode", ['Normal', 'Experimental'])
    
    # LLaMa API
    if chat_mode == 'Normal':
        prompt_message = "Assist the user kindly and politely."
    elif chat_mode == 'Experimental':
        mnd_persona, chatter_persona, example_mnd_msgs, example_chat_msgs = experimental_file_uploader()
        prompt_message = f"""
        Create a chatbot model that mimics the communication style of an MND patient using these inputs:
        1. MND Patient Persona ({mnd_persona}): Traits and speech patterns of an MND patient.
        2. Relationship Context ({chatter_persona}): Persona of someone close to the MND patient.
        3. Historical Chat Data:
        - MND Patient's Previous Messages ({example_mnd_msgs}): Past messages from the MND patient.
        - Example Chats ({example_chat_msgs}): Previous conversations between the MND patient and the other.
        The chatbot's task is to generate one-sentence, informal responses to new messages from the normal person.
        Responses should reflect the MND patient's usual language and be appropriate to their relationship with the sender.
        The output should be limited to a single sentence response without additional explanations.
        """
    
    # Select LLM
    model_list = ["llama-7b-chat", "llama-7b-32k", "llama-13b-chat", "llama-70b-chat",
                  "mixtral-8x7b-instruct", "mistral-7b-instruct", "mistral-7b",
                  "Nous-Hermes-Llama2-13b", "falcon-7b-instruct", "falcon-40b-instruct",
                  "alpaca-7b", "codellama-7b-instruct", "codellama-13b-instruct",
                  "codellama-34b-instruct", "openassistant-llama2-70b",
                  "vicuna-7b", "vicuna-13b", "vicuna-13b-16k"]
    llm = st.sidebar.selectbox("Select Model", model_list, index=0)
    
    # Get user message
    user_input = st.chat_input("Type your message here...")
    answer = None
    if user_input:
        # Display the user message
        user_message = st.chat_message("user")
        user_message.write(user_input)
        
        # Define the API request JSON
        api_request_json = {
            "model": llm,
            "messages": [
                {"role": "system", "content": prompt_message},
                {"role": "user", "content": user_input},
            ],
            "stream": False,
        }
        
        # Execute the API request
        response = llama.run(api_request_json)
        # Get the response
        answer = response.json()["choices"][0]["message"]["content"]
        if answer.startswith('"'):
            answer = answer[1:]
        if answer.endswith('"'):
            answer = answer[:-1]
        # Display the response
        assistent_message = st.chat_message("assistant")
        assistent_message.write(answer)
        
    return user_input, answer

def get_api_key():
    # Get the API Key
    if 'api_key' not in st.session_state:
        st.session_state['api_key'] = None

    if st.session_state['api_key'] is None:
        api_key = None
        api_file = st.file_uploader("Upload a file with Llama API token", type="txt")
        if api_file is not None:
            api_key = api_file.getvalue().decode("utf-8").strip()
            st.session_state['api_key'] = api_key

def llama_init(api_key):
    # Function to asynchronously initialize Llama API and handle requests
    async def init_llama_api(api_key):
        llama = LlamaAPI(api_key)
        return llama
    
    # Create a new event loop for the async task
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    llama = None
    try:
        llama = new_loop.run_until_complete(init_llama_api(api_key))
    finally:
        new_loop.close()
    return llama

def llm_chat_main():
    get_api_key()
    
    if st.session_state['api_key']:
        llama = llama_init(st.session_state['api_key'])
        
        # If successfully initialized, run the llama chat
        if llama:
            tag, subtag, mnd_name, chatter_name = chat_setup()
            load_chat_history(mnd_name, chatter_name)
            # Chat Interface
            user_input, answer = llama_chat(llama)
            # Store the chat history
            if user_input:
                store_message(mnd_name, chatter_name, tag, subtag, user_input, chatter_name)
            if answer:
                store_message(mnd_name, chatter_name, tag, subtag, answer, mnd_name)


# Check for current user and load or initialize chat history
if 'current_user' in st.session_state and st.session_state['current_user']:
    llm_chat_main()
else:
    st.error("Please log in to access the chat.")
