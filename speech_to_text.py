import speech_recognition as sr
import streamlit as st

def recognize_speech(audio_path):
    # Initialize the recognizer
    r = sr.Recognizer()
    
    source = sr.AudioFile(audio_path)

    # Use the audio file as the audio source
    with source as s:
        # Record the audio file
        audio = r.record(s)

        try:
            # Recognize the content of the audio
            return r.recognize_google(audio)
        except sr.UnknownValueError:
            # API was unable to understand the audio
            st.sidebar.error("Google Speech Recognition could not understand the audio")
        except sr.RequestError as e:
            # The API was unreachable or unresponsive
            st.sidebar.error(f"Could not request results from Google Speech Recognition service; {e}")
