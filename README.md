# Vision Voyager

## Overview

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Technologies Used](#technologies-used)
- [Future Plans](#future-plans)
- [Contributing](#contributing)
- [License](#license)

## Features

- Face recognition using the `face_recognition` library.
- Real-time display of video with attendance information.
- Firebase integration for data storage and retrieval.
- Student data management with an additional script.
- Encoding of facial features and image upload to Firebase Storage.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/face-recognition-attendance-system.git
   cd face-recognition-attendance-system
   
Install the required dependencies:

    pip install -r requirements.txt

Set up Firebase:

    Create a Firebase project and obtain the necessary credentials.
    Replace VVDB_KEY.json with your Firebase service account key.

## Usage

1. Run AdddatatoDatabase.py to add student data to the Firebase Realtime Database.

2. Run encodegenerator.py to generate face encodings and upload images to Firebase Storage.

3. python encodegenerator.py

## Technologies Used

- Python
- OpenCV
- face_recognition library
- Firebase Realtime Database
- Firebase Storage

## Future Plans









