import streamlit as st
from utils.model import load_model
from utils.video_processing import process_video
from utils.graphs import display_graphs_and_outputs

st.set_page_config(page_title="YOLO Object Tracking App", layout="wide")
st.title("Object Tracking App")

uploaded_model = st.file_uploader("Upload your YOLO model (.pt file)", type=["pt"])
uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

# Ensure uploaded_video is stored in session state for downstream use
if uploaded_video:
    st.session_state["uploaded_video"] = uploaded_video

if uploaded_model and uploaded_video:
    interval_seconds = st.number_input("Count Interval (seconds)", min_value=1, value=1, step=10)
    if st.button("Process Video"):
        process_video(uploaded_model, uploaded_video, interval_seconds)
        st.session_state["processing_complete"] = True

if "processing_complete" in st.session_state:
    display_graphs_and_outputs()