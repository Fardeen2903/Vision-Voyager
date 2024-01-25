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

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_person', methods=['GET', 'POST'])
def add_person():
    if request.method == 'POST':
        person_data = {
            'name': request.form['name'],
            'status': request.form['status'],
            'office_room_number': request.form['office_room_number'],
            'department_or_major': request.form['department_or_major'],
        }

        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('path_to_your_upload_folder', filename)
            file.save(file_path)

            # Upload the file to Firebase Storage
            blob = bucket.blob(f'person_photos/{filename}')
            blob.upload_from_filename(file_path)

            # Add the public URL to the person data
            person_data['photo_url'] = blob.public_url

        # Add person data to Firestore
        db.collection('People').add(person_data)
        flash('Person added successfully.')
        return redirect(url_for('index'))

    return render_template('add_person.html')

@app.route('/view_people')
def view_people():
    people = db.collection('People').stream()
    person_list = [{'doc_id': person.id, **person.to_dict()} for person in people]
    return render_template('view_people.html', people=person_list)

@app.route('/edit_person/<person_id>', methods=['GET', 'POST'])
def edit_person(person_id):
    person_ref = db.collection('People').document(person_id)

    if request.method == 'POST':
        updated_data = {
            'name': request.form['name'],
            'status': request.form['status'],
            'office_room_number': request.form['office_room_number'],
            'department_or_major': request.form['department_or_major'],
        }
        person_ref.update(updated_data)
        flash('Person updated successfully!')
        return redirect(url_for('view_people'))

    person = person_ref.get().to_dict()
    return render_template('edit_person.html', person=person, person_id=person_id)

@app.route('/delete_person/<person_id>', methods=['POST'])
def delete_person(person_id):
    db.collection('People').document(person_id).delete()
    flash('Person deleted successfully!')
    return redirect(url_for('view_people'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
