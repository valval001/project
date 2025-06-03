import pytest
import os
from app import app, db, User, Product, CartItem
from flask_login import login_user
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_database.db'  # Local test DB

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()  # Clean slate for test DB
            db.create_all()

            # Create test user
            test_user = User(username='testuser', email='test@example.com')
            test_user.password_hash = generate_password_hash('testpass')
            db.session.add(test_user)

            # Create test product
            test_product = Product(name='Test Product', description='desc', price=10.0, image_url='url')
            db.session.add(test_product)

            db.session.commit()

        yield client

        # Teardown: clean test DB
        with app.app_context():
            db.session.remove()
            db.drop_all()
        if os.path.exists("test_database.db"):
            os.remove("test_database.db")

def login(client, email='test@example.com', password='testpass'):
    return client.post('/login', data=dict(email=email, password=password), follow_redirects=True)

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Product" in response.data or b"No products" in response.data

def test_add_to_cart(client):
    login(client)
    response = client.get('/add_to_cart/1', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        cart_item = CartItem.query.filter_by(user_id=user.id, product_id=1).first()
        assert cart_item is not None
        assert cart_item.quantity == 1

def test_remove_from_cart(client):
    login(client)
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        cart_item = CartItem(user_id=user.id, product_id=1, quantity=1)
        db.session.add(cart_item)
        db.session.commit()

    response = client.get('/remove_from_cart/1', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        cart_item = CartItem.query.filter_by(user_id=user.id, product_id=1).first()
        assert cart_item is None

def test_checkout_get(client):
    login(client)
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        cart_item = CartItem(user_id=user.id, product_id=1, quantity=2)
        db.session.add(cart_item)
        db.session.commit()

    response = client.get('/checkout')
    assert response.status_code == 200
    assert b"Checkout" in response.data or b"Total" in response.data

def test_checkout_post(client):
    login(client)
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        cart_item = CartItem(user_id=user.id, product_id=1, quantity=2)
        db.session.add(cart_item)
        db.session.commit()

    response = client.post('/checkout', follow_redirects=True)
    assert response.status_code == 200
    assert b"thank" in response.data.lower()

    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        assert len(cart_items) == 0  # Cart should be cleared
