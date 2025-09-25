from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from database_models import db, User
from datetime import datetime

# Initialize Flask-Login
login_manager = LoginManager()

def init_auth(app):
    """Initialize authentication system"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    retype_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

# Authentication routes
def register_auth_routes(app):
    """Register authentication routes"""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            # Check if username or email
            user = User.query.filter(
                (User.username == form.username.data) | 
                (User.email == form.username.data)
            ).first()
            
            if user and check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                flash(f'Welcome back, {user.first_name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid username/email or password', 'error')
        
        return render_template('auth/login.html', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            # Check if username or email already exists
            existing_user = User.query.filter(
                (User.username == form.username.data) | 
                (User.email == form.email.data)
            ).first()
            
            if existing_user:
                if existing_user.username == form.username.data:
                    flash('Username already exists', 'error')
                else:
                    flash('Email already registered', 'error')
            else:
                # Create new user
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    password=generate_password_hash(form.password.data)
                )
                db.session.add(user)
                db.session.commit()
                
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
        
        return render_template('auth/register.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
