# Import necessary libraries
from flask_wtf.csrf import CSRFProtect
import firebase_admin
from flask import Flask, request, redirect, url_for, render_template, flash, abort, session
from firebase_admin import credentials, firestore, storage
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf.file import MultipleFileField, FileAllowed
from wtforms.validators import DataRequired, Length, EqualTo
from datetime import datetime
from firebase_admin import auth
from functools import wraps

app = Flask(__name__)

# This code sets a secret key for Flask-WTF to use for CSRF protection
app.config['SECRET_KEY'] = 'verysecretkey'

# This code initializes CSRFProtect after other components
csrf = CSRFProtect(app)
csrf.init_app(app)

# Firebase Initialization
cred = credentials.Certificate("ServiceKey.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'visionvoyager-bd590.appspot.com'})
bucket = storage.bucket()

db = firestore.client()

# Dummy user data for demonstration purposes
USERS = {
    'user1': 'password1',
    'user2': 'password2'
}

# CSRF protection
csrf = CSRFProtect(app)
csrf.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

# Login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # You can add code here to store user data in Firebase or another database
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        try:
            user = auth.get_user_by_email(username)  # Assuming username is the email
            auth_user = auth.sign_in_with_email_and_password(username, password)
            session['user_id'] = auth_user['localId']
            flash('Login successful!', 'success')
            return redirect(url_for('view_people'))
        except Exception as e:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html', form=form)


@app.route('/authenticate', methods=['POST'])
def authenticate():
    password = request.form.get('password')
    if password == '123':  # Replace 'your_password' with the actual password
        session['authenticated'] = True
        flash('Authentication successful!', 'success')
        return redirect(url_for('view_people'))
    else:
        flash('Invalid password. Please try again.', 'error')
        return redirect(url_for('view_people'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


# Home route
@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        flash('You need to login first', 'error')
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

# Allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class AddPersonForm(FlaskForm):
    name = StringField('Name')
    status = StringField('Status')
    office_room_number = StringField('Office Room Number')
    department_or_major = StringField('Department or Major')
    photos = MultipleFileField('Photos', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])

@login_required
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
    people = db.collection('people').stream()
    person_list = [{'doc_id': person.id, **person.to_dict()} for person in people]

    for person in person_list:
        # Determine if authentication is required for editing this person
        person['require_authentication'] = True  # Set it to True by default
        if 'authenticated' in session:
            person['require_authentication'] = False

    return render_template('view_people.html', people=person_list, form=FlaskForm())

class EditPersonForm(FlaskForm):
    name = StringField('Name')
    status = StringField('Status')
    office_room_number = StringField('Office Room Number')
    department_or_major = StringField('Department or Major')
    photos = MultipleFileField('Photos', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])

@app.route('/edit_person/<person_id>', methods=['GET', 'POST'])
@login_required
def edit_person(person_id):
    # Retrieve the person's data from Firestore
    person_ref = db.collection('people').document(person_id)
    person = person_ref.get().to_dict()

    if person is None:
        flash('Person not found.')
        return redirect(url_for('view_people'))

    # Create the form instance
    form = EditPersonForm()

    # Process the form data if it's a POST request and the form is valid
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

        # Update the person's data in Firestore
        person_ref.update(updated_data)
        flash('Person updated successfully!')
        return redirect(url_for('view_people'))

    # Populate the form fields with the person's data
    form.name.data = person.get('name', '')
    form.status.data = person.get('status', '')
    form.office_room_number.data = person.get('office_room_number', '')
    form.department_or_major.data = person.get('department_or_major', '')

    return render_template('edit_person.html', person_id=person_id, form=form)

@app.route('/delete_person/<person_id>', methods=['POST'])
@login_required
def delete_person(person_id):
    csrf_token = request.form.get('csrf_token')

    if not csrf_token:
        abort(400)

    db.collection('people').document(person_id).delete()
    flash('Person deleted successfully!')
    return redirect(url_for('view_people'))

# Custom error handler for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_not_found.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=8000)
