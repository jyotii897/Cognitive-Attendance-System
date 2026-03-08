import streamlit as st
import cv2
import pickle
import face_recognition
import numpy as np
from datetime import datetime
import json
import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

# --- Streamlit Page Config ---
st.set_page_config(page_title="Cognito Attendance", page_icon="🧠", layout="wide")

# --- Initialization ---
load_dotenv()

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

@st.cache_data
def load_encodings():
    try:
        with open("EncodeFile.p", "rb") as file:
            encodeListKnownWithIds = pickle.load(file)
        return encodeListKnownWithIds[0], encodeListKnownWithIds[1]
    except FileNotFoundError:
        st.error("Encoding file not found. Please ensure 'EncodeFile.p' exists in the main directory.")
        return [], []

encodedFaceKnown, studentIDs = load_encodings()

# --- Main App UI ---
st.title("🧠 Cognito Face Recognition Attendance")
st.write("Streamlit Cloud Compatible Version - Using Web Camera Snapshot for processing.")

tabs = st.tabs(["📸 Take Attendance", "📊 Admin Dashboard"])

with tabs[0]:
    st.header("Mark Attendance")
    st.write("Click 'Take Photo' to scan your face and log attendance on Firebase.")
    camera_image = st.camera_input("Take a picture to mark attendance")
    
    if camera_image is not None:
        # Convert the file to an opencv image.
        bytes_data = camera_image.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Resize for faster processing
        imgSmall = cv2.resize(cv2_img, (0, 0), None, 0.25, 0.25)
        # Convert BGR to RGB
        imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)
        
        faceCurrentFrame = face_recognition.face_locations(imgSmall)
        encodeCurrentFrame = face_recognition.face_encodings(imgSmall, faceCurrentFrame)
        
        if faceCurrentFrame:
            st.success("Face Detected! Processing database match...")
            for encodeFace, faceLocation in zip(encodeCurrentFrame, faceCurrentFrame):
                # Verify we actually have loaded encodings
                if len(encodedFaceKnown) == 0:
                    st.error("Cannot perform matching - no face database loaded.")
                    break
                    
                matches = face_recognition.compare_faces(encodedFaceKnown, encodeFace)
                faceDistance = face_recognition.face_distance(encodedFaceKnown, encodeFace)
                
                matchIndex = np.argmin(faceDistance)
                
                if matches[matchIndex]:
                    id = studentIDs[matchIndex]
                    
                    studentInfo = db.reference(f"Students/{id}").get()
                    if studentInfo:
                        # Display student details in a card-like layout
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            try:
                                blob = bucket.get_blob(f"static/Files/Images/{id}.jpg")
                                if blob:
                                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2RGB)
                                    st.image(imgStudent, width=200, caption=f"ID: {id}")
                            except Exception as e:
                                st.warning("Could not load profile image from Firebase.")
                        
                        with col2:
                            st.subheader(f"{studentInfo.get('name')}")
                            st.markdown(f"**Major:** {studentInfo.get('major')}")
                            st.markdown(f"**Standing:** {studentInfo.get('standing', 'N/A')}")
                            st.markdown(f"**Total Attendance:** {studentInfo.get('total_attendance', 0)}")
                            
                        # Update attendance logic
                        last_time_str = studentInfo.get("last_attendance_time")
                        if last_time_str:
                            try:
                                last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                                seconds_elapsed = (datetime.now() - last_time).total_seconds()
                            except ValueError:
                                # Fallback if time format is unexpected
                                seconds_elapsed = 9999
                        else:
                            seconds_elapsed = 9999
                            
                        if seconds_elapsed > 60:
                            ref = db.reference(f"Students/{id}")
                            new_total = studentInfo.get("total_attendance", 0) + 1
                            ref.child("total_attendance").set(new_total)
                            ref.child("last_attendance_time").set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            st.success(f"✅ Attendance marked successfully! Total records: {new_total}")
                            st.balloons()
                        else:
                            st.warning(f"⚠️ Attendance already marked recently! Please wait before scanning again.")
                else:
                    st.error("Face not recognized in the database.")
        else:
            st.error("No face detected in the image.")

with tabs[1]:
    st.header("Admin Dashboard")
    st.write("Live synchronization with Firebase Realtime Database.")
    
    if st.button("Refresh Data"):
        st.cache_data.clear() # clear any cached data if needed
    
    students_ref = db.reference("Students").get()
    
    if students_ref:
        import pandas as pd
        
        # Convert Firebase Dictionary to List of Dicts
        student_list = []
        for sid, info in students_ref.items():
            # Include Firebase ID explicitly just in case 'id' key isn't consistently available
            info['Firebase_ID'] = sid
            student_list.append(info)
            
        df = pd.DataFrame(student_list)
        
        # Display the data nicely
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No students found in the database.")
