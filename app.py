from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import mysql.connector
from datetime import datetime
import bcrypt
from functools import wraps

app = Flask(__name__)

# --- Role-Based Access Control ---
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                flash("Please log in to access this page.", "error")
                return redirect(url_for('login'))
            if session['role'] not in allowed_roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
app.secret_key = 'your_secret_key_here'  # Change this to a secure key

# --- Configuration (UPDATE THESE) ---
DB_CONFIGS = {
    "admin": {
        "host": "localhost",
        "user": "admin",
        "password": "admin",
        "database": "Tourism_and_Travel_Booking_System"
    },
    "agent": {
        "host": "localhost",
        "user": "agent",
        "password": "agent",
        "database": "Tourism_and_Travel_Booking_System"
    },
    "accountant": {
        "host": "localhost",
        "user": "accountant",
        "password": "accountant",
        "database": "Tourism_and_Travel_Booking_System"
    }
}
# -----------------------------------

# --- Database Connection ---
def connect_db(role='admin'):
    """Establishes a connection to the MySQL database based on user role."""
    config = DB_CONFIGS.get(role, DB_CONFIGS['admin'])
    try:
        con = mysql.connector.connect(**config)
        return con
    except Exception as e:
        flash(f"Database Connection Error: Could not connect to database. Please check your config.\nError: {e}", "error")
        return None

# --- Utility Functions ---
def validate_int_input(value, field_name):
    """Validates if a value is a positive integer."""
    if not value or not value.isdigit() or int(value) <= 0:
        flash(f"'{field_name}' must be a positive integer.", "error")
        return False
    return True

def validate_float_input(value, field_name):
    """Validates if a value is a non-negative number."""
    try:
        f_val = float(value)
        if f_val < 0:
            raise ValueError
        return True
    except (ValueError, TypeError):
        flash(f"'{field_name}' must be a non-negative number.", "error")
        return False

# --- Dashboard Refresh ---
def refresh_dashboard(role):
    """Fetches and updates the counts for the dashboard summary."""
    con = connect_db(role)
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM Customer;")
            total_customers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM Booking;")
            total_bookings = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM Payment;")
            total_payments = cur.fetchone()[0]

            return total_customers, total_bookings, total_payments
        except Exception as e:
            flash(f"Dashboard Error: Failed to load dashboard data: {e}", "error")
            return 0, 0, 0
        finally:
            con.close()
    return 0, 0, 0

# --- PACKAGE UTILITIES ---
def load_packages():
    """
    Fetches package names, IDs, and prices.
    Returns: {PackageName: (PackageID, PackagePrice)}
    """
    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT PackageName, PackageID, PackagePrice FROM TourPackage;")
            packages = cur.fetchall()
            return {name: (pid, price) for name, pid, price in packages}
        except Exception:
            return {}
        finally:
            con.close()
    return {}

package_map = load_packages()

def update_package_menu():
    """Refreshes the package map."""
    global package_map
    package_map = load_packages()

# --- Authentication Routes ---

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for('login'))

    # Determine role based on username
    role = None
    if username == 'admin':
        role = 'admin'
    elif username == 'agent':
        role = 'agent'
    elif username == 'accountant':
        role = 'accountant'

    if not role:
        flash("Invalid username or password.", "error")
        return redirect(url_for('login'))

    con = connect_db(role)
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT UserID, Username, Role, PasswordHash FROM AppUser WHERE Username = %s", (username,))
            user = cur.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[2]
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for('index'))
            else:
                flash("Invalid username or password.", "error")
        except mysql.connector.Error as err:
            flash(f"Login error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if not username or not password or not role:
        flash("All fields are required.", "error")
        return redirect(url_for('register'))

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            # Check if username already exists
            cur.execute("SELECT UserID FROM AppUser WHERE Username = %s", (username,))
            if cur.fetchone():
                flash("Username already exists.", "error")
                return redirect(url_for('register'))

            cur.execute("INSERT INTO AppUser (Username, PasswordHash, Role) VALUES (%s, %s, %s)", (username, hashed_password, role))
            con.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Registration error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('register'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

# --- Routes ---

@app.route('/')
def index():
    role = session.get('role', 'admin')
    total_customers, total_bookings, total_payments = refresh_dashboard(role)
    return render_template('index.html', total_customers=total_customers, total_bookings=total_bookings, total_payments=total_payments)

# --- Protected Routes ---
@app.route('/customers')
@role_required(['admin', 'agent', 'accountant'])
def customers():
    role = session.get('role')
    con = connect_db(role)
    customer_list = []
    customers = []
    dependents = []
    next_customer_id = 1
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT CustomerID, Cname FROM Customer;")
            customer_list = cur.fetchall()
            cur.execute("""
                SELECT c1.CustomerID, c1.Cname, c1.Email, c1.State, c1.City, c1.Country, c1.Refers
                FROM Customer c1;
            """)
            customers = cur.fetchall()
            cur.execute("SELECT DependentID, DependentName, Age, Relation, CustomerID FROM TravelDependent;")
            dependents = cur.fetchall()
            cur.execute("SELECT MAX(CustomerID) FROM Customer;")
            max_id = cur.fetchone()[0]
            next_customer_id = (max_id or 0) + 1
        except Exception as e:
            flash(f"Error loading customers: {e}", "error")
        finally:
            con.close()
    return render_template('customers.html', customer_list=customer_list, customers=customers, dependents=dependents, next_customer_id=next_customer_id)

@app.route('/customers/view')
@role_required(['admin', 'agent', 'accountant'])
def view_customers():
    con = connect_db()
    if con:
        cur = con.cursor()
        cur.execute("""
            SELECT c1.CustomerID, c1.Cname, c1.Email, c1.State, c1.City, c1.Country, c1.Refers
            FROM Customer c1;
        """)
        rows = cur.fetchall()
        con.close()
        return render_template('customers.html', customers=rows)
    return render_template('customers.html', customers=[])

@app.route('/customers/add', methods=['POST'])
@role_required(['admin', 'agent'])
def add_customer():
    c_id = request.form.get('customer_id')
    refers = request.form.get('refers')
    if not validate_int_input(c_id, "Customer ID") or not refers or not validate_int_input(refers, "Refers"): return redirect(url_for('customers'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO Customer (CustomerID, Cname, Email, State, City, Country, Refers) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (int(c_id), request.form.get('name'), request.form.get('email'),
                 request.form.get('state'), request.form.get('city'),
                 request.form.get('country'), int(refers))
            )
            con.commit()
            flash("Customer added successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('customers'))

@app.route('/customers/update', methods=['GET', 'POST'])
@role_required(['admin', 'agent'])
def update_customer():
    if request.method == 'GET':
        return redirect(url_for('customers'))
    c_id = request.form.get('customer_id')
    refers = request.form.get('refers')
    if not validate_int_input(c_id, "Customer ID"): return redirect(url_for('customers'))
    if not refers or not validate_int_input(refers, "Refers"): return redirect(url_for('customers'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE Customer SET Cname=%s, Email=%s, State=%s, City=%s, Country=%s, Refers=%s WHERE CustomerID=%s",
                (request.form.get('name'), request.form.get('email'),
                 request.form.get('state'), request.form.get('city'),
                 request.form.get('country'), int(refers), c_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Customer {c_id} updated successfully!", "success")
            else:
                flash(f"Customer ID {c_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('customers'))

@app.route('/customers/delete', methods=['POST'])
@role_required(['admin', 'agent'])
def delete_customer():
    c_id = request.form.get('customer_id')
    if not validate_int_input(c_id, "Customer ID"): return redirect(url_for('customers'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM Customer WHERE CustomerID=%s", (c_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Customer {c_id} deleted successfully!", "success")
            else:
                flash(f"Customer ID {c_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Cannot delete customer. Ensure no related bookings exist.\nError: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('customers'))

@app.route('/customers/add_dependent', methods=['POST'])
@role_required(['admin', 'agent'])
def add_dependent():
    d_name = request.form.get('dependent_name')
    age = request.form.get('age')
    relation = request.form.get('relation')
    c_id = request.form.get('customer_id')

    if not d_name:
        flash("Dependent Name cannot be empty.", "error")
        return redirect(url_for('customers'))
    if not validate_int_input(age, "Age"): return redirect(url_for('customers'))
    if not relation:
        flash("Relation cannot be empty.", "error")
        return redirect(url_for('customers'))
    if not validate_int_input(c_id, "Customer ID"): return redirect(url_for('customers'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO TravelDependent (DependentName, Age, Relation, CustomerID) VALUES (%s, %s, %s, %s)",
                (d_name, int(age), relation, c_id)
            )
            con.commit()
            flash(f"Travel Dependent '{d_name}' added successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Database error (Check Customer ID):\n{err}", "error")
        finally:
            con.close()
    return redirect(url_for('customers'))

@app.route('/customers/delete_dependent', methods=['POST'])
@role_required(['admin', 'agent'])
def delete_dependent():
    d_id = request.form.get('dependent_id')
    if not validate_int_input(d_id, "Dependent ID"): return redirect(url_for('customers'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM TravelDependent WHERE DependentID=%s", (d_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Travel Dependent {d_id} deleted successfully!", "success")
            else:
                flash(f"Dependent ID {d_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Cannot delete dependent.\nError: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('customers'))

@app.route('/customers/update_dependent', methods=['GET', 'POST'])
@role_required(['admin', 'agent'])
def update_dependent():
    if request.method == 'GET':
        return redirect(url_for('customers'))
    d_id = request.form.get('dependent_id')
    d_name = request.form.get('dependent_name')
    age = request.form.get('age')
    relation = request.form.get('relation')
    c_id = request.form.get('customer_id')

    if not validate_int_input(d_id, "Dependent ID"): return redirect(url_for('customers'))
    if not d_name:
        flash("Dependent Name cannot be empty.", "error")
        return redirect(url_for('customers'))
    if not validate_int_input(age, "Age"): return redirect(url_for('customers'))
    if not relation:
        flash("Relation cannot be empty.", "error")
        return redirect(url_for('customers'))
    if not validate_int_input(c_id, "Customer ID"): return redirect(url_for('customers'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE TravelDependent SET DependentName=%s, Age=%s, Relation=%s, CustomerID=%s WHERE DependentID=%s",
                (d_name, int(age), relation, c_id, d_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Travel Dependent {d_id} updated successfully!", "success")
            else:
                flash(f"Dependent ID {d_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('customers'))

@app.route('/customers/view_dependents')
def view_dependents():
    con = connect_db()
    dependents = []
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT DependentID, DependentName, Age, Relation, CustomerID FROM TravelDependent;")
            dependents = cur.fetchall()
        except Exception as e:
            flash(f"Error loading dependents: {e}", "error")
        finally:
            con.close()
    return render_template('customers.html', dependents=dependents)

@app.route('/bookings')
@role_required(['admin', 'agent', 'accountant'])
def bookings():
    update_package_menu()
    con = connect_db()
    bookings = []
    next_booking_id = 1
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT BookingID, BookingDate, Status, CustomerID, PackageID FROM Booking;")
            bookings = cur.fetchall()
            cur.execute("SELECT MAX(BookingID) FROM Booking;")
            max_id = cur.fetchone()[0]
            next_booking_id = (max_id or 0) + 1
        except Exception as e:
            flash(f"Error loading bookings: {e}", "error")
        finally:
            con.close()
    return render_template('bookings.html', packages=list(package_map.keys()), bookings=bookings, next_booking_id=next_booking_id)

@app.route('/bookings/view')
def view_bookings():
    con = connect_db()
    if con:
        cur = con.cursor()
        cur.execute("SELECT BookingID, BookingDate, Status, CustomerID, PackageID FROM Booking;")
        rows = cur.fetchall()
        con.close()
        return render_template('bookings.html', bookings=rows, packages=list(package_map.keys()))
    return render_template('bookings.html', bookings=[], packages=list(package_map.keys()))

@app.route('/bookings/add', methods=['POST'])
@role_required(['admin', 'agent'])
def add_booking():
    b_id = request.form.get('booking_id')
    c_id = request.form.get('customer_id')
    p_id = request.form.get('package_id')
    if not validate_int_input(b_id, "Booking ID") or not validate_int_input(c_id, "Customer ID") or not validate_int_input(p_id, "Package ID"): return redirect(url_for('bookings'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            # 1. Insert into Booking table
            cur.execute(
                "INSERT INTO Booking (BookingID, BookingDate, Status, CustomerID, PackageID) VALUES (%s,%s,%s,%s,%s)",
                (b_id, request.form.get('booking_date'), request.form.get('status'), c_id, p_id)
            )

            con.commit()
            flash(f"Booking {b_id} added successfully!", "success")

        except mysql.connector.Error as err:
            flash(f"Database error (Check Customer ID and Package ID):\n{err}", "error")
        except ValueError as err:
            flash(str(err), "error")
        finally:
            con.close()
    return redirect(url_for('bookings'))

@app.route('/bookings/delete', methods=['POST'])
@role_required(['admin', 'agent'])
def delete_booking():
    b_id = request.form.get('booking_id')
    if not validate_int_input(b_id, "Booking ID"): return redirect(url_for('bookings'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM Booking WHERE BookingID=%s", (b_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Booking {b_id} deleted successfully!", "success")
            else:
                flash(f"Booking ID {b_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Cannot delete booking. Delete dependent records first.\nError: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('bookings'))

@app.route('/bookings/update', methods=['GET', 'POST'])
def update_booking():
    if request.method == 'GET':
        return redirect(url_for('bookings'))
    b_id = request.form.get('booking_id')
    c_id = request.form.get('customer_id')
    p_id = request.form.get('package_id')
    if not validate_int_input(b_id, "Booking ID") or not validate_int_input(c_id, "Customer ID") or not validate_int_input(p_id, "Package ID"): return redirect(url_for('bookings'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE Booking SET BookingDate=%s, Status=%s, CustomerID=%s, PackageID=%s WHERE BookingID=%s",
                (request.form.get('booking_date'), request.form.get('status'), c_id, p_id, b_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Booking {b_id} updated successfully!", "success")
            else:
                flash(f"Booking ID {b_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error (Check Customer ID and Package ID):\n{err}", "error")
        finally:
            con.close()
    return redirect(url_for('bookings'))

@app.route('/payments')
def payments():
    con = connect_db()
    payments = []
    next_payment_id = 1
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT PaymentID, Amount, PaymentDate, PaymentMethod, BookingID FROM Payment;")
            payments = cur.fetchall()
            cur.execute("SELECT MAX(PaymentID) FROM Payment;")
            max_id = cur.fetchone()[0]
            next_payment_id = (max_id or 0) + 1
        except Exception as e:
            flash(f"Error loading payments: {e}", "error")
        finally:
            con.close()
    return render_template('payments.html', payments=payments, next_payment_id=next_payment_id)

@app.route('/payments/view')
def view_payments():
    con = connect_db()
    if con:
        cur = con.cursor()
        cur.execute("SELECT PaymentID, Amount, PaymentDate, PaymentMethod, BookingID FROM Payment;")
        rows = cur.fetchall()
        con.close()
        return render_template('payments.html', payments=rows)
    return render_template('payments.html', payments=[])

@app.route('/payments/add', methods=['POST'])
@role_required(['admin', 'accountant'])
def add_payment():
    p_id = request.form.get('payment_id')
    b_id = request.form.get('booking_id')
    amount = request.form.get('amount')
    if not validate_int_input(p_id, "Payment ID") or not validate_int_input(b_id, "Booking ID") or not validate_float_input(amount, "Amount"): return redirect(url_for('payments'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            # Insert payment with provided amount
            cur.execute(
                "INSERT INTO Payment (PaymentID, Amount, PaymentDate, PaymentMethod, BookingID) VALUES (%s,%s,%s,%s,%s)",
                (p_id, float(amount), request.form.get('payment_date'), request.form.get('method'), b_id)
            )
            con.commit()
            flash(f"Payment {p_id} added successfully! Amount: ₹{float(amount):.2f}", "success")
        except mysql.connector.Error as err:
            flash(f"Database error (Check Booking ID):\n{err}", "error")
        finally:
            con.close()
    return redirect(url_for('payments'))

@app.route('/payments/delete', methods=['POST'])
@role_required(['admin', 'accountant'])
def delete_payment():
    p_id = request.form.get('payment_id')
    if not validate_int_input(p_id, "Payment ID"): return redirect(url_for('payments'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM Payment WHERE PaymentID = %s", (p_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Payment {p_id} deleted successfully!", "success")
            else:
                flash(f"Payment ID {p_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('payments'))

@app.route('/payments/update', methods=['GET', 'POST'])
@role_required(['admin', 'accountant'])
def update_payment():
    if request.method == 'GET':
        return redirect(url_for('payments'))
    p_id = request.form.get('payment_id')
    b_id = request.form.get('booking_id')
    amount = request.form.get('amount')
    if not validate_int_input(p_id, "Payment ID") or not validate_int_input(b_id, "Booking ID") or not validate_float_input(amount, "Amount"): return redirect(url_for('payments'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE Payment SET Amount=%s, PaymentDate=%s, PaymentMethod=%s, BookingID=%s WHERE PaymentID=%s",
                (float(amount), request.form.get('payment_date'), request.form.get('method'), b_id, p_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Payment {p_id} updated successfully!", "success")
            else:
                flash(f"Payment ID {p_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('payments'))

@app.route('/packages')
def packages():
    update_package_menu()
    # Fetch package list for display
    con = connect_db()
    package_list = []
    next_package_id = 1
    if con:
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT tp.PackageID, tp.PackageName, tp.PackagePrice, tp.Duration, tp.No_of_Travelers
                FROM TourPackage tp;
            """)
            package_list = cur.fetchall()
            cur.execute("SELECT MAX(PackageID) FROM TourPackage;")
            max_id = cur.fetchone()[0]
            next_package_id = (max_id or 0) + 1
        except Exception as e:
            flash(f"Error loading packages: {e}", "error")
        finally:
            con.close()
    return render_template('packages.html', packages=list(package_map.keys()), package_list=package_list, next_package_id=next_package_id)

@app.route('/packages/view')
def view_packages():
    con = connect_db()
    if con:
        cur = con.cursor()
        cur.execute("""
            SELECT tp.PackageID, tp.PackageName, tp.PackagePrice, tp.Duration, tp.No_of_Travelers
            FROM TourPackage tp;
        """)
        rows = cur.fetchall()
        con.close()
        return render_template('packages.html', package_list=rows, packages=list(package_map.keys()))
    return render_template('packages.html', package_list=[], packages=list(package_map.keys()))

@app.route('/packages/add', methods=['POST'])
@role_required(['admin', 'agent'])
def add_package():
    p_id = request.form.get('package_id')
    p_name = request.form.get('package_name')
    p_price = request.form.get('price')
    p_duration = request.form.get('duration')
    p_travelers = request.form.get('travelers')

    if not validate_int_input(p_id, "Package ID"): return redirect(url_for('packages'))
    if not p_name:
        flash("Package Name cannot be empty.", "error")
        return redirect(url_for('packages'))
    if not validate_float_input(p_price, "Price"): return redirect(url_for('packages'))
    if not validate_int_input(p_duration, "Duration"): return redirect(url_for('packages'))
    if not validate_int_input(p_travelers, "Number of Travelers"): return redirect(url_for('packages'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO TourPackage (PackageID, PackageName, PackagePrice, Duration, No_of_Travelers) VALUES (%s, %s, %s, %s, %s)",
                (int(p_id), p_name, float(p_price), int(p_duration), int(p_travelers))
            )
            con.commit()
            flash(f"New Package '{p_name}' (ID: {p_id}) added successfully!", "success")
            update_package_menu()
        except mysql.connector.Error as err:
            flash(f"Database error:\n{err}", "error")
        finally:
            con.close()
    return redirect(url_for('packages'))



@app.route('/packages/delete', methods=['POST'])
@role_required(['admin', 'agent'])
def delete_package():
    p_id = request.form.get('package_id')
    if not validate_int_input(p_id, "Package ID"): return redirect(url_for('packages'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM TourPackage WHERE PackageID=%s", (p_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Package {p_id} deleted successfully!", "success")
                update_package_menu()
            else:
                flash(f"Package ID {p_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Cannot delete package. Ensure no related bookings exist.\nError: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('packages'))

@app.route('/packages/update', methods=['GET', 'POST'])
def update_package():
    if request.method == 'GET':
        return redirect(url_for('packages'))
    p_id = request.form.get('package_id')
    p_name = request.form.get('package_name')
    p_price = request.form.get('price')
    p_duration = request.form.get('duration')
    p_travelers = request.form.get('travelers')
    if not validate_int_input(p_id, "Package ID") or not p_name or not validate_float_input(p_price, "Price") or not validate_int_input(p_duration, "Duration") or not validate_int_input(p_travelers, "Number of Travelers"): return redirect(url_for('packages'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE TourPackage SET PackageName=%s, PackagePrice=%s, Duration=%s, No_of_Travelers=%s WHERE PackageID=%s",
                (p_name, float(p_price), int(p_duration), int(p_travelers), p_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Package {p_id} updated successfully!", "success")
                update_package_menu()
            else:
                flash(f"Package ID {p_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('packages'))

@app.route('/procedures')
def procedures():
    return render_template('procedures.html')

@app.route('/procedures/run_procedure', methods=['POST'])
def run_procedure():
    p_id = request.form.get('package_id')
    if not validate_int_input(p_id, "Package ID"): return redirect(url_for('procedures'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            # Check if package exists
            cur.execute("SELECT PackageID FROM TourPackage WHERE PackageID = %s", (int(p_id),))
            if not cur.fetchone():
                flash(f"Package ID {p_id} does not exist.", "error")
                return redirect(url_for('procedures'))

            cur.callproc('calculate_package_total_cost', (int(p_id),))
            results = []
            for result in cur.stored_results():
                rows = result.fetchall()
                results.extend(rows)

            return render_template('procedures.html', procedure_results=results, package_id=p_id)

        except mysql.connector.Error as err:
            flash(f"Procedure Error: Failed to execute procedure: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('procedures'))

@app.route('/procedures/run_function', methods=['POST'])
def run_function():
    c_id = request.form.get('customer_id')
    if not validate_int_input(c_id, "Customer ID"): return redirect(url_for('procedures'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(f"SELECT TotalAmountSpent({c_id});")
            result = cur.fetchone()
            if result and result[0] is not None:
                total_spent = f"Total Amount Spent: ₹{result[0]:,.2f}"
            else:
                total_spent = "Total Amount Spent: ₹0.00 (Customer not found or no payments)"
            return render_template('procedures.html', function_result=total_spent)

        except mysql.connector.Error as err:
            flash(f"Function Error: Failed to execute function: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('procedures'))

@app.route('/queries')
def queries():
    return render_template('queries.html')

@app.route('/queries/run_a')
def run_query_a():
    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT c.Cname, COUNT(td.DependentName) AS Total_Dependents
                FROM Customer c
                LEFT JOIN TravelDependent td ON c.CustomerID = td.CustomerID
                GROUP BY c.CustomerID;
            """)
            rows = cur.fetchall()
            con.close()
            return render_template('queries.html', query_a_results=rows)
        except mysql.connector.Error as err:
            flash(f"Query Error (a): Failed to run query:\n{err}", "error")
    return redirect(url_for('queries'))

@app.route('/queries/run_b')
def run_query_b():
    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT PackageName, PackagePrice FROM TourPackage
                ORDER BY PackagePrice DESC LIMIT 3;
            """)
            rows = cur.fetchall()
            con.close()
            return render_template('queries.html', query_b_results=rows)
        except mysql.connector.Error as err:
            flash(f"Query Error (b): Failed to run query:\n{err}", "error")
    return redirect(url_for('queries'))

@app.route('/queries/run_c')
def run_query_c():
    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT b.BookingID, c.Cname, h.HotelName, h.Rating
                FROM Booking b
                JOIN Customer c ON b.CustomerID = c.CustomerID
                JOIN Itinerary i ON b.BookingID = i.BookingID
                JOIN Hotel h ON i.HotelID = h.HotelID
                WHERE b.Status = 'Confirmed' OR b.Status = 'Paid';
            """)
            rows = cur.fetchall()
            con.close()
            return render_template('queries.html', query_c_results=rows)
        except mysql.connector.Error as err:
            flash(f"Query Error (c): Failed to run query:\n{err}", "error")
    return redirect(url_for('queries'))

# --- Destinations Routes ---
@app.route('/destinations')
def destinations():
    con = connect_db()
    destinations = []
    next_destination_id = 1
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT DestinationID, DestinationName, Dlocation FROM Destination;")
            destinations = cur.fetchall()
            cur.execute("SELECT MAX(DestinationID) FROM Destination;")
            max_id = cur.fetchone()[0]
            next_destination_id = (max_id or 0) + 1
        except Exception as e:
            flash(f"Error loading destinations: {e}", "error")
        finally:
            con.close()
    return render_template('destinations.html', destinations=destinations, next_destination_id=next_destination_id)

@app.route('/destinations/view')
def view_destinations():
    con = connect_db()
    if con:
        cur = con.cursor()
        cur.execute("SELECT DestinationID, DestinationName, Dlocation FROM Destination;")
        rows = cur.fetchall()
        con.close()
        return render_template('destinations.html', destinations=rows)
    return render_template('destinations.html', destinations=[])

@app.route('/destinations/add', methods=['POST'])
@role_required(['admin'])
def add_destination():
    d_id = request.form.get('destination_id')
    if not validate_int_input(d_id, "Destination ID"): return redirect(url_for('destinations'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO Destination (DestinationID, DestinationName, Dlocation) VALUES (%s,%s,%s)",
                (d_id, request.form.get('destination_name'), request.form.get('dlocation'))
            )
            con.commit()
            flash(f"Destination {d_id} added successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('destinations'))

@app.route('/destinations/delete', methods=['POST'])
@role_required(['admin'])
def delete_destination():
    d_id = request.form.get('destination_id')
    if not validate_int_input(d_id, "Destination ID"): return redirect(url_for('destinations'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM Destination WHERE DestinationID=%s", (d_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Destination {d_id} deleted successfully!", "success")
            else:
                flash(f"Destination ID {d_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Cannot delete destination. Ensure no related records exist.\nError: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('destinations'))

@app.route('/destinations/update', methods=['POST'])
def update_destination():
    d_id = request.form.get('destination_id')
    if not validate_int_input(d_id, "Destination ID"): return redirect(url_for('destinations'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE Destination SET DestinationName=%s, Dlocation=%s WHERE DestinationID=%s",
                (request.form.get('destination_name'), request.form.get('dlocation'), d_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Destination {d_id} updated successfully!", "success")
            else:
                flash(f"Destination ID {d_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('destinations'))

# --- Hotels Routes ---
@app.route('/hotels')
def hotels():
    con = connect_db()
    hotels = []
    next_hotel_id = 1
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT HotelID, HotelName, Address, Rating, HotelPrice FROM Hotel;")
            hotels = cur.fetchall()
            cur.execute("SELECT MAX(HotelID) FROM Hotel;")
            max_id = cur.fetchone()[0]
            next_hotel_id = (max_id or 0) + 1
        except Exception as e:
            flash(f"Error loading hotels: {e}", "error")
        finally:
            con.close()
    return render_template('hotels.html', hotels=hotels, next_hotel_id=next_hotel_id)

@app.route('/hotels/view')
def view_hotels():
    con = connect_db()
    if con:
        cur = con.cursor()
        cur.execute("SELECT HotelID, HotelName, Address, Rating, HotelPrice FROM Hotel;")
        rows = cur.fetchall()
        con.close()
        return render_template('hotels.html', hotels=rows)
    return render_template('hotels.html', hotels=[])

@app.route('/hotels/add', methods=['POST'])
@role_required(['admin'])
def add_hotel():
    h_id = request.form.get('hotel_id')
    rating = request.form.get('rating')
    price = request.form.get('hotel_price')
    if not validate_int_input(h_id, "Hotel ID") or not validate_float_input(rating, "Rating") or not validate_float_input(price, "Hotel Price"): return redirect(url_for('hotels'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO Hotel (HotelID, HotelName, Address, Rating, HotelPrice) VALUES (%s,%s,%s,%s,%s)",
                (h_id, request.form.get('hotel_name'), request.form.get('address'), float(rating), float(price))
            )
            con.commit()
            flash(f"Hotel {h_id} added successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('hotels'))

@app.route('/hotels/delete', methods=['POST'])
@role_required(['admin'])
def delete_hotel():
    h_id = request.form.get('hotel_id')
    if not validate_int_input(h_id, "Hotel ID"): return redirect(url_for('hotels'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM Hotel WHERE HotelID=%s", (h_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Hotel {h_id} deleted successfully!", "success")
            else:
                flash(f"Hotel ID {h_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Cannot delete hotel. Ensure no related records exist.\nError: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('hotels'))

@app.route('/hotels/update', methods=['GET', 'POST'])
def update_hotel():
    if request.method == 'GET':
        return redirect(url_for('hotels'))
    h_id = request.form.get('hotel_id')
    rating = request.form.get('rating')
    price = request.form.get('hotel_price')
    if not validate_int_input(h_id, "Hotel ID") or not validate_float_input(rating, "Rating") or not validate_float_input(price, "Hotel Price"): return redirect(url_for('hotels'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE Hotel SET HotelName=%s, Address=%s, Rating=%s, HotelPrice=%s WHERE HotelID=%s",
                (request.form.get('hotel_name'), request.form.get('address'), float(rating), float(price), h_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Hotel {h_id} updated successfully!", "success")
            else:
                flash(f"Hotel ID {h_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('hotels'))

# --- Transport Routes ---
@app.route('/transports')
def transports():
    con = connect_db()
    transports = []
    next_transport_id = 1
    if con:
        cur = con.cursor()
        try:
            cur.execute("SELECT TransportID, TransportType, DepartLocation, ArrivalLocation, DepartDateTime, ArrivalDateTime, TransportPrice FROM Transport;")
            transports = cur.fetchall()
            cur.execute("SELECT MAX(TransportID) FROM Transport;")
            max_id = cur.fetchone()[0]
            next_transport_id = (max_id or 0) + 1
        except Exception as e:
            flash(f"Error loading transports: {e}", "error")
        finally:
            con.close()
    return render_template('transports.html', transports=transports, next_transport_id=next_transport_id)

@app.route('/transports/view')
def view_transports():
    con = connect_db()
    if con:
        cur = con.cursor()
        cur.execute("SELECT TransportID, TransportType, DepartLocation, ArrivalLocation, DepartDateTime, ArrivalDateTime, TransportPrice FROM Transport;")
        rows = cur.fetchall()
        con.close()
        return render_template('transports.html', transports=rows)
    return render_template('transports.html', transports=[])

@app.route('/transports/add', methods=['POST'])
@role_required(['admin'])
def add_transport():
    t_id = request.form.get('transport_id')
    if not validate_int_input(t_id, "Transport ID"): return redirect(url_for('transports'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO Transport (TransportID, TransportType, DepartLocation, ArrivalLocation, DepartDateTime, ArrivalDateTime, TransportPrice) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (t_id, request.form.get('transport_type'), request.form.get('depart_location'), request.form.get('arrival_location'), request.form.get('depart_datetime'), request.form.get('arrival_datetime'), request.form.get('transport_price'))
            )
            con.commit()
            flash(f"Transport {t_id} added successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('transports'))

@app.route('/transports/delete', methods=['POST'])
@role_required(['admin'])
def delete_transport():
    t_id = request.form.get('transport_id')
    if not validate_int_input(t_id, "Transport ID"): return redirect(url_for('transports'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM Transport WHERE TransportID=%s", (t_id,))
            if cur.rowcount > 0:
                con.commit()
                flash(f"Transport {t_id} deleted successfully!", "success")
            else:
                flash(f"Transport ID {t_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Cannot delete transport. Ensure no related records exist.\nError: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('transports'))

@app.route('/transports/update', methods=['GET', 'POST'])
def update_transport():
    if request.method == 'GET':
        return redirect(url_for('transports'))
    t_id = request.form.get('transport_id')
    price = request.form.get('transport_price')
    if not validate_int_input(t_id, "Transport ID") or not validate_float_input(price, "Transport Price"): return redirect(url_for('transports'))

    con = connect_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE Transport SET TransportType=%s, DepartLocation=%s, ArrivalLocation=%s, DepartDateTime=%s, ArrivalDateTime=%s, TransportPrice=%s WHERE TransportID=%s",
                (request.form.get('transport_type'), request.form.get('depart_location'), request.form.get('arrival_location'), request.form.get('depart_datetime'), request.form.get('arrival_datetime'), float(price), t_id)
            )
            if cur.rowcount > 0:
                con.commit()
                flash(f"Transport {t_id} updated successfully!", "success")
            else:
                flash(f"Transport ID {t_id} not found.", "warning")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            con.close()
    return redirect(url_for('transports'))

if __name__ == '__main__':
    app.run(debug=True)
