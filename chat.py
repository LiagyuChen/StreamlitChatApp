import streamlit as st
import pandas as pd
import base64

# Initialize session state
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'log_chat' not in st.session_state:
    st.session_state['log_chat'] = False
if 'chat_data' not in st.session_state:
    st.session_state['chat_data'] = None
if 'chat_histories' not in st.session_state:
    st.session_state['chat_histories'] = pd.DataFrame(columns=['MNDName', 'Chatter', 'Tag', 'SubTag', 'Timestamp', 'Message', 'Sender'])

# Hangle login
def login():
    st.session_state['current_user'] = st.text_input("Enter MND patient's name to login:")
    if st.button("Login"):
        st.experimental_rerun()

# Function to convert DataFrame to CSV and then encode it to base64
def convert_df_to_csv_base64(df):
    csv_file = df.to_csv(index=False).encode('utf-8')
    b64 = base64.b64encode(csv_file).decode()
    return b64

# Check if user is logged in
if not st.session_state['current_user']:
    login()
else:
    st.write(f"Logged in as: {st.session_state['current_user']}")
    
    # Choose if log the chat data
    st.session_state['log_chat'] = st.checkbox("Log chat data?", value=st.session_state['log_chat'])

    if st.session_state['log_chat']:
        st.markdown("* Upload a CSV file containing chat history data")
        st.markdown("* The columns of the CSV file must be exactly the same as:")
        st.markdown("* `MNDName`, `Chatter`, `Tag`, `SubTag`, `Timestamp`, `Message`, `Sender`")
        chat_data = st.file_uploader("Upload chat history file:", type=['csv'])
        
        # Update session state only if new file is uploaded
        if chat_data is not None and chat_data != st.session_state['chat_data']:
            st.session_state['chat_data'] = chat_data
            if chat_data.size > 0:
                try:
                    data_df = pd.read_csv(chat_data)
                    if not data_df.empty and data_df.columns.tolist() == ['MNDName', 'Chatter', 'Tag', 'SubTag', 'Timestamp', 'Message', 'Sender']:
                        st.session_state['chat_histories'] = data_df
                    else:
                        st.warning("The uploaded CSV file does not have the correct columns, the original content will be replaced!")
                except pd.errors.EmptyDataError:
                    st.warning("The uploaded CSV file is empty!")

        # Provide a download button if chat_histories is available
        if st.session_state['chat_data'] and st.session_state['chat_histories'] is not None:
            file_base64 = convert_df_to_csv_base64(st.session_state['chat_histories'])
            href = f'<a href="data:file/csv;base64,{file_base64}" download="updated_{st.session_state["chat_data"].name}">Download updated chat history file</a>'
            st.markdown(href, unsafe_allow_html=True)

