import os
import pickle
import numpy as np
import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime
import tempfile
import tkinter as tk
from PIL import Image, ImageTk

cred = credentials.Certificate("Face-Rec/VVDB_KEY.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://visionvoyagerdb-default-rtdb.firebaseio.com/",
    'storageBucket': "visionvoyagerdb.appspot.com"
})

bucket = storage.bucket()
encodeListKnown = None
studentIds = None
imgModeList=[]

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition App")

        self.camera = cv2.VideoCapture(0)
        self.is_camera_on = False

        self.camera_button = tk.Button(root, text="Toggle Camera", command=self.toggle_camera)
        self.camera_button.pack(pady=10)

        self.database_button = tk.Button(root, text="Database View", command=self.open_database_view)
        self.database_button.pack(pady=5)

        self.camera_label = tk.Label(root)
        self.camera_label.pack()

        self.update_camera()

    def toggle_camera(self):
        self.is_camera_on = not self.is_camera_on

    def open_database_view(self):
        # Implement the function to open the database view
        pass

    def update_camera(self):
        if self.is_camera_on:
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                image = ImageTk.PhotoImage(image)
                self.camera_label.config(image=image)
                self.camera_label.image = image
        self.root.after(10, self.update_camera)

def start_face_recognition_process():
    cap = cv2.VideoCapture(2)
    success, img = cap.read()
    cap.release()

    if not success:
        return {'error': 'Failed to capture image'}

    small_frame = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)

    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    recognized_ids = []
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
        name = "Unknown"

        face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            recognized_id = studentIds[best_match_index]
            recognized_ids.append(recognized_id)

    return {'recognized_ids': recognized_ids}

def recognize_face(img_array):
    global encodeListKnown, studentIds

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

def recognize_faces_from_frame(faceCurFrame, encodeCurFrame):
    global encodeListKnown, studentIds
    recognized_ids = []
    confidences = []  # Store the confidence percentage for each recognized face
    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            recognized_id = studentIds[matchIndex]
            recognized_ids.append(recognized_id)
            confidence = (1 - faceDis[matchIndex]) * 100
            confidences.append(confidence)
    return recognized_ids, confidences

def display_recognition_results(recognized_ids, imgDisplay, modeType, counter, imgModeList):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    font_color = (255, 255, 255)  # White color for text
    thickness = 2
    line_height = 35  # Space between lines

    base_x, base_y = 50, 50

    for recognized_id in recognized_ids:
        ref = db.reference(f'Students/{recognized_id}')
        student = ref.get()

        if student:
            # If the student exists in the database, retrieve the name and standing
            name = student.get('name', None)
            standing = student.get('standing', 'Unknown Standing')  # Default value if not found

            if name:
                # Get the face locations of the recognized face
                face_locations = face_recognition.face_locations(imgDisplay)
                for face_location in face_locations:
                    top, right, bottom, left = face_location
                    # Draw a green rectangle around the face
                    cv2.rectangle(imgDisplay, (left, top), (right, bottom), (0, 255, 0), cv2.FILLED)
                    # Overlay the picture of the recognized person onto the face
                    image_path = f"Face-Rec/Images/{recognized_id}.png"
                    blob = bucket.blob(image_path)
                    try:
                        with tempfile.NamedTemporaryFile(delete=False) as temp_image:
                            blob.download_to_filename(temp_image.name)
                            recognized_image = cv2.imread(temp_image.name)
                            if recognized_image is not None:
                                # Resize the image to fit the face
                                face_width = right - left
                                face_height = bottom - top
                                recognized_image_resized = cv2.resize(recognized_image, (face_width, face_height))
                                # Overlay the image onto the face
                                imgDisplay[top:bottom, left:right] = recognized_image_resized
                            os.unlink(temp_image.name)
                    except Exception as e:  # This handles any exception when downloading or processing the image
                        print(f"Error processing image for ID {recognized_id}: {e}")
                    
                    # Draw the recognized name in the lower left corner of the green box
                    text_size = cv2.getTextSize(name, font, font_scale, thickness)[0]
                    text_x = left + 10  # Offset from the left edge of the green box
                    text_y = bottom - 10  # Offset from the bottom edge of the green box
                    # Draw the green box
                    cv2.rectangle(imgDisplay, (left, bottom - text_size[1] - 20), (left + text_size[0] + 20, bottom), (0, 255, 0), cv2.FILLED)
                    # Draw the name in white font
                    cv2.putText(imgDisplay, name, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
                    break

    if not recognized_ids:
        cv2.putText(imgDisplay, "Unknown person", (base_x, base_y), font, font_scale, font_color, thickness)

def reset_mode(imgDisplay, modeType, counter, imgModeList):
    # Reset the modeType and counter if no faces are detected
    modeType = 0
    counter = 0
    return modeType, counter

def main():
    global encodeListKnown, studentIds, imgModeList  # Declare global variables

    modeType = 0
    counter = 0

    background = cv2.imread('Face-Rec/Resources/background.png')

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

        background_resized = cv2.resize(background, (640, 480))
        img_resized = cv2.resize(img, (background_resized.shape[1], background_resized.shape[0]))

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        imgDisplay = cv2.addWeighted(background_resized, 0.5, img_resized, 0.5, 0)

        if faceCurFrame:
            recognized_ids, confidences = recognize_faces_from_frame(faceCurFrame, encodeCurFrame)
            display_recognition_results(recognized_ids, imgDisplay, modeType, counter, imgModeList)
            for recognized_id, confidence in zip(recognized_ids, confidences):
                print(f"Recognized ID: {recognized_id}, Confidence: {confidence:.2f}%")
        else:
            modeType, counter = reset_mode(imgDisplay, modeType, counter, imgModeList)

        cv2.imshow("Lion Vision", imgDisplay)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Allow exiting the loop with the 'q' key
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    
    
    