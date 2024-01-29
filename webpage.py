# Import necessary libraries
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
import firebase_admin
from flask import Flask, request, redirect, url_for, render_template, flash
from firebase_admin import credentials, firestore, storage
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, FileField
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os

app = Flask(__name__)

# This code sets a secret key for Flask-WTF to use for CSRF protection
app.config['SECRET_KEY'] = 'your_secret_key_here'

# This code initializes CSRFProtect after other components
csrf = CSRFProtect(app)
csrf.init_app(app)

# Firebase Initialization
cred = credentials.Certificate("ServiceKey.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'your-firebase-storage-bucket'})



db = firestore.client()
bucket = storage.bucket()

# Allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

class AddPersonForm(FlaskForm):
    name = StringField('Name')
    status = StringField('Status')
    office_room_number = StringField('Office Room Number')
    department_or_major = StringField('Department or Major')
    photo = FileField('Photo')

@app.route('/add_person', methods=['GET', 'POST'])
def add_person():
    form = AddPersonForm()

    if form.validate_on_submit():

        name = form.name.data
        status = form.status.data
        office_room_number = form.office_room_number.data
        department_or_major = form.department_or_major.data

        # Create a new person document
        person_data = {
            'name': name,
            'status': status,
            'office_room_number': office_room_number,
            'department_or_major': department_or_major,
        }


        file = form.photo.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('path_to_your_upload_folder', filename)
            file.save(file_path)

            # This code uploads the file to Firebase Storage
            blob = bucket.blob(f'photos/{filename}')
            blob.upload_from_filename(file_path)


            person_data['photo_url'] = blob.public_url


        db.collection('people').add(person_data)
        flash('Person added successfully.')
        return redirect(url_for('view_people'))

    return render_template('add_person.html', form=form)

@app.route('/view_people')
def view_people():
    people = db.collection('people').stream()
    person_list = [{'doc_id': person.id, **person.to_dict()} for person in people]
    form = FlaskForm()
    return render_template('view_people.html', people=person_list, form=form)

class EditPersonForm(FlaskForm):
    name = StringField('Name')
    status = StringField('Status')
    office_room_number = StringField('Office Room Number')
    department_or_major = StringField('Department or Major')
    photo = FileField('Photo')

# This code creates a route for editing a person's information
@app.route('/edit_person/<person_id>', methods=['GET', 'POST'])
def edit_person(person_id):
    person_ref = db.collection('people').document(person_id)
    person = person_ref.get().to_dict()

    form = EditPersonForm()

    if request.method == 'POST' and form.validate_on_submit():
        # Get the updated form data
        name = form.name.data
        status = form.status.data
        office_room_number = form.office_room_number.data
        department_or_major = form.department_or_major.data

        # Update the person document
        updated_data = {
            'name': name,
            'status': status,
            'office_room_number': office_room_number,
            'department_or_major': department_or_major,
        }

        person_ref.update(updated_data)
        flash('Person updated successfully!')
        return redirect(url_for('view_people'))

    # This code loads existing person details into the form fields
    form.name.data = person['name']
    form.status.data = person['status']
    form.office_room_number.data = person['office_room_number']
    form.department_or_major.data = person['department_or_major']

    return render_template('edit_person.html', person_id=person_id, form=form)


# This code creates a route for deleting a person
@app.route('/delete_person/<person_id>', methods=['POST'])
def delete_person(person_id):
    csrf_token = request.form.get('csrf_token')

    # Validate CSRF token
    if not csrf_token:
        abort(400)  # Bad Request - CSRF token missing or invalid

    db.collection('people').document(person_id).delete()
    flash('Person deleted successfully!')
    return redirect(url_for('view_people'))
if __name__ == '__main__':
    app.run(debug=True, port=8000)
