import os
import pickle
import numpy as np
import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime
import tempfile

# Initialize Firebase Admin
cred = credentials.Certificate("VVDB_KEY.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://visionvoyagerdb-default-rtdb.firebaseio.com/",
    'storageBucket': "visionvoyagerdb.appspot.com"
})

# Global variables
bucket = storage.bucket()
encodeListKnown = None  # Global variable for known face encodings
studentIds = None  # Global variable for corresponding student IDs
imgModeList=[]

def start_face_recognition_process():
    # Capture a frame from the camera
    cap = cv2.VideoCapture(0)  # 0 is typically the default camera
    success, img = cap.read()
    cap.release()

    if not success:
        return {'error': 'Failed to capture image'}

    # Resize image for faster face recognition processing
    small_frame = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)

    # Find all face locations and encodings in the current frame
    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    recognized_ids = []
    for face_encoding in face_encodings:
        # See if the face is a match for known faces
        matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
        name = "Unknown"  # In case we didn't recognize the person

        # Use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            recognized_id = studentIds[best_match_index]
            recognized_ids.append(recognized_id)

    # Return information about the recognized faces
    return {'recognized_ids': recognized_ids}

# Function to recognize face from an image array
def recognize_face(img_array):
    global encodeListKnown, studentIds

    # Load the encoding file just once
    if encodeListKnown is None or studentIds is None:
        with open('Face-Rec/EncodeFile.p', 'rb') as file:
            encodeListKnownWithIds = pickle.load(file)
            encodeListKnown, studentIds = encodeListKnownWithIds

    face_locations = face_recognition.face_locations(img_array)
    face_encodings = face_recognition.face_encodings(img_array, face_locations)

    recognized_ids = []
    for encodeFace in face_encodings:
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            recognized_id = studentIds[matchIndex]
            recognized_ids.append(recognized_id)

    return recognized_ids if recognized_ids else None

def main():
    global encodeListKnown, studentIds, imgModeList  # Declare global variables

    # Initialize 'modeType' and 'counter' at the start of the function
    modeType = 0
    counter = 0

    # Load the background image
    background = cv2.imread('C:\\Users\\littl\\OneDrive\\Documents\\GitHub\\Vision-Voyager\\Face-Rec\\Resources\\overlay.jpg')

    # Initialize face encodings
    if encodeListKnown is None or studentIds is None:
        # Load face encodings from file
        with open('Face-Rec/EncodeFile.p', 'rb') as file:
            encodeListKnownWithIds = pickle.load(file)
            encodeListKnown, studentIds = encodeListKnownWithIds

    # Check if encodings were loaded correctly
    if encodeListKnown is None:
        print("Error: Known face encodings not loaded.")
        return  # Exit the function if no encodings were loaded

    # Initialize the camera and settings for face recognition
    cv2.namedWindow("Lion Vision")  # Create a named window
    cap = cv2.VideoCapture(0)  # Use the default camera
    cap.set(3, 640)  # Set the width
    cap.set(4, 480)  # Set the height

    # Main loop for processing video frames
    while cv2.getWindowProperty("Lion Vision", 0) >= 0:  # Check if the window is still open
        success, img = cap.read()
        if not success:
            continue  # Skip the rest of the loop if no image was captured

        # Resize the background image to match the camera frame size
        background_resized = cv2.resize(background, (640, 480))

        # Resize the image for faster face recognition processing
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        # Overlay the camera frame on top of the resized background
        imgDisplay = cv2.addWeighted(background_resized, 0.5, img, 0.5, 0)

        # Handle face recognition results
        if faceCurFrame:
            recognized_ids = recognize_faces_from_frame(faceCurFrame, encodeCurFrame)
            display_recognition_results(recognized_ids, imgDisplay, modeType, counter, imgModeList)
        else:
            modeType, counter = reset_mode(imgDisplay, modeType, counter, imgModeList)

        # Display the resulting frame with any UI updates
        cv2.imshow("Lion Vision", imgDisplay)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Allow exiting the loop with the 'q' key
            break

    # Clean up: release the camera and close all windows
    cap.release()
    cv2.destroyAllWindows()


def recognize_faces_from_frame(faceCurFrame, encodeCurFrame):
    global encodeListKnown, studentIds
    recognized_ids = []
    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            recognized_id = studentIds[matchIndex]
            recognized_ids.append(recognized_id)
    return recognized_ids


def display_recognition_results(recognized_ids, imgDisplay, modeType, counter, imgModeList):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    font_color = (255, 255, 255)  # White color for text
    thickness = 2
    line_height = 35  # Space between lines

    if recognized_ids:
        for recognized_id in recognized_ids:
            # Reference to the student in the Firebase Realtime Database
            ref = db.reference(f'Students/{recognized_id}')
            student = ref.get()

            if student:
                name = student.get('name', "Unknown")
                standing = student.get('standing', 'Unknown Standing')

                # Display the name and standing of the recognized person
                cv2.putText(imgDisplay, f"Name: {name}", (10, 50), font, font_scale, font_color, thickness)
                cv2.putText(imgDisplay, f"Standing: {standing}", (10, 90), font, font_scale, font_color, thickness)
            else:
                # Display "Unknown person" if the student ID is not found in the database
                cv2.putText(imgDisplay, "Unknown person", (10, 50), font, font_scale, font_color, thickness)
    else:
        # Display "Unknown person" if no faces are recognized
        cv2.putText(imgDisplay, "Unknown person", (10, 50), font, font_scale, font_color, thickness)



def reset_mode(imgDisplay, modeType, counter, imgModeList):
    # Reset the modeType and counter if no faces are detected
    modeType = 0
    counter = 0
    return modeType, counter

if __name__ == "__main__":
    main()
