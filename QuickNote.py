import streamlit as st
import pandas as pd
import torch
import whisper
import warnings
import time
import re
import tempfile
from fuzzywuzzy import process
from streamlit_audio_recorder import audio_recorder  # pip install streamlit-audio-recorder

warnings.filterwarnings("ignore")

# ---------------- Global Setup ----------------

# Define the menu items dataframe
menu_items = pd.DataFrame({
    "Items": [
        "chicken burger", "veg momos", "french fries", "veg sandwich",
        "chicken juicy burger", "veg pizza", "burrito", "paneer momos", "vadapav"
    ],
    "Price": [50, 60, 65, 50, 40, 80, 70, 65, 45]
})

# Cache the Whisper model so it loads only once
@st.cache_resource
def load_whisper_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model("small").to(device)

model = load_whisper_model()

# Function to extract order items from transcribed text
def extract_items(text, menu_items_df, quantity_threshold=40):
    items = []
    quantities = []
    stop_words = {'count', 'piece', 'pieces', 'nos', 'x', 'no', 'ct', 'pk', 'qt', 'pack'}
    segments = [s.strip() for s in re.split(r'[,.;]', text) if s.strip()]
    
    for segment in segments:
        numbers = re.findall(r'\b\d+\b', segment)
        quantity = 1
        item_candidate = segment
        
        if numbers:
            quantity = int(numbers[0])
            item_candidate = re.sub(r'\b{}\b'.format(numbers[0]), '', segment, count=1).strip()
        
        item_candidate = re.sub(r'[^\w\s]', '', item_candidate).strip().lower()
        item_candidate = ' '.join([word for word in item_candidate.split() if word not in stop_words])
        
        if item_candidate:
            menu_items_list = menu_items_df['Items'].tolist()
            match_result = process.extractOne(item_candidate, menu_items_list)
            if match_result:
                match, score = match_result
                if score >= quantity_threshold:
                    items.append(match)
                    quantities.append(quantity)
                    
    # Create dataframe with extracted information
    current_day = " ".join(time.ctime().split()[1:3])
    now = time.strftime("%I:%M %p")
    df = pd.DataFrame({
        'Day': [current_day] * len(items),
        'Time': [now] * len(items),
        'Items': items,
        'Quantity': quantities
    })
    # Merge to get unit prices
    merged_df = pd.merge(df, menu_items_df, on='Items', how='left')
    merged_df.rename(columns={'Price': 'Unit_Price'}, inplace=True)
    merged_df['Price'] = merged_df['Unit_Price'] * merged_df['Quantity']
    return merged_df

# Initialize session state variables
if 'recorded_audio' not in st.session_state:
    st.session_state.recorded_audio = None
if 'current_df' not in st.session_state:
    st.session_state.current_df = None
if 'log_df' not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=['Day', 'Time', 'Items', 'Quantity', 'Unit_Price', 'Price'])

# ---------------- Streamlit UI ----------------

st.title("Voice Order Processing App")

# Section: Record Audio
st.header("Record Your Order")
audio_bytes = audio_recorder()
if audio_bytes is not None:
    st.audio(audio_bytes, format="audio/wav")
    st.session_state.recorded_audio = audio_bytes

# Section: Upload & Process Audio
if st.button("Upload Audio for Processing"):
    if st.session_state.recorded_audio is None:
        st.error("No audio recorded!")
    else:
        # Save the recorded audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(st.session_state.recorded_audio)
            tmp_file_path = tmp_file.name
        
        with st.spinner("Transcribing audio..."):
            result = model.transcribe(tmp_file_path)
            transcribed_text = result["text"]
        st.write("**Transcribed Text:**", transcribed_text)
        
        # Extract items from transcribed text
        df_extracted = extract_items(transcribed_text, menu_items)
        st.session_state.current_df = df_extracted.copy()
        st.success("Audio processed and items extracted!")

# Section: Review and Adjust Order
if st.session_state.current_df is not None:
    st.header("Review and Adjust Order")
    
    # Display each row with minus and plus buttons for quantity adjustment
    for idx, row in st.session_state.current_df.iterrows():
        cols = st.columns([2, 1, 1, 1, 2])
        cols[0].write(row['Items'])
        # Minus button
        if cols[1].button(" - ", key=f"minus_{idx}"):
            current_qty = st.session_state.current_df.loc[idx, "Quantity"]
            new_qty = max(1, current_qty - 1)
            st.session_state.current_df.loc[idx, "Quantity"] = new_qty
            st.session_state.current_df.loc[idx, "Price"] = st.session_state.current_df.loc[idx, "Unit_Price"] * new_qty
            st.experimental_rerun()
        # Display current quantity
        cols[2].write(st.session_state.current_df.loc[idx, "Quantity"])
        # Plus button
        if cols[3].button(" + ", key=f"plus_{idx}"):
            new_qty = st.session_state.current_df.loc[idx, "Quantity"] + 1
            st.session_state.current_df.loc[idx, "Quantity"] = new_qty
            st.session_state.current_df.loc[idx, "Price"] = st.session_state.current_df.loc[idx, "Unit_Price"] * new_qty
            st.experimental_rerun()
        # Display price for this row
        cols[4].write(f"₹ {st.session_state.current_df.loc[idx, 'Price']}")
    
    # Show total amount for this order
    total_amount = st.session_state.current_df['Price'].sum()
    st.subheader(f"Total Amount: ₹ {total_amount}")
    
    # Submit the current order to the log
    if st.button("Submit Order"):
        st.session_state.log_df = pd.concat(
            [st.session_state.log_df, st.session_state.current_df], ignore_index=True
        )
        st.success("Order submitted successfully!")
        # Clear the current order data to allow for a new one
        st.session_state.current_df = None
        st.session_state.recorded_audio = None

# Section: View Order Log
if st.button("View Order Log"):
    st.header("Order Log")
    st.dataframe(st.session_state.log_df)
