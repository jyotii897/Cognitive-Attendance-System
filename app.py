from flask import Flask, render_template, Response, redirect, url_for, request
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- MOCKING LOGIC START ---
MOCK_MODE = False

try:
    import cv2
    import face_recognition
    import numpy as np
    import cvzone
    import pickle
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import db
    from firebase_admin import storage
    
    # Check for service key
    if not os.path.exists("serviceAccountKey.json"):
        raise ImportError("serviceAccountKey.json missing")

except ImportError as e:
    print(f"⚠️  MISSING DEPENDENCY OR KEY: {e}")
    print("⚠️  SWITCHING TO MOCK MODE. Functionality will be limited.")
    MOCK_MODE = True
    import random
    import time
    
    # Mock Objects
    class MockCV2:
        CAP_PROP_FRAME_WIDTH = 3
        CAP_PROP_FRAME_HEIGHT = 4
        COLOR_BGR2RGB = 1
        COLOR_BGRA2BGR = 2
        FONT_HERSHEY_COMPLEX = 1
        
        def VideoCapture(self, idx): return self
        def set(self, prop, val): pass
        def read(self): 
            # Return a dummy black frame
            return True, np.zeros((480, 640, 3), dtype=np.uint8)
        def imread(self, path):
             return np.zeros((720, 1280, 3), dtype=np.uint8) # Dummy background
        def resize(self, img, dim, fx=0, fy=0): return img
        def cvtColor(self, img, code): return img
        def imencode(self, ext, img): return True, np.array([0]) # Returns short byte array
        def putText(self, *args): pass
        def waitKey(self, delay): pass
        def getTextSize(self, text, font, scale, thick): return ((0,0), 0)
        def imdecode(self, buf, flags): return np.zeros((216, 216, 3), dtype=np.uint8)

    class MockNP:
        uint8 = 'uint8'
        def argmin(self, a): return 0
        def zeros(self, shape, dtype): return [ [ [0]*3 ] * shape[1] ] * shape[0] # Very crude list-based fake if needed, but we used real np if avail.
        def frombuffer(self, b, dtype): return b 
        def array(self, a): return a

    # Try to keep numpy if available, otherwise mock it (unlikely numpy is missing if installed via reqs)
    try:
        import numpy as np
    except:
        np = MockNP()

    cv2 = MockCV2()
    
    class MockCVZone:
        def cornerRect(self, img, bbox, rt=0): return img
        def putTextRect(self, img, text, pos, thickness=1): return img
    
    cvzone = MockCVZone()
    
    class MockFaceRec:
        def face_locations(self, img): return []
        def face_encodings(self, img, locs): return []
        def compare_faces(self, known, check): return [False]
        def face_distance(self, known, check): return [1.0]
        
    face_recognition = MockFaceRec()

    # Mock Firebase
    class MockDB:
        def reference(self, path): return self
        def get(self): 
            # Return dummy student info
            return {
                "name": "Jyoti (Mock)",
                "major": "Computer Science",
                "starting_year": 2021,
                "total_attendance": 10,
                "standing": "Good",
                "year": 3,
                "last_attendance_time": "2024-01-01 12:00:00"
            }
        def child(self, path): return self
        def set(self, data): print(f"Mock DB Set: {data}")
        def update(self, data): print(f"Mock DB Update: {data}")
        def delete(self): print("Mock DB Delete")

    class MockStorage:
        def bucket(self, name=None): return self
        def get_blob(self, path): return self
        def blob(self, path): return self
        def download_as_string(self): return b'' # Empty bytes
        def upload_from_filename(self, filename): print(f"Mock Upload: {filename}")
        def delete(self): print("Mock Delete")

    db = MockDB()
    storage = MockStorage()
    firebase_admin = None # Just to act as flag

# --- MOCKING LOGIC END ---

app = Flask(__name__)

if not MOCK_MODE:
    # database credentials
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://cognito-2312c.firebaseio.com/",
            "storageBucket": "cognito-2312c.firebasestorage.app",
        },
    )
    bucket = storage.bucket()


def dataset(id):
    if MOCK_MODE:
        # Return static dummy data for demo
        return {
            "name": f"Mock Student {id}",
            "major": "AI Engineering",
            "starting_year": 2023,
            "total_attendance": 5,
            "standing": "Excellent",
            "year": 2,
            "last_attendance_time": "2024-12-24 10:00:00"
        }, np.zeros((216, 216, 3), dtype=np.uint8), 0
        
    studentInfo = db.reference(f"Students/{id}").get()
    if studentInfo is not None:
        blob = bucket.get_blob(f"static/Files/Images/{id}.jpg")
        if blob is not None:
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
            if studentInfo["last_attendance_time"] is not None:
                datetimeObject = datetime.strptime(studentInfo["last_attendance_time"], "%Y-%m-%d %H:%M:%S")
                secondElapsed = (datetime.now() - datetimeObject).total_seconds()
            else:
                datetimeObject = None
                secondElapsed = None
            return studentInfo, imgStudent, secondElapsed
    return None


already_marked_id_student = []
already_marked_id_admin = []


def generate_frame():
    if MOCK_MODE:
        # Generate a dummy video feed with a message
        while True:
            # Create black image
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add text
            cv2.putText(frame, "MOCK MODE - NO WEBCAM/DB", (50, 240), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            
            # Encode
            ret, buffer = cv2.imencode(".jpg", frame)
            # Use a real buffer if our mock failed, or just bytes
            if isinstance(buffer, np.ndarray):
                frame_bytes = buffer.tobytes()
            else:
                # Fallback if mock is too simple
                frame_bytes = b'' 
                
            yield (b"--frame\r\n" b"Content-Type: image/jpeg \r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(0.1)
        return

    # Original Logic
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    imgBackground = cv2.imread("static/Files/Resources/background.png")

    folderModePath = "static/Files/Resources/Modes/"
    modePathList = os.listdir(folderModePath)
    imgModeList = []

    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

    modeType = 0
    id = -1
    imgStudent = []
    counter = 0

    file = open("EncodeFile.p", "rb")
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodedFaceKnown, studentIDs = encodeListKnownWithIds

    while True:
        success, img = capture.read()

        if not success:
            break
        else:
            imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

            faceCurrentFrame = face_recognition.face_locations(imgSmall)
            encodeCurrentFrame = face_recognition.face_encodings(
                imgSmall, faceCurrentFrame
            )

            imgBackground[162 : 162 + 480, 55 : 55 + 640] = img
            imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[modeType]

            if faceCurrentFrame:
                for encodeFace, faceLocation in zip(
                    encodeCurrentFrame, faceCurrentFrame
                ):
                    matches = face_recognition.compare_faces(
                        encodedFaceKnown, encodeFace
                    )
                    faceDistance = face_recognition.face_distance(
                        encodedFaceKnown, encodeFace
                    )

                    matchIndex = np.argmin(faceDistance)

                    y1, x2, y2, x1 = faceLocation
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                    if matches[matchIndex] == True:
                        id = studentIDs[matchIndex]

                        if counter == 0:
                            cvzone.putTextRect(
                                imgBackground, "Face Detected", (65, 200), thickness=2
                            )
                            cv2.waitKey(1)
                            counter = 1
                            modeType = 1
                    else:
                        cvzone.putTextRect(
                            imgBackground, "Face Detected", (65, 200), thickness=2
                        )
                        cv2.waitKey(3)
                        cvzone.putTextRect(
                            imgBackground, "Face Not Found", (65, 200), thickness=2
                        )
                        modeType = 4
                        counter = 0
                        imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[
                            modeType
                        ]

                if counter != 0:
                    if counter == 1:
                        studentInfo, imgStudent, secondElapsed = dataset(id)
                        if secondElapsed > 60:
                            ref = db.reference(f"Students/{id}")
                            studentInfo["total_attendance"] += 1
                            ref.child("total_attendance").set(
                                studentInfo["total_attendance"]
                            )
                            ref.child("last_attendance_time").set(
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                        else:
                            modeType = 3
                            counter = 0
                            imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[
                                modeType
                            ]

                            already_marked_id_student.append(id)
                            already_marked_id_admin.append(id)

                    if modeType != 3:
                        if 5 < counter <= 10:
                            modeType = 2

                        imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[
                            modeType
                        ]

                        if counter <= 5:
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["total_attendance"]),
                                (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX,
                                1,
                                (255, 255, 255),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["major"]),
                                (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.5,
                                (255, 255, 255),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(id),
                                (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.5,
                                (255, 255, 255),
                                1,
                            )
                            standing = studentInfo.get("standing", "N/A")
                            cv2.putText(
                                imgBackground,
                                str(standing),
                                (910, 625),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.6,
                                (100, 100, 100),
                                1,
                            )
                            
                            

                            (w, h), _ = cv2.getTextSize(
                                str(studentInfo["name"]), cv2.FONT_HERSHEY_COMPLEX, 1, 1
                            )

                            offset = (414 - w) // 2
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["name"]),
                                (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX,
                                1,
                                (50, 50, 50),
                                1,
                            )

                            imgStudentResize = cv2.resize(imgStudent, (216, 216))

                            imgBackground[
                                175 : 175 + 216, 909 : 909 + 216
                            ] = imgStudentResize

                        counter += 1

                        if counter >= 10:
                            counter = 0
                            modeType = 0
                            studentInfo = []
                            imgStudent = []
                            imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[
                                modeType
                            ]

            else:
                modeType = 0
                counter = 0

            ret, buffer = cv2.imencode(".jpeg", imgBackground)
            frame = buffer.tobytes()

        yield (b"--frame\r\n" b"Content-Type: image/jpeg \r\n\r\n" + frame + b"\r\n")


#########################################################################################################################


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video")
def video():
    return Response(
        generate_frame(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route('/loginspage.html')
def login():
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY", "mock-key"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "mock-domain"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", "mock-id"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "mock-bucket"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "mock-sender"),
        "appId": os.getenv("FIREBASE_APP_ID", "mock-app-id"),
        "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "mock-measurement-id")
    }
    return render_template('loginspage.html', firebase_config=firebase_config)

@app.route('/signup.html')
def signup():
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY", "mock-key"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "mock-domain"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", "mock-id"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "mock-bucket"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "mock-sender"),
        "appId": os.getenv("FIREBASE_APP_ID", "mock-app-id"),
        "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "mock-measurement-id")
    }
    return render_template('signup.html', firebase_config=firebase_config)

@app.route('/aboutus.html')
def aboutus():
    return render_template('aboutus.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/home.html')
def home():
    return render_template('home.html')


#########################################################################################################################


@app.route("/admin")
def admin():
    if MOCK_MODE:
        return render_template("admin.html", data=[({
            "id": "123", "name": "Jyoti (Mock)", "major": "CS", "total_attendance": 10, "last_attendance_time": "Now"
        }, None, None)])
        
    all_student_info = []
    studentIDs, _ = add_image_database()
    for i in studentIDs:
        student_info = dataset(i)
        if student_info is not None:
            all_student_info.append(student_info)
    return render_template("admin.html", data=all_student_info)


@app.route("/admin/admin_attendance_list", methods=["GET", "POST"])
def admin_attendance_list():
    if MOCK_MODE:
        return render_template("admin_attendance_list.html", data=[({
            "id": "123", "name": "Jyoti (Mock)", "major": "CS", "total_attendance": 10, "last_attendance_time": "Now"
        }, None, 0)])

    if request.method == "POST":
        if request.form.get("button_student") == "VALUE1":
            already_marked_id_student.clear()
            return redirect(url_for("admin_attendance_list"))
        else:
            request.form.get("button_admin") == "VALUE2"
            already_marked_id_admin.clear()
            return redirect(url_for("admin_attendance_list"))
    else:
        unique_id_admin = list(set(already_marked_id_admin))
        student_info = []
        for i in unique_id_admin:
            student_info.append(dataset(i))
        return render_template("admin_attendance_list.html", data=student_info)



#########################################################################################################################

def add_image_database():
    if MOCK_MODE:
        return [], []
        
    folderPath = "static/Files/Images"
    imgPathList = os.listdir(folderPath)
    imgList = []
    studentIDs = []

    for path in imgPathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        studentIDs.append(os.path.splitext(path)[0])

        fileName = f"{folderPath}/{path}"
        bucket = storage.bucket("cognito-2312c.firebasestorage.app")
        blob = bucket.blob(fileName)
        blob.upload_from_filename(fileName)

    return studentIDs, imgList


def findEncodings(images):
    if MOCK_MODE:
        return []
        
    encodeList = []

    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList


@app.route("/admin/add_user", methods=["GET", "POST"])
def add_user():
    if MOCK_MODE:
         return render_template("add_user.html")
         
    id = request.form.get("id", False)
    name = request.form.get("name", False)
    password = request.form.get("password", False)
    major = request.form.get("major", False)
    total_attendance = request.form.get("total_attendance", False)
    
    last_attendance_date = request.form.get("last_attendance_date", False)
    last_attendance_time = request.form.get("last_attendance_time", False)
    

    
    last_attendance_datetime = f"{last_attendance_date} {last_attendance_time}"
    
    total_attendance = int(total_attendance)
     

    if request.method == "POST":
        image = request.files["image"]
        filename = f"{'static/Files/Images'}/{id}.jpg"
        image.save(os.path.join(filename))

    studentIDs, imgList = add_image_database()

    encodeListKnown = findEncodings(imgList)

    encodeListKnownWithIds = [encodeListKnown, studentIDs]

    file = open("EncodeFile.p", "wb")
    pickle.dump(encodeListKnownWithIds, file)
    file.close()

    if id:
        add_student = db.reference(f"Students")

        add_student.child(id).set(
            {
                "id": id,
                "name": name,
                "password": password,
                "major": major,
                "total_attendance": total_attendance,
                "last_attendance_time": last_attendance_datetime,
            }
        )

    return render_template("add_user.html")


#########################################################################################################################


@app.route("/admin/edit_user", methods=["POST", "GET"])
def edit_user():
    if MOCK_MODE:
         return render_template("edit_user.html", data={
            "studentInfo": {"name": "Test"}, "lastlogin": 0, "image": None
         })
         
    value = request.form.get("edit_student")

    studentInfo, imgStudent, secondElapsed = dataset(value)
    hoursElapsed = round((secondElapsed / 3600), 2)

    info = {
        "studentInfo": studentInfo,
        "lastlogin": hoursElapsed,
        "image": imgStudent,
    }

    return render_template("edit_user.html", data=info)


#########################################################################################################################


@app.route("/admin/save_changes", methods=["POST", "GET"])
def save_changes():
    if MOCK_MODE:
        return "Data received successfully! (MOCKED)"
        
    content = request.get_data()

    dic_data = json.loads(content.decode("utf-8"))

    dic_data = {k: v.strip() for k, v in dic_data.items()}

    dic_data["year"] = int(dic_data["year"])
    dic_data["total_attendance"] = int(dic_data["total_attendance"])
    dic_data["starting_year"] = int(dic_data["starting_year"])

    update_student = db.reference(f"Students")

    update_student.child(dic_data["id"]).update(
        {
            "id": dic_data["id"],
            "name": dic_data["name"],
            "major": dic_data["major"],
            "total_attendance": dic_data["total_attendance"],
            "last_attendance_time": dic_data["last_attendance_time"],
        }
    )

    return "Data received successfully!"


#########################################################################################################################


def delete_image(student_id):
    if MOCK_MODE: return "Successful"
    
    filepath = f"static/Files/Images/{student_id}.jpg"

    os.remove(filepath)

    bucket = storage.bucket()
    blob = bucket.blob(filepath)
    blob.delete()

    return "Successful"


@app.route("/admin/delete_user", methods=["POST", "GET"])
def delete_user():
    if MOCK_MODE: return "Successful"
    
    content = request.get_data()

    student_id = json.loads(content.decode("utf-8"))

    delete_student = db.reference(f"Students")
    delete_student.child(student_id).delete()

    delete_image(student_id)

    studentIDs, imgList = add_image_database()

    encodeListKnown = findEncodings(imgList)

    encodeListKnownWithIds = [encodeListKnown, studentIDs]

    file = open("EncodeFile.p", "wb")
    pickle.dump(encodeListKnownWithIds, file)
    file.close()

    return "Successful"


#########################################################################################################################
if __name__ == "__main__":
    
    app.run(debug=True)
