import pytest
from app import app, Product
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

# def test_product_detail_page(client):
#     mock_product = Product(id=1, name="Test Product", description="Desc", price=10.0, image_url="url")
#     with patch('app.Product.query.get_or_404', return_value=mock_product):
#         response = client.get('/product/1')
#         assert response.status_code == 200
#         assert b"Test Product" in response.data

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

def test_cart_view(client):
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Test Product"
    mock_product.price = 100.0
    mock_product.image_url = "http://example.com/image.jpg"

    with client.session_transaction() as sess:
        sess['cart'] = [1]

    with patch('app.Product.query.get', return_value=mock_product):  # or '__main__.Product.query.get'
        response = client.get('/cart', follow_redirects=True)
        print(response.data.decode())  # For debugging
        assert response.status_code == 200
        assert b'Test Product' in response.data

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
