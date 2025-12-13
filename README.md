# 🧠 Cognito - Intelligent Attendance System

![Python-3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3.2-black?logo=flask&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Realtime_DB_&_Storage-orange?logo=firebase&logoColor=white)
![OpenCV](https://img.shields.io/badge/CV-OpenCV_&_Dlib-green?logo=opencv&logoColor=white)

**Cognito** is a cutting-edge, real-time facial recognition attendance system designed to streamline academic and corporate attendance tracking. Built with Python and Flask, it leverages powerful computer vision libraries to detect, recognize, and log attendance instantly to a cloud-based Firebase backend.

---

## 📸 Dashboard Preview

![Dashboard Wireframe](docs/images/dashboard_wireframe.png)

*Conceptual wireframe of the admin interface.*

---

## 🏗️ System Architecture

The system follows a modular architecture integrating local processing with cloud data management.

```mermaid
graph TD
    subgraph Client System
    A[Student] -->|Walks Past| B(Webcam Input)
    B --> C{Face Detection}
    C -->|Face Found| D[Encoding Generator]
    D -->|128-d Embedding| E[Face Matcher]
    end

    subgraph "Local Resources"
        F[(Pickle Database)] -->|Load Known Encodings| E
    end

    subgraph "Cloud Backend Integration (Firebase)"
        E -- Match Confirmed --> G[Attendance Logger]
        G -->|Update time| H[(Realtime Database)]
        G -->|Fetch Profile Img| I[(Firebase Storage)]
        J[Admin Dashboard] -->|Read/Write| H
        J -->|Upload New Profiles| I
        J -->|Manage/Delete| H
    end

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#ffae42,stroke:#f66,stroke-width:2px
    style I fill:#ffae42,stroke:#f66,stroke-width:2px
```

---

## ✨ Key Features

- **Real-Time Recognition**: Identifies registered users in milliseconds using `dlib` state-of-the-art face recognition.
- **Live Attendance Logging**: Automatically updates check-in times in **Firebase Realtime Database**.
- **Wait-Time Logic**: Smart "elapsed time" calculation prevents duplicate entries within a set timeframe.
- **Admin Dashboard**:
    - **Take Attendance**: Live video feed with overlay graphics for recognition status.
    - **Add Students**: Easy interface to register new users (ID, Name, Major).
    - **Attendance List**: View and download daily attendance logs as CSV.
- **Cloud Storage**: Student profile images are securely stored and retrieved from **Firebase Storage**.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | ![Flask](https://img.shields.io/badge/-Flask-000?style=flat-square&logo=flask) | Lightweight WSGI web application framework. |
| **Vision** | ![OpenCV](https://img.shields.io/badge/-OpenCV-5C3EE8?style=flat-square&logo=opencv) | Real-time computer vision processing. |
| **AI/ML** | `face_recognition`, `dlib` | Deep metric learning for face encoding. |
| **Database** | ![Firebase](https://img.shields.io/badge/-Firebase-FFCA28?style=flat-square&logo=firebase) | NoSQL cloud database for real-time syncing. |
| **Frontend** | HTML5, CSS3, JavaScript | Responsive admin interface. |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ (Tested with 3.13)
- A generic USB Webcam

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/architpr/Cognito-attendance-System.git
    cd Cognito-attendance-System
    ```

2.  **Create & Activate Virtual Environment** (Recommended)
    ```powershell
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**
    > **Note**: `dlib` can be tricky on Windows. If `pip install dlib` fails, download a pre-compiled wheel (e.g., from [cp313-win_amd64](https://github.com/z-mahmud22/Dlib_Windows_Python3.x/)) or install CMake and Visual Studio build tools first.
    ```bash
    pip install -r requirements_no_version.txt
    ```

4.  **Firebase Setup**
    - Create a Firebase Project.
    - Enable **Realtime Database** and **Storage**.
    - Download your `serviceAccountKey.json` from Firebase Console -> Project Settings -> Service Accounts.
    - Place `serviceAccountKey.json` in the root directory.

5.  **Run the Application**
    ```bash
    python app.py
    ```
    Access the dashboard at `http://127.0.0.1:5000`.

---

## 📂 Project Structure

```bash
📂 Cognito-attendance-System
├── 📂 static/              # CSS, JS, and Assets
│   └── 📂 Files/           # Generated/Uploaded Resources
├── 📂 templates/           # HTML Templates (Admin, Login, etc.)
├── app.py                  # Main Flask Application
├── EncodeGenerator.py      # Script to generate encodings
├── database_actions.py     # Database helper functions
└── requirements.txt        # Dependencies
```

## 🤝 Contributing

Contributions are welcome! Please fork this repository and submit a pull request.

---
*Built with ❤️ by the Cognito Team*
