import pytest
from app import app, User, Product
from unittest.mock import patch
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_index_page(client):
    with patch('app.Product.query.paginate') as mock_paginate:
        mock_paginate.return_value.items = []
        mock_paginate.return_value.page = 1
        mock_paginate.return_value.pages = 1
        response = client.get('/')
        assert response.status_code == 200
        assert b"Product" in response.data or b"No products" in response.data

def test_add_to_cart(client):
    with client.session_transaction() as sess:
        sess['cart'] = []
    response = client.get('/add_to_cart/1', follow_redirects=True)
    with client.session_transaction() as sess:
        assert 1 in sess['cart']
    assert response.status_code == 200

def test_remove_from_cart(client):
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    response = client.get('/remove_from_cart/1', follow_redirects=True)
    with client.session_transaction() as sess:
        assert 1 not in sess['cart']
    assert response.status_code == 200

def test_checkout_get(client):
    mock_product = Product(id=1, name="Mock", description="desc", price=10.0, image_url="url")
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    with patch('app.Product.query.get', return_value=mock_product):
        response = client.get('/checkout')
        assert response.status_code == 200
        assert b"Checkout" in response.data or b"Total" in response.data

def test_checkout_post(client):
    mock_product = Product(id=1, name="Mock", description="desc", price=10.0, image_url="url")
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    with patch('app.Product.query.get', return_value=mock_product):
        response = client.post('/checkout')
        assert response.status_code == 200
        assert b"thank" in response.data.lower()

# ---- New tests for user login/signup ----

def test_signup(client):
    # Mock User.query.filter_by to simulate no existing user
    with patch('app.User.query.filter_by') as mock_filter:
        mock_filter.return_value.first.return_value = None
        response = client.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password',
            'confirm_password': 'password'
        }, follow_redirects=True)
        assert response.status_code == 200
        # You can assert success message or redirect URL as per your app

def test_signup_existing_email(client):
    # Simulate existing user found in DB
    with patch('app.User.query.filter_by') as mock_filter:
        mock_filter.return_value.first.return_value = User(username='existing', email='existing@example.com')
        response = client.post('/signup', data={
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'password',
            'confirm_password': 'password'
        })
        assert b'Email already registered' in response.data or response.status_code == 200

def test_login_success(client):
    test_user = User(username='testuser', email='test@example.com')
    test_user.password_hash = generate_password_hash('testpass')

    with patch('app.User.query.filter_by') as mock_filter:
        mock_filter.return_value.first.return_value = test_user
        response = client.post('/login', data={'email': 'test@example.com', 'password': 'testpass'}, follow_redirects=True)
        assert response.status_code == 200
        # You can check for a welcome message or redirect location

def test_login_fail(client):
    with patch('app.User.query.filter_by') as mock_filter:
        mock_filter.return_value.first.return_value = None
        response = client.post('/login', data={'email': 'wrong@example.com', 'password': 'wrongpass'})
        assert b'Invalid email or password' in response.data or response.status_code == 200

# ---- More detailed cart tests ----

def test_add_same_product_multiple_times(client):
    with client.session_transaction() as sess:
        sess['cart'] = [1, 1]
    response = client.get('/add_to_cart/1', follow_redirects=True)
    with client.session_transaction() as sess:
        # The cart might be a list, check if count of '1' is increased
        assert sess['cart'].count(1) >= 3
    assert response.status_code == 200

def test_remove_product_not_in_cart(client):
    with client.session_transaction() as sess:
        sess['cart'] = []
    response = client.get('/remove_from_cart/1', follow_redirects=True)
    with client.session_transaction() as sess:
        assert 1 not in sess['cart']
    assert response.status_code == 200
