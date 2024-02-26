import os
import pickle
from datetime import datetime
import cv2
import cvzone
import face_recognition
import firebase_admin
import numpy as np
from firebase_admin import credentials, db, storage

# Initialize Firebase
def initialize_firebase():
    cred = credentials.Certificate("VVDB_KEY.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://visionvoyagerdb-default-rtdb.firebaseio.com/",
        'storageBucket': "visionvoyagerdb.appspot.com/Images"
    })
    return storage.bucket()

# Load known face encodings and student IDs
def load_face_encodings():
    with open('EncodeFile.p', 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    return encodeListKnownWithIds

# Load mode images
def load_mode_images():
    folderModePath = 'Resources/Modes'
    modePathList = os.listdir(folderModePath)
    imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]
    return imgModeList

# Recognize faces in the given frame
def recognize_faces(frame, encodeListKnown):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    return face_locations, face_encodings

# Retrieve student data from Firebase
def retrieve_student_data(student_id, bucket):
    student_info = db.reference(f'Students/{student_id}').get()
    blob = bucket.get_blob(f'Images/{student_id}.png')
    if blob:
        array = np.frombuffer(blob.download_as_string(), np.uint8)
        if len(array) > 0:
            img_student = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
            return student_info, img_student
    return None, None

# Update student attendance and other data
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

# Main function to process video feed
def process_video_feed(cap, encodeListKnown, studentIds, imgModeList, bucket):
    modeType = 0
    counter = 0
    id = -1
    imgBackground = cv2.imread('Resources/backgroundV.png')

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
                        cv2.rectangle(imgBackground, (left, top), (right, bottom), (0, 255, 0),2)  # Draw green rectangle

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

# Main function to run the program
def main():
    bucket = initialize_firebase()
    encodeListKnown, studentIds = load_face_encodings()  # Capture studentIds variable here
    imgModeList = load_mode_images()

    cap = cv2.VideoCapture(1)
    cap.set(3, 640)
    cap.set(4, 480)

    process_video_feed(cap, encodeListKnown, studentIds, imgModeList, bucket)  # Pass studentIds to process_video_feed

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
