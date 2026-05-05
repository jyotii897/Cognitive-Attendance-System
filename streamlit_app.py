import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import json
import os
import mediapipe as mp
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

# --- Streamlit Page Config ---
st.set_page_config(page_title="Cognito Attendance", page_icon="🧠", layout="wide")

# --- Initialization ---
load_dotenv()

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)

# Initialize Firebase only once
if not firebase_admin._apps:
    cred_path = "serviceAccountKey.json"
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        # Streamlit Cloud Secret or Env Var Fallback
        service_account_info = json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "{}"))
        if service_account_info:
             cred = credentials.Certificate(service_account_info)
        else:
             st.error("Firebase credentials not found. Please upload serviceAccountKey.json or set FIREBASE_SERVICE_ACCOUNT_JSON environment variable.")
             st.stop()
        
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://cognito-2312c-45d68-default-rtdb.firebaseio.com",
            "storageBucket": "cognito-2312c-45d68.firebasestorage.app",
        },
    )

bucket = storage.bucket()

# --- Main App UI ---
st.title("🧠 Cognito Attendance - Light Version")
st.write("Using Google MediaPipe for lightning-fast deployment and processing.")

tabs = st.tabs(["📸 Take Attendance", "📊 Admin Dashboard"])

with tabs[0]:
    st.header("Mark Attendance")
    st.write("1. Take a photo. 2. Select your name. 3. Click Mark Attendance.")
    
    # Fetch student list for the dropdown
    students_data = db.reference("Students").get()
    student_names = {}
    if students_data:
        for sid, info in students_data.items():
            student_names[f"{info.get('name')} ({sid})"] = sid

    col_cam, col_info = st.columns([2, 1])
    
    with col_cam:
        camera_image = st.camera_input("Take a picture to verify your identity")
    
    if camera_image is not None:
        # Convert the file to an opencv image.
        bytes_data = camera_image.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        
        # Process face detection
        results = face_detection.process(img_rgb)
        
        if results.detections:
            st.success(f"✅ {len(results.detections)} Face(s) Detected!")
            
            with col_info:
                st.subheader("Identify Yourself")
                selected_student_label = st.selectbox("Select your name from the list:", list(student_names.keys()))
                
                if st.button("Confirm & Mark Attendance"):
                    student_id = student_names[selected_student_label]
                    studentInfo = db.reference(f"Students/{student_id}").get()
                    
                    if studentInfo:
                        # Update attendance logic
                        last_time_str = studentInfo.get("last_attendance_time")
                        can_mark = True
                        if last_time_str:
                            try:
                                last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                                seconds_elapsed = (datetime.now() - last_time).total_seconds()
                                if seconds_elapsed < 60:
                                    can_mark = False
                                    st.warning(f"⚠️ Attendance already marked recently! Please wait.")
                            except:
                                pass
                            
                        if can_mark:
                            ref = db.reference(f"Students/{student_id}")
                            new_total = studentInfo.get("total_attendance", 0) + 1
                            ref.child("total_attendance").set(new_total)
                            ref.child("last_attendance_time").set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            st.success(f"✅ Attendance marked for {studentInfo.get('name')}!")
                            st.balloons()
                            
                            # Show profile image
                            try:
                                blob = bucket.get_blob(f"static/Files/Images/{student_id}.jpg")
                                if blob:
                                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2RGB)
                                    st.image(imgStudent, width=150)
                            except:
                                pass
        else:
            st.error("❌ No face detected. Please try again with better lighting.")

with tabs[1]:
    st.header("Admin Dashboard")
    st.write("Live synchronization with Firebase Realtime Database.")
    
    if st.button("Refresh Data"):
        st.cache_data.clear()
    
    students_ref = db.reference("Students").get()
    
    if students_ref:
        import pandas as pd
        student_list = []
        for sid, info in students_ref.items():
            info['Firebase_ID'] = sid
            student_list.append(info)
        df = pd.DataFrame(student_list)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No students found in the database.")
