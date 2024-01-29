import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("VVDB_KEY.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://visionvoyagerdb-default-rtdb.firebaseio.com/"
})

ref = db.reference('Students')

data = {
    "123456":
        {
            "name": "Bryce McLeod",
            "major": "Computer Science",
            "starting_year": 2020,
            "total_attendance": 0,
            "standing": "S+",
            "year": 4,
            "last_tracked_time": "2024-1-28 00:54:00"
        },
    "321654":
        {
            "name": "Indian Dude",
            "major": "Robotics",
            "starting_year": 2017,
            "total_attendance": 7,
            "standing": "A+",
            "year": 4,
            "last_tracked_time": "2024-1-28 00:54:34"
        },
    "852741":
        {
            "name": "Emly Blunt",
            "major": "Economics",
            "starting_year": 2021,
            "total_attendance": 12,
            "standing": "B",
            "year": 1,
            "last_tracked_time": "2024-1-28 00:54:34"
        },
    "963852":
        {
            "name": "Elon Musk",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 7,
            "standing": "F",
            "year": 2,
            "last_tracked_time": "2024-1-28 00:54:34"
        }
}

# Send Da Data
for key, value in data.items():
    ref.child(key).set(value)