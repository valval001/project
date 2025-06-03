import pytest
from app import app, db, User, Product, CartItem
from flask import session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # ✅ Safe test DB
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LOGIN_DISABLED'] = False

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def login(client, email, password):
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


def test_signup_and_login(client):
    with app.app_context():
        assert User.query.count() == 0

    # Sign up
    response = client.post('/signup', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password',
        'confirm_password': 'password'
    }, follow_redirects=True)

    assert b'Account created! Please log in.' in response.data

    # Login
    response = login(client, 'test@example.com', 'password')
    assert b'Logged in successfully.' in response.data


def test_add_product_and_cart(client):
    with app.app_context():
        user = User(username="buyer", email="buyer@example.com")
        user.set_password("pass123")
        product = Product(name="Sample Product", description="Test", price=99.99, image_url="http://image")
        db.session.add_all([user, product])
        db.session.commit()

    login(client, 'buyer@example.com', 'pass123')

    # Add product to cart
    response = client.get(f'/add_to_cart/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'cart' in session


def test_remove_from_cart(client):
    with app.app_context():
        user = User(username="remover", email="remover@example.com")
        user.set_password("pass123")
        product = Product(name="DelItem", description="To be deleted", price=50.0, image_url="http://img")
        db.session.add_all([user, product])
        db.session.commit()

        cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=2)
        db.session.add(cart_item)
        db.session.commit()

        product_id = product.id  # Save before session closes

    login(client, 'remover@example.com', 'pass123')

    # Remove one quantity
    response = client.get(f'/remove_from_cart/{product_id}', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        updated = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
        assert updated.quantity == 1
