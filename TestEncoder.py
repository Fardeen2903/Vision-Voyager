import os
import pickle
import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import unittest

class FaceEncodingTest(unittest.TestCase):
    def setUp(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate("Face-Rec/VVDB_KEY.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': "https://visionvoyagerdb-default-rtdb.firebaseio.com/",
                'storageBucket': "visionvoyagerdb.appspot.com"
            })
        self.folderPath = 'Face-Rec/Images'

    def test_find_encodings(self):
        imgList = []
        studentIds = []
        pathList = os.listdir(self.folderPath)
        for path in pathList:
            img = cv2.imread(os.path.join(self.folderPath, path))
            if img is not None:
                imgList.append(img)
                studentIds.append(os.path.splitext(path)[0])
        encodeListKnown = self.find_encodings(imgList)
        self.assertEqual(len(imgList), len(encodeListKnown))

    def test_read_images(self):
        pathList = os.listdir(self.folderPath)
        self.assertTrue(len(pathList) > 0, "No images found in the specified folder path")
        for path in pathList:
            img = cv2.imread(os.path.join(self.folderPath, path))
            self.assertIsNotNone(img, f"Failed to read image: {path}")

    def test_encode_faces(self):
        pathList = os.listdir(self.folderPath)
        imgList = [cv2.imread(os.path.join(self.folderPath, path)) for path in pathList]
        encodeListKnown = self.find_encodings(imgList)
        self.assertTrue(len(encodeListKnown) > 0, "No face encodings generated")

    def find_encodings(self, imagesList):
        encodeList = []
        for img in imagesList:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(img)
            if face_encodings:
                encodeList.append(face_encodings[0])
        return encodeList

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
