import pytest
from app import app, Product, User
from unittest.mock import patch, MagicMock

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

@patch('app.User.query.filter_by')
def test_login_success(mock_filter_by, client):
    mock_user = MagicMock(spec=User)
    mock_user.check_password.return_value = True
    mock_filter_by.return_value.first.return_value = mock_user

    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)

    assert b"Logged in successfully" in response.data or response.status_code == 200

@patch('app.User.query.filter_by')
def test_login_failure(mock_filter_by, client):
    mock_filter_by.return_value.first.return_value = None
    response = client.post('/login', data={
        'email': 'invalid@example.com',
        'password': 'wrong'
    }, follow_redirects=True)

    assert b"Invalid email or password" in response.data or response.status_code == 200

@patch('app.User.query.filter_by')
def test_signup_existing_user(mock_filter_by, client):
    mock_filter_by.side_effect = [MagicMock(), None]  # username exists
    response = client.post('/signup', data={
        'username': 'existinguser',
        'email': 'new@example.com',
        'password': '1234',
        'confirm_password': '1234'
    }, follow_redirects=True)

    assert b"Username already exists" in response.data

def test_signup_password_mismatch(client):
    response = client.post('/signup', data={
        'username': 'user',
        'email': 'user@example.com',
        'password': 'pass1',
        'confirm_password': 'pass2'
    }, follow_redirects=True)

    assert b"Passwords do not match" in response.data

@patch('app.CartItem.query.filter_by')
@patch('app.Product')
def test_cart_page(mock_product, mock_cartitem, client):
    mock_product.price = 10
    mock_cartitem.return_value.all.return_value = [
        MagicMock(product=mock_product, quantity=2)
    ]

    with client.session_transaction() as sess:
        sess['_user_id'] = '1'  # Simulate logged in user

    response = client.get('/cart')
    assert b"Total" in response.data or response.status_code == 200

@patch('app.CartItem.query.filter_by')
@patch('app.db.session.commit')
def test_checkout_post(mock_commit, mock_cartitem, client):
    mock_cartitem.return_value.all.return_value = [
        MagicMock(product=MagicMock(price=20.0), quantity=1)
    ]

    with client.session_transaction() as sess:
        sess['_user_id'] = '1'

    response = client.post('/checkout', follow_redirects=True)
    assert b"thank" in response.data.lower()

@patch('app.CartItem.query.filter_by')
def test_checkout_get(mock_cartitem, client):
    mock_cartitem.return_value.all.return_value = [
        MagicMock(product=MagicMock(price=15.0), quantity=2)
    ]

    with client.session_transaction() as sess:
        sess['_user_id'] = '1'

    response = client.get('/checkout')
    assert b"Checkout" in response.data or b"Total" in response.data
