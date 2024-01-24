import threading
import cv2
from deepface import DeepFace

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

counter = 0
face_match = False
reference_img = cv2.imread("reference.jpg")
print("Reference image loaded.")

# Load Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def check_face(frame):
    global face_match
    try:
        print("Checking face...")
        # Convert the frame to grayscale for face detection
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the frame
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            # Crop the face region for verification
            face_roi = frame[y:y + h, x:x + w]

            # Verify the cropped face
            result = DeepFace.verify(face_roi, reference_img.copy(), enforce_detection=False)

            print("Face checked.")
            print("Result:", result)

            if result['verified']:
                face_match = True
                break
            else:
                face_match = False
    except ValueError as e:
        print(f"Error: {e}")


while True:
    ret, frame = cap.read()

    if ret:
        if counter % 30 == 0:
            try:
                threading.Thread(target=check_face, args=(frame.copy(),)).start()
            except ValueError as e:
                print(f"Error: {e}")
        counter += 1

        if face_match:
            cv2.putText(frame, "MATCH", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            print("MATCH")
        else:
            cv2.putText(frame, "NO MATCH", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
            print(" NO MATCH")

        cv2.imshow("video", frame)

        key = cv2.waitKey(1)
        if key == ord("q"):
            break

# Release the video capture resource
cap.release()

# Close all windows
cv2.destroyAllWindows()

