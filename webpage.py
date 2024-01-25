# Import necessary libraries
from datetime import datetime
import firebase_admin
from flask import Flask, request, redirect, url_for, render_template, flash
from firebase_admin import credentials, firestore, storage
from werkzeug.utils import secure_filename
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'secretsecretsecretkey'

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

# Create a route for adding a new person
@app.route('/add_person', methods=['GET', 'POST'])
def add_person():
    if request.method == 'POST':
        # Get the form data
        name = request.form['name']
        status = request.form['status']
        office_room_number = request.form['office_room_number']
        department_or_major = request.form['department_or_major']

        # Create a new person document
        person_data = {
            'name': name,
            'status': status,
            'office_room_number': office_room_number,
            'department_or_major': department_or_major,
        }

        # Upload the photo if provided
        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('path_to_your_upload_folder', filename)
            file.save(file_path)

            # Upload the file to Firebase Storage
            blob = bucket.blob(f'photos/{filename}')
            blob.upload_from_filename(file_path)

            # Add the photo URL to the person document
            person_data['photo_url'] = blob.public_url

        # Add the person data to Firestore
        db.collection('people').add(person_data)
        flash('Person added successfully.')
        return redirect(url_for('view_people'))

    return render_template('add_person.html')

# Create a route for viewing all people
@app.route('/view_people')
def view_people():
    people = db.collection('people').stream()
    person_list = [{'doc_id': person.id, **person.to_dict()} for person in people]
    return render_template('view_people.html', people=person_list)

# Create a route for editing a person's information
@app.route('/edit_person/<person_id>', methods=['GET', 'POST'])
def edit_person(person_id):
    person_ref = db.collection('people').document(person_id)

    if request.method == 'POST':
        # Get the updated form data
        name = request.form['name']
        status = request.form['status']
        office_room_number = request.form['office_room_number']
        department_or_major = request.form['department_or_major']

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

    person = person_ref.get().to_dict()
    return render_template('edit_person.html', person=person, person_id=person_id)

# Create a route for deleting a person
@app.route('/delete_person/<person_id>', methods=['POST'])
def delete_person(person_id):
    db.collection('people').document(person_id).delete()
    flash('Person deleted successfully!')
    return redirect(url_for('view_people'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
