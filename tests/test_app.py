import os
import pytest
from app import app, db, User, Product, CartItem

# Force testing environment to use SQLite in-memory DB
os.environ['FLASK_ENV'] = 'testing'
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['WTF_CSRF_ENABLED'] = False  # If you ever use Flask-WTF
app.config['SECRET_KEY'] = 'test-secret-key'

@pytest.fixture
def client():
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_signup_login_logout(client):
    # Sign up
    response = client.post('/signup', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password',
        'confirm_password': 'password'
    }, follow_redirects=True)
    assert b'Account created! Please log in.' in response.data

    # Login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password'
    }, follow_redirects=True)
    assert b'Logged in successfully.' in response.data

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert b'You have been logged out.' in response.data


def test_add_product_and_cart(client):
    # Setup user and login
    with app.app_context():
        user = User(username="buyer", email="buyer@example.com")
        user.set_password("pass123")
        db.session.add(user)

        product = Product(name="Test Product", description="Test Desc", price=99.99, image_url="http://example.com/img.jpg")
        db.session.add(product)

        db.session.commit()

    # Login
    client.post('/login', data={'email': 'buyer@example.com', 'password': 'pass123'}, follow_redirects=True)

    # Add to cart
    response = client.get(f'/add_to_cart/{product.id}', follow_redirects=True)
    assert response.status_code == 200

    # Go to cart
    response = client.get('/cart')
    assert b'Test Product' in response.data
    assert b'99.99' in response.data


def test_remove_from_cart(client):
    with app.app_context():
        user = User(username="remover", email="remover@example.com")
        user.set_password("pass123")
        product = Product(name="DelItem", description="To be deleted", price=50.0, image_url="http://img")
        db.session.add_all([user, product])
        db.session.commit()

        item = CartItem(user_id=user.id, product_id=product.id, quantity=2)
        db.session.add(item)
        db.session.commit()

    client.post('/login', data={'email': 'remover@example.com', 'password': 'pass123'}, follow_redirects=True)
    
    # Remove one
    response = client.get(f'/remove_from_cart/{product.id}', follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        remaining = CartItem.query.filter_by(user_id=user.id, product_id=product.id).first()
        assert remaining.quantity == 1

    # Remove last one
    client.get(f'/remove_from_cart/{product.id}', follow_redirects=True)
    with app.app_context():
        remaining = CartItem.query.filter_by(user_id=user.id, product_id=product.id).first()
        assert remaining is None
