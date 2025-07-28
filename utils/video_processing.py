import tempfile, os, cv2
from collections import defaultdict
import pandas as pd
import supervision as sv
from .model import load_model
import streamlit as st

def process_video(uploaded_model, uploaded_video, interval_seconds):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as model_file:
        model_file.write(uploaded_model.read())
        model_path = model_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
        video_file.write(uploaded_video.read())
        input_video_path = video_file.name

    model = load_model(model_path)
    cap = cv2.VideoCapture(input_video_path)
    original_filename = os.path.splitext(uploaded_video.name)[0]
    out_path = os.path.join(tempfile.gettempdir(), f"track_result_{original_filename}.mp4")
    width, height = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    box_annotator = sv.BoxAnnotator()
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    progress = st.progress(0)

    # Use working logic from standalone script
    second_counts = defaultdict(set)
    tracker_lifetimes = defaultdict(int)
    min_frames = int(fps * 0.5)

    for idx in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(frame, imgsz=1280, tracker="bytetrack.yaml")[0]
        detections = sv.Detections.from_ultralytics(results)
        detections = detections[detections.confidence > 0.5]
        frame = box_annotator.annotate(scene=frame, detections=detections)

        for xyxy, tracker_id in zip(detections.xyxy, detections.tracker_id):
            if tracker_id is None:
                continue
            x1, y1, *_ = map(int, xyxy)
            cv2.putText(frame, f"ID: {tracker_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)

        frame = draw_counter(frame, len(detections))
        out.write(frame)

        second = int(idx / fps // interval_seconds * interval_seconds)
        for tracker_id in detections.tracker_id:
            if tracker_id is not None:
                tracker_lifetimes[tracker_id] += 1
                if tracker_lifetimes[tracker_id] >= min_frames:
                    second_counts[second].add(tracker_id)

        progress.progress(min((idx + 1) / frame_count, 1.0))

    cap.release()
    out.release()

    df_counts = pd.DataFrame(
        [(s, len(ids)) for s, ids in sorted(second_counts.items())],
        columns=["Second", "Unique IDs"]
    )
    csv_path = os.path.join(tempfile.gettempdir(), f"track_result_{original_filename}.csv")
    df_counts.to_csv(csv_path, index=False)
    # Removed the st.download_button block for CSV download

    # Store results in session state for downstream use
    st.session_state["df_counts"] = df_counts
    st.session_state["preview_frame"] = cv2.cvtColor(cv2.VideoCapture(out_path).read()[1], cv2.COLOR_BGR2RGB)
    st.session_state["output_video_path"] = out_path
    st.session_state["csv_path"] = csv_path
    st.session_state["graph_path"] = os.path.join(tempfile.gettempdir(), "detection_graph.png")
    st.session_state["uploaded_video"] = uploaded_video

    st.session_state["processing_complete"] = True


# Draws the count in the top-right corner of the frame
def draw_counter(frame, count):
    text = f"Count: {count}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
    text_x = frame.shape[1] - text_size[0] - 10  # Top-right corner
    text_y = 30
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, (0, 255, 0), thickness)
    return frame