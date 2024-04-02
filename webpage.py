## Import necessary libraries
from flask_wtf.csrf import CSRFProtect, generate_csrf
import firebase_admin
from firebase_admin import credentials, storage, db  # Changed from firestore to db for Realtime Database
from flask import Flask, request, redirect, url_for, render_template, flash, abort, session, jsonify
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField
from flask_wtf.file import MultipleFileField, FileAllowed
import numpy as np
import cv2
import face_recognition
from app import recognize_face, start_face_recognition_process
import subprocess
from uuid import uuid4
import logging
import sys
import os
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'verysecretkey'
csrf = CSRFProtect(app)
csrf.init_app(app)

# Check if the default app has already been initialized to prevent re-initialization error
if not firebase_admin._apps:
    cred = credentials.Certificate("VVDB_KEY.json")
    default_app = firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://visionvoyagerdb-default-rtdb.firebaseio.com/',  # Add your Realtime Database URL
        'storageBucket': 'visionvoyagerdb.appspot.com'
    })

bucket = storage.bucket(app=firebase_admin.get_app())

# Firebase Realtime Database initialization (Note: 'db' used from the imported 'db', not firestore)
db_ref = db.reference()  # This is the root reference for Realtime Database

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_not_found.html'), 404

@app.route('/about')
def about():
    return render_template('about.html')

class AddPersonForm(FlaskForm):
    name = StringField('Name')
    status = StringField('Status')
    office_room_number = StringField('Office Room Number')
    department_or_major = StringField('Department or Major')
    photos = MultipleFileField('Photos', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])


@app.route('/add_person', methods=['GET', 'POST'])
def add_person():
    form = AddPersonForm()

    if form.validate_on_submit():
        # Generate a unique ID for the new person
        unique_id = str(uuid4())

        # Extract form data
        name = form.name.data
        status = form.status.data
        office_room_number = form.office_room_number.data
        department_or_major = form.department_or_major.data

        # Create a dictionary of the person's data
        person_data = {
            'name': name,
            'status': status,
            'office_room_number': office_room_number,
            'department_or_major': department_or_major,
        }

        # Process each photo if any
        if form.photos.data:
            for file in form.photos.data:
                if file and allowed_file(file.filename):
                    # Secure the filename
                    _, file_extension = os.path.splitext(file.filename)
                    secure_name = f"{unique_id}{file_extension}"  # Use the unique ID as the file name
                    blob = bucket.blob(f'Face-Rec/images/{secure_name}')
                    blob.upload_from_string(file.read(), content_type=file.content_type)

                    # Store the public URL in the Realtime Database
                    person_data['photo_url'] = blob.public_url
                    try:
                        blob.upload_from_string(file.read(), content_type=file.content_type)
                        person_data['photo_url'] = blob.public_url
                    except Exception as e:
                        logging.error(f"Failed to upload file: {e}")

        # Save the person data to the Realtime Database using the unique ID
        db_ref = db.reference(f'people/{unique_id}')
        db_ref.set(person_data)

        flash('Person added successfully.')
        return redirect(url_for('view_people'))

    return render_template('add_person.html', csrf_token=generate_csrf(), form=form)



@app.route('/view_people')
def view_people():
    # Firebase Realtime Database retrieval
    ref = db.reference('people')  # This references the 'people' node
    people = ref.get()  # This retrieves all people from the 'people' node

    person_list = []
    if people:  # Check if people is not None
        person_list = [{'doc_id': key, **val} for key, val in people.items()]

    form = FlaskForm()  # Assuming you have a reason for this form here.
    return render_template('view_people.html', people=person_list, form=form)



@app.route('/face_recognition', methods=['POST'])
def face_recognition():
    # Get the image file from the request
    file = request.files['image']

    # Convert the image file to a numpy array
    img_np = np.fromstring(file.read(), np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

    # Perform face recognition on the image
    face_locations = face_recognition.face_locations(img)
    face_encodings = face_recognition.face_encodings(img, face_locations)

    # Process the detected faces (e.g., identify known faces, draw bounding boxes)

    # Prepare the response data
    response_data = {
        'faces_detected': len(face_locations),
        'face_locations': face_locations,  # Optionally, you can convert to a format suitable for JSON serialization
        # Add other relevant data here
    }

    # Return the response as JSON
    return jsonify(response_data)


@app.route('/find_person', methods=['POST'])
def find_person():
    if 'image' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        # Convert the image file to a format that can be processed
        img = np.fromstring(file.read(), np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        # Use the recognize_face function to attempt to identify the person
        recognized_ids = recognize_face(img)
        # Use the recognize_face function to attempt to identify the person
        recognized_ids = recognize_face(img)

        if recognized_ids:
            # Assuming the list only contains one recognized ID for simplicity
            person_id = recognized_ids[0]
            doc_ref = db.collection('Students').document(person_id)
            doc = doc_ref.get()
            if doc.exists:
                person_data = doc.to_dict()
                # Assuming you've already got the photos uploaded with the person's ID
                img_blob = bucket.blob(f"photos/{person_id}.jpg")
                img_url = img_blob.public_url if img_blob.exists() else None

                return jsonify({
                    "found": True,
                    "id": person_id,
                    "name": person_data.get('name'),
                    "major": person_data.get('major'),
                    "img_url": img_url
                })
        else:
            # No person recognized
            return jsonify({"found": False}), 404


def is_url_correct(requested_url):
    valid_urls = ['/view_people', '/add_person', '/edit_person']
    return requested_url in valid_urls


class EditPersonForm(FlaskForm):
    name = StringField('Name')
    status = StringField('Status')
    office_room_number = StringField('Office Room Number')
    department_or_major = StringField('Department or Major')
    photos = MultipleFileField('Photos', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])


@app.route('/edit_person/<person_id>', methods=['GET', 'POST'])
def edit_person(person_id):
    ref = db.reference(f'people/{person_id}')  # Realtime Database reference to a specific person
    person = ref.get()

    if person is None:
        flash('Person not found.')
        return redirect(url_for('view_people'))

    form = EditPersonForm()

    if request.method == 'POST' and form.validate_on_submit():
        updated_data = {
            'name': form.name.data,
            'status': form.status.data,
            'office_room_number': form.office_room_number.data,
            'department_or_major': form.department_or_major.data,
        }

        # Realtime Database update
        ref.update(updated_data)  # Update the person's data in the Realtime Database

        flash('Person updated successfully!')
        return redirect(url_for('view_people'))

    # If it's a GET request or the form is not validated, prefill the form
    form.name.data = person.get('name', '')
    form.status.data = person.get('status', '')
    form.office_room_number.data = person.get('office_room_number', '')
    form.department_or_major.data = person.get('department_or_major', '')

    return render_template('edit_person.html', person_id=person_id, form=form)


@app.route('/delete_person/<person_id>', methods=['POST'])
def delete_person(person_id):
    csrf_token = request.form.get('csrf_token')

    if not csrf_token:
        abort(400)

    # Realtime Database delete
    ref = db.reference(f'people/{person_id}')  # Realtime Database reference to the specific person
    ref.delete()  # Delete the person's data from the Realtime Database

    flash('Person deleted successfully!')
    return redirect(url_for('view_people'))


@app.route('/test_app')
def test_app():
    # This route will render the test_app.html template that includes a button to start the face recognition process
    return render_template('test_app.html')


@app.route('/start_face_recognition', methods=['GET'])
def start_face_recognition():
    try:
        # Specify the command to run app.py. Adjust the path to app.py as necessary.
        command = ['C:\\Users\\littl\\PycharmProjects\\pythonProject\\venv\\Scripts\\python', 'C:\\Users\\littl\\OneDrive\\Documents\\GitHub\\Vision-Voyager\\app.py']  # Change this to the correct path

        # Start app.py as a subprocess and capture the output and errors
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Read output and errors
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            message = "Face recognition process started successfully."
        else:
            message = f"Face recognition process failed to start. STDOUT: {stdout} STDERR: {stderr}"

        return jsonify({"message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8000)
