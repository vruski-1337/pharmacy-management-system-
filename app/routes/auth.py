from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Company, User
import os
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_registration_number():
    """Generate unique registration number"""
    from datetime import datetime
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    import random
    random_suffix = random.randint(100, 999)
    return f"REG{timestamp}{random_suffix}"


@auth_bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in, else to login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Company registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['company_name', 'owner_name', 'email', 'phone', 'address', 
                          'city', 'state', 'country', 'postal_code', 'username', 'password', 'confirm_password']
        
        for field in required_fields:
            if not request.form.get(field):
                flash(f'{field.replace("_", " ").title()} is required.', 'danger')
                return redirect(url_for('auth.register'))
        
        # Check if username already exists
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if email already exists
        if Company.query.filter_by(email=request.form.get('email')).first():
            flash('Email already registered. Please use a different email or login.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if passwords match
        if request.form.get('password') != request.form.get('confirm_password'):
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Validate password strength
        password = request.form.get('password')
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            # Handle logo upload
            logo_path = None
            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to make filename unique
                    filename = f"{datetime.utcnow().timestamp()}_{filename}"
                    upload_folder = '/workspaces/pharmacy-management-system-/app/static/uploads'
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, filename))
                    logo_path = f"uploads/{filename}"
            
            # Create company
            company = Company(
                company_name=request.form.get('company_name'),
                owner_name=request.form.get('owner_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                country=request.form.get('country'),
                postal_code=request.form.get('postal_code'),
                gst_number=request.form.get('gst_number'),
                drug_license_number=request.form.get('drug_license_number'),
                logo_path=logo_path
            )
            db.session.add(company)
            db.session.flush()  # Get the company ID
            
            # Create user (owner)
            user = User(
                company_id=company.id,
                username=request.form.get('username'),
                is_active=True,
                role='owner'
            )
            user.set_password(request.form.get('password'))
            db.session.add(user)
            
            db.session.commit()
            
            # Auto-login the user
            login_user(user, remember=True)
            flash('Registration successful! Welcome to Pharmacy Management System.', 'success')
            return redirect(url_for('dashboard.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """View company profile"""
    company = current_user.company
    return render_template('profile.html', company=company)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit company profile"""
    company = current_user.company
    
    if request.method == 'POST':
        try:
            company.company_name = request.form.get('company_name', company.company_name)
            company.owner_name = request.form.get('owner_name', company.owner_name)
            company.phone = request.form.get('phone', company.phone)
            company.address = request.form.get('address', company.address)
            company.city = request.form.get('city', company.city)
            company.state = request.form.get('state', company.state)
            company.country = request.form.get('country', company.country)
            company.postal_code = request.form.get('postal_code', company.postal_code)
            company.gst_number = request.form.get('gst_number', company.gst_number)
            company.drug_license_number = request.form.get('drug_license_number', company.drug_license_number)
            
            # Handle logo upload
            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old logo if exists
                    if company.logo_path:
                        old_file = os.path.join('/workspaces/pharmacy-management-system-/app/static', company.logo_path)
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    
                    filename = secure_filename(file.filename)
                    filename = f"{datetime.utcnow().timestamp()}_{filename}"
                    upload_folder = '/workspaces/pharmacy-management-system-/app/static/uploads'
                    file.save(os.path.join(upload_folder, filename))
                    company.logo_path = f"uploads/{filename}"
            
            company.updated_date = datetime.utcnow()
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update profile: {str(e)}', 'danger')
            return redirect(url_for('auth.edit_profile'))
    
    return render_template('edit_profile.html', company=company)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(old_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('auth.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to change password: {str(e)}', 'danger')
            return redirect(url_for('auth.change_password'))
    
    return render_template('change_password.html')


@auth_bp.route('/access-denied')
def access_denied():
    return render_template('access_denied.html'), 403
