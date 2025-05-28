from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'super-secret-key'

# SQLAlchemy DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:25258202Pr@database-1.cm14ws46qfvu.us-east-1.rds.amazonaws.com/product'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image_url = db.Column(db.String(255))

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 2  # number of products per page

    pagination = Product.query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    return render_template("index.html", products=products, pagination=pagination)
@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product.html", product=product)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', [])
    cart.append(product_id)
    session['cart'] = cart
    return redirect(request.referrer or url_for('index'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    if product_id in cart:
        cart.remove(product_id)
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    items = []
    total = 0
    for product_id in cart:
        product = Product.query.get(product_id)
        if product:
            items.append(product)
            total += product.price
    return render_template("cart.html", items=items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    items = []
    total = 0
    for product_id in cart:
        product = Product.query.get(product_id)
        if product:
            items.append(product)
            total += product.price

    if request.method == 'POST':
        session['cart'] = []
        return render_template('thankyou.html')

    return render_template("checkout.html", items=items, total=total)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
