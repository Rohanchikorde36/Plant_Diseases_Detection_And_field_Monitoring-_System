# from werkzeug import generate_password_hash
# hashed_password=generate_password_hash("yourpassword",method="sha256")

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Irfan'
app.config['MYSQL_DB'] = 'user'

mysql = MySQL(app)

# Route for login page
@app.route('/')
def home_page():
    return render_template('home.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         cursor = mysql.connection.cursor()
#         cursor.execute("SELECT * FROM login  WHERE username = %s", (username,))
#         user = cursor.fetchone()
#         cursor.close()
 
#         if user and check_password_hash(user[2], password):

#             flash("Login Successful!")  # For now, just display success message
#             return redirect(url_for('home'))
#         else:
#             error = 'Invalid username or password'

#     return render_template('login.html', error=error)

# Route for registration page (optional)
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         hashed_password = generate_password_hash(password, method='sha256')

#         cursor = mysql.connection.cursor()
#         cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
#         mysql.connection.commit()
#         cursor.close()
#         flash('Registration Successful!')
#         return redirect(url_for('login'))

#     return render_template('register.html')
@app.route('/registration', methods=['GET', 'POST'])
def register():
    error = None
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')

        cursor = mysql.connection.cursor()
        # Check if the username already exists
        cursor.execute("SELECT * FROM login WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = 'Username already taken. Choose a different one.'
        else:
            # Insert the new user into the database
            cursor.execute("INSERT INTO login (username, password) VALUES (%s, %s)", (username, hashed_password))
            mysql.connection.commit()
            cursor.close()
            message = 'Registration successful! You can now log in.'
            return redirect(url_for('login'))
        cursor.close()
    return render_template('registration.html', error=error, message=message)

if __name__ == '__main__':
    app.run(debug=True)