import unittest
import os
from unittest.mock import patch

from webapp import app


class TestWebApp(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to My App', response.data)

    def test_add_person_route(self):
        response = self.app.get('/add_person')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Person', response.data)

    def test_view_people_route(self):
        response = self.app.get('/view_people')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'View People', response.data)

    @patch('webapp.face_recognition_function')  # Mock the face_recognition_function
    def test_face_recognition_route(self, mock_face_recognition_function):

        mock_face_recognition_function.return_value = {'result': 'success'}

        with open('test_image.png', 'rb') as image_file:
            response = self.app.post('/face_recognition', data={'image': image_file},
                                     content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_face_recognition_function.called)

if __name__ == '__main__':
    unittest.main()
