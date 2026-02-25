from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Company, User, db
from app.utils import require_roles

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/companies')
@require_roles('owner')
def companies_list():
    companies = Company.query.order_by(Company.created_date.desc()).all()
    return render_template('admin/companies_list.html', companies=companies)


@admin_bp.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
@require_roles('owner')
def edit_company_login(company_id):
    company = Company.query.get_or_404(company_id)
    user = User.query.filter_by(company_id=company.id).first()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username:
            flash('Username is required.', 'danger')
            return redirect(url_for('admin.edit_company_login', company_id=company.id))

        # Check username uniqueness (allow current user's username)
        existing = User.query.filter(User.username == username).first()
        if existing and (not user or existing.id != user.id):
            flash('Username already taken.', 'danger')
            return redirect(url_for('admin.edit_company_login', company_id=company.id))

        if not user:
            user = User(company_id=company.id, username=username)
            if password:
                user.set_password(password)
            db.session.add(user)
        else:
            user.username = username
            if password:
                user.set_password(password)

        db.session.commit()
        flash('Login credentials updated successfully.', 'success')
        return redirect(url_for('admin.companies_list'))

    return render_template('admin/edit_company.html', company=company, user=user)
