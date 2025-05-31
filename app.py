from flask import Flask, render_template, request, redirect, session, make_response
import sqlite3
from datetime import datetime
from weasyprint import HTML

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'

# Dummy user data
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'waiter': {'password': 'waiter123', 'role': 'waiter'}
}

# Sample menu items
menu_items = {
    1: {"name": "Chicken Curry", "price": 10.0},
    2: {"name": "Fried Rice", "price": 8.0},
    3: {"name": "Coke", "price": 2.0},
    4: {"name": "Tea", "price": 1.5}
}

def get_db():
    return sqlite3.connect('hotel.db')

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    role = session['role']
    return render_template('dashboard.html', role=role)

@app.route('/menu')
def menu():
    if 'username' not in session or session['role'] != 'waiter':
        return redirect('/login')

    tables = [1, 2, 3, 4, 5]  # Sample table numbers
    return render_template('menu.html', menu_items=menu_items, tables=tables)

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'username' not in session or session['role'] != 'waiter':
        return redirect('/login')

    table_number = request.form.get('table_number')
    selected_items = request.form.getlist('items')  # list of item IDs as strings

    try:
        total = sum(menu_items[int(item_id)]["price"] for item_id in selected_items)
    except KeyError:
        return "Invalid item selected", 400

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO orders (table_number, items, total) VALUES (?, ?, ?)",
              (table_number, ','.join(selected_items), total))
    conn.commit()
    conn.close()

    return redirect(f"/bill/{table_number}")

@app.route('/bill/<table_number>')
def bill(table_number):
    if 'username' not in session or session['role'] != 'waiter':
        return redirect('/login')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY timestamp DESC LIMIT 1")
    current_order = c.fetchone()
    conn.close()

    if not current_order:
        return "No order found for this table"

    item_ids = current_order[2].split(',')
    items = [menu_items[int(i)] for i in item_ids]
    tax = round(current_order[3] * 0.1, 2)
    total_with_tax = round(current_order[3] + tax, 2)

    return render_template('bill.html',
                           table=table_number,
                           items=items,
                           subtotal=current_order[3],
                           tax=tax,
                           total=total_with_tax)

@app.route('/bill/<table_number>/pdf')
def bill_pdf(table_number):
    if 'username' not in session or session['role'] != 'waiter':
        return redirect('/login')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY timestamp DESC LIMIT 1")
    current_order = c.fetchone()
    conn.close()

    if not current_order:
        return "No order found for this table"

    item_ids = current_order[2].split(',')
    items = [menu_items[int(i)] for i in item_ids]
    tax = round(current_order[3] * 0.1, 2)
    total_with_tax = round(current_order[3] + tax, 2)

    html = render_template('bill.html',
                           table=table_number,
                           items=items,
                           subtotal=current_order[3],
                           tax=tax,
                           total=total_with_tax)

    pdf = HTML(string=html).write_pdf()

    return make_response(
        pdf,
        200,
        {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'inline; filename=bill_table_{table_number}.pdf'
        }
    )

@app.route('/kitchen')
def kitchen():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY timestamp DESC")
    orders = c.fetchall()
    conn.close()

    return render_template('kitchen.html', orders=orders, menu_items=menu_items)

@app.route('/update_status/<int:order_id>/<status>')
def update_status(order_id, status):
    if 'username' not in session:
        return redirect('/login')
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()
    return redirect('/kitchen')

@app.route('/report')
def report():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY timestamp DESC")
    orders = c.fetchall()

    daily_total = 0
    best_sellers = {}

    for order in orders:
        daily_total += order[3]
        item_ids = order[2].split(',')
        for item_id in item_ids:
            best_sellers[item_id] = best_sellers.get(item_id, 0) + 1

    best_seller_list = sorted(best_sellers.items(), key=lambda x: x[1], reverse=True)
    best_seller_names = [(menu_items[int(k)]['name'], v) for k, v in best_seller_list]
    today = datetime.now().strftime("%B %d, %Y")

    conn.close()

    return render_template('report.html',
                           daily_total=daily_total,
                           best_sellers=best_seller_names,
                           date=today)

@app.route('/inventory')
def inventory():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory")
    items = c.fetchall()
    conn.close()

    return render_template('inventory.html', items=items)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    import database
    database.init_db()
    app.run(debug=True)