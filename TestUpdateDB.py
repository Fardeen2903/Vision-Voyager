import unittest
import firebase_admin
from firebase_admin import db, credentials

class TestFirebaseData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cred = credentials.Certificate("Face-Rec/VVDB_KEY.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://visionvoyagerdb-default-rtdb.firebaseio.com/"
        })

    @classmethod
    def tearDownClass(cls):
        ref = db.reference('Students')
        ref.delete()

    def test_data_insertion(self):
        ref = db.reference('Students')
        data = {
            "123456":
                {
                    "name": "Fardeen S",
                    "major": "Computer Science",
                    "starting_year": 2020,
                    "total_attendance": 0,
                    "standing": "S+",
                    "year": 4,
                    "last_tracked_time": "2024-1-28 00:54:00"
                },
        }

        for key, value in data.items():
            ref.child(key).set(value)

        retrieved_data = ref.get()
        self.assertEqual(data, retrieved_data, "Data retrieved from Firebase does not match the original data")

if __name__ == '__main__':
    unittest.main()
