import streamlit as st
import requests
from data import get_df, menu_df
import pandas as pd
import streamlit.components.v1 as components

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
                    df = get_df(response.text)
                    st.session_state.current_df = df  # Save current df to session
                        
                else:
                    st.error(f"Transcription failed with status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")

# Show current transcribed data with delete functionality
if st.session_state.current_df is not None and not st.session_state.current_df.empty:
    st.subheader("Current Transcription")

    custom_table_html = """
    <style>
        .responsive-table {
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            min-width: 600px;
        }
        th, td {
            text-align: center;
            padding: 10px;
            border: 1px solid #ddd;
        }
        .qty-buttons {
            display: flex;
            justify-content: center;
            gap: 8px;
        }
        .qty-buttons form {
            display: inline;
        }
        .delete-btn form {
            display: inline;
        }
    </style>
    <div class="responsive-table">
        <table>
            <thead>
                <tr>
                    <th>Delete</th>
                    <th>Item</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
    """

    for idx, row in st.session_state.current_df.iterrows():
        custom_table_html += f"""
            <tr>
                <td class="delete-btn">
                    <form action="?delete={idx}" method="post">
                        <button type="submit">🗑️</button>
                    </form>
                </td>
                <td>{row['Item']}</td>
                <td class="qty-buttons">
                    <form action="?minus={idx}" method="post">
                        <button type="submit">➖</button>
                    </form>
                    {row['Quantity']}
                    <form action="?plus={idx}" method="post">
                        <button type="submit">➕</button>
                    </form>
                </td>
                <td>{row['Price']}</td>
                <td>{row['Total']}</td>
            </tr>
        """

    custom_table_html += """
            </tbody>
        </table>
    </div>
    """

    st.markdown(custom_table_html, unsafe_allow_html=True)

    # Check for button actions
    query_params = st.experimental_get_query_params()

    if "delete" in query_params:
        idx = int(query_params["delete"][0])
        st.session_state.current_df = st.session_state.current_df.drop(idx).reset_index(drop=True)
        st.experimental_set_query_params()
        st.rerun()

    if "plus" in query_params:
        idx = int(query_params["plus"][0])
        st.session_state.current_df.at[idx, "Quantity"] += 1
        st.session_state.current_df.at[idx, "Total"] = (
            st.session_state.current_df.at[idx, "Quantity"] * st.session_state.current_df.at[idx, "Price"]
        )
        st.experimental_set_query_params()
        st.rerun()

    if "minus" in query_params:
        idx = int(query_params["minus"][0])
        if st.session_state.current_df.at[idx, "Quantity"] > 1:
            st.session_state.current_df.at[idx, "Quantity"] -= 1
            st.session_state.current_df.at[idx, "Total"] = (
                st.session_state.current_df.at[idx, "Quantity"] * st.session_state.current_df.at[idx, "Price"]
            )
            st.experimental_set_query_params()
            st.rerun()

    st.subheader(f"Current Total: ₹{sum(st.session_state.current_df['Total'])}")


# Show submit button only if we have a current transcribed df
if st.session_state.current_df is not None and not st.session_state.current_df.empty:
    if st.button("Submit"):
        st.session_state.total_items = pd.concat([st.session_state.total_items, st.session_state.current_df], ignore_index=True)
        st.success("Entry added to log.")
        #st.session_state.current_df = None  # Clear after submitting

# View log
# Initialize session state for log visibility
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
