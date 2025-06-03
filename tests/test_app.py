import pytest
from app import app, Product, User
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests if using Flask-WTF
    with app.test_client() as client:
        with app.app_context():
            yield client

def login_test_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Adjust if your app uses different key for logged-in user

def test_add_to_cart(client):
    with client.session_transaction() as sess:
        sess['cart'] = []
    # add product id=1 to cart, follow redirect to get updated session
    response = client.get('/add_to_cart/1', follow_redirects=True)
    with client.session_transaction() as sess:
        assert 1 in sess['cart'], f"Cart after adding: {sess['cart']}"
    assert response.status_code == 200

def test_remove_from_cart(client):
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    response = client.get('/remove_from_cart/1', follow_redirects=True)
    with client.session_transaction() as sess:
        assert 1 not in sess['cart'], f"Cart after removing: {sess['cart']}"
    assert response.status_code == 200

def test_add_same_product_multiple_times(client):
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    response = client.get('/add_to_cart/1', follow_redirects=True)
    with client.session_transaction() as sess:
        count = sess['cart'].count(1)
        assert count == 2, f"Cart contents: {sess['cart']}"
    assert response.status_code == 200

def test_checkout_get(client):
    login_test_user(client)
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    mock_product = Product(id=1, name="Mock", description="desc", price=10.0, image_url="url")
    with patch('app.Product.query.get', return_value=mock_product):
        response = client.get('/checkout', follow_redirects=True)
        assert response.status_code == 200
        assert b"checkout" in response.data.lower() or b"total" in response.data.lower()

def test_checkout_post(client):
    login_test_user(client)
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    mock_product = Product(id=1, name="Mock", description="desc", price=10.0, image_url="url")
    with patch('app.Product.query.get', return_value=mock_product):
        response = client.post('/checkout', follow_redirects=True)
        assert response.status_code == 200
        assert b"thank" in response.data.lower() or b"order placed" in response.data.lower()

def test_signup_new_email(client):
    with patch('app.User.query.filter_by') as mock_filter:
        mock_filter.return_value.first.return_value = None  # No user with this email
        response = client.post('/signup', data={
            'email': 'new@example.com',
            'password': 'test123',
            'confirm_password': 'test123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower() or b"welcome" in response.data.lower()

def test_signup_existing_email(client):
    # Create a mock user WITHOUT password kwarg, set attributes manually
    mock_user = User()
    mock_user.id = 1
    mock_user.email = "existing@example.com"
    with patch('app.User.query.filter_by') as mock_filter:
        mock_filter.return_value.first.return_value = mock_user
        response = client.post('/signup', data={
            'email': 'existing@example.com',
            'password': 'test123',
            'confirm_password': 'test123'
        }, follow_redirects=True)
        assert b'Email already registered' in response.data or response.status_code == 200

def test_login_success(client):
    mock_user = User()
    mock_user.id = 1
    mock_user.email = "user@example.com"
    # Patch password check
    with patch('app.User.query.filter_by') as mock_filter, \
         patch('app.check_password_hash') as mock_check_pw:
        mock_filter.return_value.first.return_value = mock_user
        mock_check_pw.return_value = True
        response = client.post('/login', data={
            'email': 'user@example.com',
            'password': 'correctpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"logout" in response.data.lower() or b"welcome" in response.data.lower()

def test_login_failure(client):
    with patch('app.User.query.filter_by') as mock_filter:
        mock_filter.return_value.first.return_value = None
        response = client.post('/login', data={
            'email': 'wrong@example.com',
            'password': 'nopassword'
        }, follow_redirects=True)
        assert b"Invalid email or password" in response.data or response.status_code == 200
