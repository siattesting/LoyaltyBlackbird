from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select
from auth import auth_bp
from app import db
from models import User, UserType
from .forms import LoginForm, RegistrationForm
from utils import is_safe_url

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            select(User).where(User.email == form.email.data)
        )
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Successfully logged in!', 'success')
            next_page = request.args.get('next')
            if not is_safe_url(next_page):
                return redirect(url_for('dashboard.index'))
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = db.session.scalar(
            select(User).where(
                (User.email == form.email.data) | (User.username == form.username.data)
            )
        )
        
        if existing_user:
            flash('User with this email or username already exists', 'error')
            return render_template('auth/register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            password_hash=generate_password_hash(form.password.data),
            user_type=UserType(form.user_type.data),
            business_name=form.business_name.data if form.user_type.data == 'merchant' else None,
            address=form.address.data if form.user_type.data == 'merchant' else None,
            # latitude=form.latitude.data if form.user_type.data == 'merchant' else None,
            # longitude=form.longitude.data if form.user_type.data == 'merchant' else None
        )
        print(user)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('dashboard.index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))
