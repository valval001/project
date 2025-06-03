import pytest
from app import app, db, User, Product, CartItem
from flask import session

@pytest.fixture
def client():
    # Setup app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for testing
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a sample product for cart tests
            product = Product(name='Test Product', description='Desc', price=10.0, image_url='http://image.url')
            db.session.add(product)
            db.session.commit()
        yield client
        # Clean up DB after tests
        with app.app_context():
            db.drop_all()

def signup(client, username, email, password, confirm):
    return client.post('/signup', data={
        'username': username,
        'email': email,
        'password': password,
        'confirm_password': confirm
    }, follow_redirects=True)

def login(client, email, password):
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)


def test_signup_login_logout(client):
    # Signup new user
    resp = signup(client, 'testuser', 'test@example.com', 'testpass', 'testpass')
    assert b"Account created" in resp.data

    # Login with new user
    resp = login(client, 'test@example.com', 'testpass')
    assert b"Logged in successfully" in resp.data

    # Logout
    resp = logout(client)
    assert b"You have been logged out" in resp.data

def test_add_remove_cart(client):
    # Signup and login
    signup(client, 'testuser', 'test@example.com', 'testpass', 'testpass')
    login(client, 'test@example.com', 'testpass')

    # Add product to cart (product id 1 since only one product created)
    resp = client.get('/add_to_cart/1', follow_redirects=True)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert 1 in sess.get('cart', [])

    # Check cart page
    resp = client.get('/cart')
    assert b'Test Product' in resp.data

    # Remove product from cart
    resp = client.get('/remove_from_cart/1', follow_redirects=True)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        # Cart should be empty now
        assert sess.get('cart', []) == []

def test_checkout_clears_cart(client):
    signup(client, 'testuser', 'test@example.com', 'testpass', 'testpass')
    login(client, 'test@example.com', 'testpass')

    # Add product to cart twice (quantity=2)
    client.get('/add_to_cart/1')
    client.get('/add_to_cart/1')

    resp = client.get('/cart')
    assert b'Test Product' in resp.data

    # Checkout page GET
    resp = client.get('/checkout')
    assert b'Test Product' in resp.data

    # Checkout POST to clear cart
    resp = client.post('/checkout', follow_redirects=True)
    assert b'Thank you' in resp.data

    # Cart should be empty now
    resp = client.get('/cart')
    assert b'Test Product' not in resp.data
