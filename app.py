from flask import Flask, render_template, request, session, redirect, url_for
import pymysql
import os
from dotenv import load_dotenv
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for session
load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host='swiftcsv.mysql.pythonanywhere-services.com',
        user='swiftcsv',
        password=os.getenv("PYMYSQL_PASS"),
        database='swiftcsv$meddb'
    )

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/show', methods=['GET', 'POST'])
def show_inventory():
    connection = get_db_connection()

    # Filters and search
    search = request.args.get('search', '')
    composition_filter = request.args.get('composition', '')
    category_filter = request.args.get('category', '')
    price_filter = request.args.get('unit_price', '')

    query = "SELECT * FROM medicine_inventory WHERE 1=1"
    params = []
    if search:
        query += " AND name LIKE %s"
        params.append(f"%{search}%")
    if composition_filter:
        query += " AND composition = %s"
        params.append(composition_filter)
    if category_filter:
        query += " AND category = %s"
        params.append(category_filter)
    if price_filter:
        query += " AND unit_price <= %s"
        params.append(price_filter)

    df = pd.read_sql(query, connection, params=params)
    connection.close()

    # Get unique dropdown values
    connection = get_db_connection()
    compositions = pd.read_sql("SELECT DISTINCT composition FROM medicine_inventory", connection)['composition'].tolist()
    categories = pd.read_sql("SELECT DISTINCT category FROM medicine_inventory", connection)['category'].tolist()
    connection.close()

    return render_template(
        'inventory.html',
        table=df.to_dict(orient='records'),
        compositions=compositions,
        categories=categories,
        search=search
    )
@app.route('/add_to_cart/<medicine_id>')
def add_to_cart(medicine_id):
    connection = get_db_connection()
    df = pd.read_sql(
        "SELECT medicine_id, name, composition, category, unit_price FROM medicine_inventory WHERE medicine_id = %s",
        connection,
        params=[medicine_id]
    )

    if df.empty:
        connection.close()
        return "Medicine not found", 404

    # Insert into billing table
    cursor = connection.cursor()
    insert_query = """
        INSERT INTO billing (medicine_id, name, composition, category, unit_price)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        df.at[0, 'medicine_id'],
        df.at[0, 'name'],
        df.at[0, 'composition'],
        df.at[0, 'category'],
        float(df.at[0, 'unit_price'])
    ))
    connection.commit()
    cursor.close()
    connection.close()

    # Add to session cart (optional)
    if 'cart' not in session:
        session['cart'] = []

    existing_ids = [item['medicine_id'] for item in session['cart']]
    if medicine_id not in existing_ids:
        session['cart'].append(df.to_dict(orient='records')[0])
        session.modified = True

    return redirect(url_for('show_inventory'))

@app.route('/billing')
def billing():
    cart = session.get('cart', [])
    total = sum(float(item['unit_price']) for item in cart)
    return render_template('billing.html', cart=cart, total=total)

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('show_inventory'))
