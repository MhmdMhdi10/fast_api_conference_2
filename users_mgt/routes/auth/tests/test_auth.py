import os

from fastapi.testclient import TestClient
from database.database import SessionLocal, engine
from main import app

client = TestClient(app)


def test_signup():
    response = client.post(
        "/auth/users",
        json={"username": "test_user", "password": "test_password"},
    )

    assert response.status_code == 201


def test_signup_repeat():
    response = client.post(
        "/auth/users",
        json={"username": "test_user", "password": "test_password"},
    )

    assert response.status_code == 400


def test_login():
    response = client.post(
        "/auth/login",
        json={"username": "test_user", "password": "test_password"},
    )

    assert response.status_code == 200


def test_login_no_account():
    response = client.post(
        "/auth/login",
        json={"username": "test_user1", "password": "test_password1"},
    )

    assert response.status_code == 400


def test_refresh():
    login_response = client.post('/auth/login', json={'username': 'test_user', 'password': 'test_password'})
    refresh_token = login_response.json()['refresh']
    headers = {'Authorization': f'Bearer {refresh_token}'}
    response = client.post('/auth/refresh', headers=headers)

    assert response.status_code == 200


def test_refresh_invalid_token():
    # Test refreshing a token with an invalid ref+resh token
    headers = {'Authorization': 'Bearer invalid_token'}
    response = client.post('/auth/refresh', headers=headers)
    assert response.status_code == 401




# class TestAuthAPI(unittest.TestCase):
#     def setUp(self):
#         self.client = TestClient(app)
#         self.db = SessionLocal(bind=engine)
#         self._create_test_user()
#
#     def tearDown(self):
#         self.db.rollback()
#         self.db.close()
#
#     def _create_test_user(self):
#         user = User(
#             username='test_user',
#             password=generate_password_hash('test_password'),
#         )
#         self.db.add(user)
#         self.db.commit()
#
#     def test_signup(self):
#         # Test creating a new user
#         response = self.client.post('/auth/users', json={'username': 'new_user', 'password': 'new_password'})
#         self.assertEqual(response.status_code, 201)
#         self.assertEqual(response.json()['username'], 'new_user')
#
#     def test_signup_duplicate_username(self):
#         # Test creating a user with a duplicate username
#         response = self.client.post('/auth/users', json={'username': 'test_user', 'password': 'new_password'})
#         self.assertEqual(response.status_code, 400)
#
#     def test_login(self):
#         # Test logging in with valid credentials
#         response = self.client.post('/auth/login', json={'username': 'test_user', 'password': 'test_password'})
#         self.assertEqual(response.status_code, 200)
#         self.assertIsNotNone(response.json()['access'])
#         self.assertIsNotNone(response.json()['refresh'])
#
#     def test_login_invalid_credentials(self):
#         # Test logging in with invalid credentials
#         response = self.client.post('/auth/login', json={'username': 'test_user', 'password': 'wrong_password'})
#         self.assertEqual(response.status_code, 400)
#
#     def test_refresh(self):
#         # Test refreshing a token with a valid refresh token
#         login_response = self.client.post('/auth/login', json={'username': 'test_user', 'password': 'test_password'})
#         refresh_token = login_response.json()['refresh']
#         headers = {'Authorization': f'Bearer {refresh_token}'}
#         response = self.client.post('/auth/refresh', headers=headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertIsNotNone(response.json()['access'])
#
#     def test_refresh_invalid_token(self):
#         # Test refreshing a token with an invalid refresh token
#         headers = {'Authorization': 'Bearer invalid_token'}
#         response = self.client.post('/auth/refresh', headers=headers)
#         self.assertEqual(response.status_code, 401)
