import streamlit as st
import requests
from data import get_df, menu_df
import pandas as pd

st.title("QuickNote")
st.sidebar.title('Menu')
st.sidebar.dataframe(menu_df, use_container_width=True)

# Initialize session state for persistent storage
if 'total_items' not in st.session_state:
    st.session_state.total_items = pd.DataFrame(columns=["Item", "Quantity", "Price", "Total"])

# For storing current transcribed df
if 'current_df' not in st.session_state:
    st.session_state.current_df = None

audio_value = st.audio_input("Record the audio")

if audio_value:
    st.audio(audio_value)

    if st.button('Transcribe'):

        files = {"file": ("recording.wav", audio_value, "audio/wav")}

        with st.spinner("In progess..."):
            try:
                response = requests.post("https://656cbe97210e.ngrok-free.app/transcribe", files=files)

                if response.status_code == 200:
                    st.success("Transcribed successfully!")
                    df = get_df(response.text)
                    st.session_state.current_df = df  # Save current df to session
                    st.table(df)
                    st.subheader(f"Total : ₹{sum(df['Total'])}")
                else:
                    st.error(f"Transcription failed with status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")

# Show submit button only if we have a current transcribed df
if st.session_state.current_df is not None:
    if st.button("Submit"):
        st.session_state.total_items = pd.concat([st.session_state.total_items, st.session_state.current_df], ignore_index=True)
        st.success("Entry added to log.")
        st.session_state.current_df = None  # Clear after submitting

# View log
# Initialize session state for log visibility
# Initialize session state for the total_items DataFrame and log visibility
if 'total_items' not in st.session_state:
    st.session_state.total_items = pd.DataFrame()
if 'show_log' not in st.session_state:
    st.session_state.show_log = False

# Show both buttons side-by-side
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("View Log"):
        st.session_state.show_log = True

with col2:
    if st.button("Close Log"):
        st.session_state.show_log = False

# Display the log if the flag is True
if st.session_state.show_log and not st.session_state.total_items.empty:
    st.subheader("Submitted Orders Log")
    st.dataframe(st.session_state.total_items, use_container_width=True)
    st.subheader(f"Grand Total: ₹{sum(st.session_state.total_items['Total'])}")
elif st.session_state.show_log and st.session_state.total_items.empty:
    st.info("No submissions yet.")
