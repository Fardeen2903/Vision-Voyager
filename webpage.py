# Import necessary libraries
from flask_wtf.csrf import CSRFProtect
import firebase_admin
from flask import Flask, request, redirect, url_for, render_template, flash, abort, session, jsonify
from firebase_admin import credentials, firestore, storage
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField
from flask_wtf.file import MultipleFileField, FileAllowed
import numpy as np
import cv2
import face_recognition
from app import recognize_face
import sys
sys.path.append('app.py')

app = Flask(__name__)

app.config['SECRET_KEY'] = 'verysecretkey'

csrf = CSRFProtect(app)
csrf.init_app(app)

cred = credentials.Certificate("VVDB_KEY.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'visionvoyagerdb.appspot.com'})
bucket = storage.bucket()

db = firestore.client()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_not_found.html'), 404

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
        name = form.name.data
        status = form.status.data
        office_room_number = form.office_room_number.data
        department_or_major = form.department_or_major.data

        person_data = {
            'name': name,
            'status': status,
            'office_room_number': office_room_number,
            'department_or_major': department_or_major,
        }

        photo_urls = []

        if form.photos.data:
            for file in form.photos.data:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    blob = bucket.blob(f'photos/{filename}')
                    blob.upload_from_string(file.read(), content_type=file.content_type)
                    photo_urls.append(blob.public_url)

        person_data['photo_urls'] = photo_urls

        db.collection('people').add(person_data)
        flash('Person added successfully.')
        return redirect(url_for('view_people'))

    return render_template('add_person.html', form=form)

@app.route('/view_people')
def view_people():
    # Check the URL here, and if incorrect, redirect to the previous working page
    if not is_url_correct(request.path):
        flash('Incorrect URL. Redirecting to the previous page.')
        return redirect(url_for(session.get('last_working_page', 'index')))

    # Store the current page in the session
    session['last_working_page'] = 'view_people'

    people = db.collection('people').stream()
    person_list = [{'doc_id': person.id, **person.to_dict()} for person in people]
    form = FlaskForm()
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
    # Check if the post request has the file part
    if 'image' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['image']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Read the image file in a format suitable for OpenCV
        img = face_recognition.load_image_file(file)
        # Call the face recognition function
        person_found = recognize_face(img)
        if person_found:
            return jsonify({"found": True, "person": person_found})
        else:
            return jsonify({"found": False})

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
    person_ref = db.collection('people').document(person_id)
    person = person_ref.get().to_dict()

    if person is None:
        flash('Person not found.')
        return redirect(url_for('view_people'))

    form = EditPersonForm()

    if request.method == 'POST' and form.validate_on_submit():
        name = form.name.data
        status = form.status.data
        office_room_number = form.office_room_number.data
        department_or_major = form.department_or_major.data

        updated_data = {
            'name': name,
            'status': status,
            'office_room_number': office_room_number,
            'department_or_major': department_or_major,
        }

        person_ref.update(updated_data)
        flash('Person updated successfully!')
        return redirect(url_for('view_people'))

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

    db.collection('people').document(person_id).delete()
    flash('Person deleted successfully!')
    return redirect(url_for('view_people'))

@app.route('/test_app')
def test_app():
    return render_template('test_app.html')

    db.collection('people').document(person_id).delete()
    flash('Person deleted successfully!')
    return redirect(url_for('view_people'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)
