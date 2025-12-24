# Implementation Plan - Mocking & Run

## Goal
Run the Cognito Attendance System with **mocked dependencies** to bypass installation errors and missing credentials, allowing the user to view the UI.

## Process
I will modify `app.py` to gracefully handle missing imports for `face_recognition`, `dlib`, `cvzone`, and `firebase_admin`.

## Proposed Changes

### [MODIFY] [app.py](file:///c:/Users/rayjy/New%20folder%20%286%29/Cognito-attendance-System/app.py)
-   **Import Guards**: Wrap `cv2`, `face_recognition`, `cvzone`, `firebase_admin` imports in try/except blocks.
-   **Mock Classes**: Create dummy classes (e.g., `MockCV2`, `MockFirebase`) that log calls instead of crashing.
    -   `MockCV2`: Return black frames for video capture.
    -   `MockFirebase`: Return dummy student data for database calls.
-   **Bypass Auth**: Skip the `serviceAccountKey.json` check.

## Verification
1.  **Run Application**: `python app.py` should start without errors.
2.  **UI Check**: Visit `http://127.0.0.1:5000` to see the dashboard.
