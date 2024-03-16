import os
import pickle
from datetime import datetime
import cv2
import cvzone
import face_recognition
import firebase_admin
import numpy as np
from firebase_admin import credentials, db, storage
import torch

# Function to initialize Firebase
def initialize_firebase():
    cred = credentials.Certificate("VVDB_KEY.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://visionvoyagerdb-default-rtdb.firebaseio.com/",
        'storageBucket': "visionvoyagerdb.appspot.com/Images"
    })
    return storage.bucket()

# Function to load face encodings from a pickle file
def load_face_encodings():
    with open('EncodeFile.p', 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    return encodeListKnownWithIds

# Function to load mode images
def load_mode_images():
    folderModePath = 'Resources/Modes'
    modePathList = os.listdir(folderModePath)
    imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]
    return imgModeList

# Function to process a single frame
def process_frame(frame, encodeListKnown, bucket):
    modeType = 0
    counter = 0
    id = -1
    imgBackground = cv2.imread('Resources/background.png')

    # Resize the frame to a smaller resolution
    frame = cv2.resize(frame, (640, 480))

    face_locations, face_encodings = recognize_faces(frame, encodeListKnown)
    return imgBackground  # Return the processed frame

# Main function to process video feed
def process_video_feed(cap, encodeListKnown, studentIds, imgModeList, bucket):
    modeType = 0
    counter = 0
    id = -1
    imgBackground = cv2.imread('Resources/background.png')

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    while True:
        success, img = cap.read()
        if not success or img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        face_locations, face_encodings = recognize_faces(img, encodeListKnown)

        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if face_locations:
            for encodeFace, faceLoc in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    id = studentIds[matchIndex]

                    if counter == 0:
                        cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                        counter = 1
                        modeType = 1

                        # Draw rectangle around the detected face
                        top, right, bottom, left = faceLoc

                        # Adjust rectangle size with a scaling factor
                        scale_factor = 0.8
                        box_width = int((right - left) * scale_factor)
                        box_height = int((bottom - top) * scale_factor)

                        # Calculate new coordinates for the smaller rectangle
                        new_top = top + int((bottom - top) * (1 - scale_factor) / 2)
                        new_right = left + box_width
                        new_bottom = new_top + box_height
                        new_left = left

                        # Draw the smaller rectangle
                        cv2.rectangle(imgBackground, (new_left, new_top), (new_right, new_bottom), (0, 255, 0),
                                      2)  # Draw green rectangle

            if counter != 0:
                if counter == 1:
                    student_info, img_student = retrieve_student_data(id, bucket)
                    if student_info and img_student:
                        if not update_student_data(student_info, id):
                            modeType = 3
                            counter = 0
                            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if modeType != 3 and isinstance(img_student, np.ndarray) and img_student.size != 0:
                    if 10 < counter < 20:
                        modeType = 2

                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        # Display student information on the background
                        student_name = student_info['name']
                        student_id = student_info['student_id']

                        # Define text to be displayed
                        text = f"Name: {student_name}, ID: {student_id}"

                        # Calculate text position
                        text_position = (50, 50)  # Adjust position as needed

                        # Draw text on the background image
                        cv2.putText(imgBackground, text, text_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                        pass  # Add your code here

                    counter += 1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        else:
            modeType = 0
            counter = 0

        cv2.imshow("Face Attendance", imgBackground)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Function to recognize faces in a frame
def recognize_faces(frame, encodeListKnown):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    return face_locations, face_encodings

# Function to retrieve student data from Firebase storage
def retrieve_student_data(student_id, bucket):
    student_info = db.reference(f'Students/{student_id}').get()
    blob = bucket.get_blob(f'Images/{student_id}.png')
    if blob:
        array = np.frombuffer(blob.download_as_string(), np.uint8)
        if len(array) > 0:
            img_student = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
            return student_info, img_student
    return None, None

def update_student_data(student_info, id):
    datetimeObject = datetime.strptime(student_info['last_tracked_time'], "%Y-%m-%d %H:%M:%S")
    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
    if secondsElapsed > 30:
        ref = db.reference(f'Students/{id}')
        student_info['total_attendance'] += 1
        ref.child('total_attendance').set(student_info['total_attendance'])
        ref.child('last_tracked_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    else:
        return False
    return True

def detect_objects(image):
    # Load YOLOv5 model
    model = torch.load('C:\Users\Jarvis\Documents\GitHub\Vision-Voyager\yolov5\models\yolov5l.yaml')

    # Perform object detection
    results = model(image)
    return results

def load_mode_images():
    folderModePath = 'Resources/Modes'
    modePathList = os.listdir(folderModePath)
    imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]
    return imgModeList

def detect_objects(image):
    # Load YOLOv5 model
    model = torch.load('yolov5s.pt')

    # Perform object detection
    results = model(image)
    return results
def process_video_feed_with_yolov5(cap, encodeListKnown, studentIds, imgModeList, bucket):
    # Initialize YOLOv5 model here

    while True:
        success, img = cap.read()
        if not success or img is None:
            continue

        # Perform object detection
        results = detect_objects(img)

        # Process detection results and integrate into your application logic

        # Display the processed frame
        cv2.imshow("Object Detection", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
def main_with_yolov5():
    bucket = initialize_firebase()
    encodeListKnown, studentIds = load_face_encodings()  # Capture studentIds variable here
    imgModeList = load_mode_images()

    cap = cv2.VideoCapture(1)
    cap.set(3, 640)
    cap.set(4, 480)

    process_video_feed_with_yolov5(cap, encodeListKnown, studentIds, imgModeList, bucket)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main_with_yolov5()