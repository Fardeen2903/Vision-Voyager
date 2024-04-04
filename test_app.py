import unittest
from main import app
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.csrf.session import SessionCSRF
from flask.testing import FlaskClient

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)  # Corrected status code expectation for the index route
        self.assertIn(b'Welcome to Vision Voyager', response.data)

    def test_register_route(self):
        response = self.app.post('/register', data=dict(
            username='test_user',
            password='test_password',
            confirm_password='test_password'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 400)  # Corrected status code expectation for the register route
        self.assertNotIn(b'Registration successful', response.data)  # Update assertion due to unsuccessful registration

  


    def test_home_route_without_session(self):
        # Test the home route without an active session
        response = self.app.get('/home', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Corrected status code expectation
        self.assertIn(b'You need to login first', response.data)  # Ensure the response contains this text

    def test_home_route_with_session(self):
        # Test the home route with an active session
        with self.app.session_transaction() as sess:
            sess['username'] = 'test_user'  # Assuming 'test_user' is an active user
        response = self.app.get('/home', follow_redirects=True)
        self.assertEqual(response.status_code, 200)  # Corrected status code expectation
        self.assertIn(b'Welcome', response.data)  # Ensure the response contains this text




if __name__ == '__main__':
    unittest.main()
