# Import Librariesa
import os

import random
from flask import Flask, redirect, render_template, request, session, flash, url_for, jsonify
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from PIL import Image
import torchvision.transforms.functional as TF
import CNN
import numpy as np
import torch
import pandas as pd

# Create Flask App object 
app=Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Database configuration with absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate=Migrate(app,db)
# User model for storing credentials
# class User(db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(150), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password = db.Column(db.String(150), nullable=False)

#     def set_password(self, password):
#         self.password = generate_password_hash(password)

#     def check_password(self, password):
#         return check_password_hash(self.password, password)

# with app.app_context():
#     db.create_all()


# Admin Model

# class Admin(db.Model):
#     __tablename__ = 'admin'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(150), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password = db.Column(db.String(150), nullable=False)

#     def set_password(self, password):
#         self.password = generate_password_hash(password)

#     def check_password(self, password):
#         return check_password_hash(self.password, password)

# with app.app_context():
#     db.create_all()


# Create Admin Table
class Admin(db.Model):
    __tablename__ = 'Admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

with app.app_context():
    db.create_all()

# Load disease information
try:
    disease_info = pd.read_csv('disease_info.csv', encoding='cp1252')
    supplement_info = pd.read_csv('supplement_info.csv', encoding='cp1252')
except Exception as e:
    print(f"Error loading CSV files: {e}")

# Load model
try:
    model = CNN.CNN(39)
    model.load_state_dict(torch.load("plant_disease_model_1_latest.pt"))
    model.eval()
except Exception as e:
    print(f"Error loading model: {e}")
    model = None


# Prediction function
def prediction(image_path):
    try:
        image = Image.open(image_path)
        image = image.resize((224, 224))
        input_data = TF.to_tensor(image)
        input_data = input_data.view((-1, 3, 224, 224))
        output = model(input_data)
        output = output.detach().numpy()
        index = np.argmax(output)
        return index
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/index')
def engine():
    return render_template('index.html')
# @app.route('/forgot')
# def forgot():
#     return render_template('forgot.html')

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'irfanmurtaza7051@gmail.com'
app.config['MAIL_PASSWORD'] = 'zcvf gcmb bcew yqnu' #App security password
app.config['MAIL_DEFAULT_SENDER'] = 'irfanmurtaza7051@gmai.com'


mail = Mail(app)

# Token Serializer
s = URLSafeTimedSerializer(app.secret_key)

# Add a reset token generation and verification method

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):  # Token expires in 1 hour
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None
    return email

# Create a password reset request route

@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        admin = Admin.query.filter_by(email=email).first()
        if admin:
            reset_token = generate_reset_token(email)
            reset_url = url_for('reset_password', token=reset_token, _external=True)
            
            msg = Message("Password Reset Request", sender="your_email@gmail.com", recipients=[email])
            msg.body = f"Please click the link to reset your password: {reset_url}"
            mail.send(msg)
            # Send an email with the reset URL (use Flask-Mail or any email library)
            # Example: send_email(admin.email, 'Password Reset Request', f'Reset your password: {reset_url}')
            
            flash('Check your email for a password reset link.', 'info')
        else:
            flash('No account with that email address.', 'danger')
    return render_template('forgot.html')

# Create a password reset route

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('forgot'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email).first()
        if admin:
            admin.set_password(password)
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('login_page'))
    return render_template('reset_password.html')


# Admin Register

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email=request.form.get('email')
        password = request.form.get('password')

        # Check if username and password fields are filled
        if not username or not email or not password:
            flash('Please fill in all required fields.','danger')
            return redirect(url_for('register'))

        existing_user = Admin.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.','danger')
            return redirect(url_for('register'))

        # Create new user and set password
        new_user = Admin(username=username,email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.','success')
        return redirect(url_for('login_page'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Admin.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!','success')
            session['authenticated'] = True
            return redirect(url_for('dashboard'))
            # return redirect(url_for('desh_base'))
            
        else:
            flash('Invalid username or password. Please try again.','danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('login_page'))


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')


        admin_email = 'irfanmurtaza7051@gmail.com'  # Admin email
        subject = f"New Contact Form Submission from {name}"
        email_body = f"""
        A new message has been submitted through the contact form:
        
        Name: {name}
        Email: {email}
        Message:
        {message}
        """


        # Send email
        try:
            msg = Message(subject, recipients=[admin_email])
           

            msg.body = email_body
            msg.reply_to = email # Set the user's email as the reply-to address

            # Send the email
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')

        # Redirect to the same page after submission
        return redirect(url_for('contact'))

    return render_template('contact-us.html')


# //////

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        image = request.files['image']
        filename = secure_filename(image.filename)
        file_path = os.path.join('static/uploads', filename)
        image.save(file_path)
        
        pred = prediction(file_path)
        if pred is not None:
            title = disease_info['disease_name'][pred]
            description = disease_info['description'][pred]
            prevent = disease_info['Possible Steps'][pred]
            image_url = disease_info['image_url'][pred]
            supplement_name = supplement_info['supplement name'][pred]
            supplement_image_url = supplement_info['supplement image'][pred]
            supplement_buy_link = supplement_info['buy link'][pred]
            return render_template('submit.html', title=title, desc=description, prevent=prevent,
                                   image_url=image_url, pred=pred, sname=supplement_name,
                                   simage=supplement_image_url, buy_link=supplement_buy_link)
        else:
            flash('Prediction failed. Please try again.')
            return redirect(url_for('home_page'))

@app.route('/market')
def market():
    return render_template('market.html', supplement_image=list(supplement_info['supplement image']),
                           supplement_name=list(supplement_info['supplement name']),
                           disease=list(disease_info['disease_name']),
                           buy=list(supplement_info['buy link']))


@app.route('/dashboard')
def dashboard():
    if 'authenticated' not in session or not session['authenticated']:
        flash("You need to log in first!", "warning")
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    return render_template('dashboard.html')  # Render the dashboard



@app.route('/index')
def view_index():
    if 'authenticated' not in session or not session['authenticated']:
        flash("Please log in to access this file.", "warning")
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    
    # Assuming index.html is in the templates folder
    return render_template('index.html')  # Serve the index.html file
if __name__ == '__main__':
    app.run(debug=True)



