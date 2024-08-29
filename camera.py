import time
import cv2
import numpy as np
from PIL import Image
import tempfile
import os
import streamlit as st
from deepface import DeepFace

def camera_main():
    st.header("Camera Feed")

    # Create placeholders for video feed and analysis results
    video_placeholder = st.empty()
    analysis_placeholder = st.empty()

    # Initialize the camera
    cap = cv2.VideoCapture(0)

    # Initialize the state for DeepFace analysis
    if "last_analysis" not in st.session_state:
        st.session_state.last_analysis = time.time() - 100  # Ensures immediate first analysis

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            st.error("Failed to capture image from camera.")
            break

        # Convert the frame from BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        # Display the current frame
        video_placeholder.image(image, caption="Live Camera Feed", use_column_width=True)

        # Save the frame to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file_path = temp_file.name
            cv2.imwrite(temp_file_path, frame)

        # Automatically perform DeepFace analysis every 5 seconds
        current_time = time.time()
        if current_time - st.session_state.last_analysis > 5:  # Interval of 5 seconds
            try:
                # Perform DeepFace analysis
                analysis_result = DeepFace.analyze(img_path=temp_file_path, actions=['age', 'gender', 'race', 'emotion'])
                analysis_placeholder.write("DeepFace Analysis Result:")
                analysis_placeholder.json(analysis_result)
                st.session_state.last_analysis = current_time
            except Exception as e:
                analysis_placeholder.error(f"DeepFace analysis error: {e}")

        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    camera_main()
