import pytest
from app import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.secret_key = "test-secret"
    with app.test_client() as client:
        yield client

@patch('app.Product')
def test_index_page(mock_product, client):
    mock_query = MagicMock()
    mock_query.paginate.return_value.items = [MagicMock(name="Product1", price=100)]
    mock_product.query = mock_query

    response = client.get('/')
    assert response.status_code == 200
    assert b"Product" in response.data or b"product" in response.data  # assuming template renders 'product'

@patch('app.Product')
def test_add_and_remove_cart(mock_product, client):
    mock_product.query.get.return_value = MagicMock(id=1, price=10)

    # Add to cart
    response = client.get('/add_to_cart/1', follow_redirects=True)
    assert response.status_code == 200

    # Check cart
    response = client.get('/cart')
    assert response.status_code == 200
    assert b"$" in response.data or b"INR" in response.data  # check for total

    # Remove from cart
    response = client.get('/remove_from_cart/1', follow_redirects=True)
    assert response.status_code == 200

def test_checkout_get(client):
    response = client.get('/checkout')
    assert response.status_code == 200

def test_checkout_post(client):
    with client.session_transaction() as sess:
        sess['cart'] = [1]
    with patch('app.Product.query.get') as mock_get:
        mock_get.return_value = MagicMock(id=1, price=10)
        response = client.post('/checkout')
        assert response.status_code == 200
