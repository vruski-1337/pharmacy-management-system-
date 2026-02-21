from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Product, StockMovement, Category, Unit
from datetime import datetime
import os

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@inventory_bp.route('/products')
@login_required
def products_list():
    """List all products"""
    company_id = current_user.company_id
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    category_id = request.args.get('category_id', type=int)
    
    query = Product.query.filter_by(company_id=company_id, is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Product.product_name.ilike(f'%{search}%'),
                Product.generic_name.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%')
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    elif category:
        query = query.filter_by(category=category)
    
    products = query.order_by(Product.product_name).paginate(page=page, per_page=20)
    
    # Get categories from master table if available, fallback to product.category
    cat_objs = Category.query.filter_by(company_id=company_id, is_active=True).order_by(Category.name).all()
    if cat_objs:
        categories = [c.name for c in cat_objs]
    else:
        categories = db.session.query(Product.category).filter_by(
            company_id=company_id, is_active=True
        ).distinct().all()
        categories = [c[0] for c in categories if c[0]]
    
    return render_template('inventory/products_list.html', 
                         products=products, 
                         search=search, 
                         category=category,
                         categories=categories)


@inventory_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product"""
    if request.method == 'POST':
        try:
            # Check unique SKU
            if Product.query.filter_by(sku=request.form.get('sku')).first():
                flash('SKU already exists.', 'danger')
                return redirect(url_for('inventory.add_product'))
            
            # Check unique barcode (if provided)
            barcode = request.form.get('barcode')
            if barcode and Product.query.filter_by(barcode=barcode).first():
                flash('Barcode already exists.', 'danger')
                return redirect(url_for('inventory.add_product'))
            
            # Handle image upload
            image_path = None
            if 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{datetime.utcnow().timestamp()}_{filename}"
                    upload_folder = '/workspaces/pharmacy-management-system-/app/static/uploads'
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, filename))
                    image_path = f"uploads/{filename}"
            
            mfg_date = None
            exp_date = None
            if request.form.get('manufacturing_date'):
                mfg_date = datetime.strptime(request.form.get('manufacturing_date'), '%Y-%m-%d')
            if request.form.get('expiry_date'):
                exp_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d')
            
            product = Product(
                company_id=current_user.company_id,
                product_name=request.form.get('product_name'),
                generic_name=request.form.get('generic_name'),
                brand=request.form.get('brand'),
                category=request.form.get('category'),
                manufacturer=request.form.get('manufacturer'),
                batch_number=request.form.get('batch_number'),
                barcode=barcode,
                sku=request.form.get('sku'),
                purchase_price=float(request.form.get('purchase_price', 0)),
                selling_price=float(request.form.get('selling_price', 0)),
                mrp=float(request.form.get('mrp', 0)),
                tax_percentage=float(request.form.get('tax_percentage', 0)),
                manufacturing_date=mfg_date,
                expiry_date=exp_date,
                quantity=int(request.form.get('quantity', 0)),
                minimum_stock_level=int(request.form.get('minimum_stock_level', 10)),
                reorder_level=int(request.form.get('reorder_level', 20)),
                prescription_required=request.form.get('prescription_required') == 'on',
                description=request.form.get('description'),
                image_path=image_path
            )
            # assign master ids if provided
            try:
                cid = request.form.get('category_id')
                if cid:
                    product.category_id = int(cid)
                    cat = Category.query.get(int(cid))
                    if cat:
                        product.category = cat.name
                uid = request.form.get('unit_id')
                if uid:
                    product.unit_id = int(uid)
            except Exception:
                pass
            
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully.', 'success')
            return redirect(url_for('inventory.product_detail', product_id=product.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add product: {str(e)}', 'danger')
            return redirect(url_for('inventory.add_product'))
    
    # provide categories and units for the form
    categories = Category.query.filter_by(company_id=current_user.company_id, is_active=True).order_by(Category.name).all()
    units = Unit.query.filter_by(company_id=current_user.company_id, is_active=True).order_by(Unit.name).all()
    return render_template('inventory/add_product.html', categories=categories, units=units)


@inventory_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    """Product detail view"""
    product = Product.query.get(product_id)
    if not product or product.company_id != current_user.company_id:
        flash('Product not found.', 'danger')
        return redirect(url_for('inventory.products_list'))
    
    # Get stock movements
    movements = StockMovement.query.filter_by(product_id=product_id).order_by(
        StockMovement.created_date.desc()
    ).limit(20).all()
    
    return render_template('inventory/product_detail.html', product=product, movements=movements)


@inventory_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product"""
    product = Product.query.get(product_id)
    if not product or product.company_id != current_user.company_id:
        flash('Product not found.', 'danger')
        return redirect(url_for('inventory.products_list'))
    
    if request.method == 'POST':
        try:
            # Check unique barcode if changed
            barcode = request.form.get('barcode')
            if barcode != product.barcode and Product.query.filter_by(barcode=barcode).first():
                flash('Barcode already exists.', 'danger')
                return redirect(url_for('inventory.edit_product', product_id=product_id))
            
            product.product_name = request.form.get('product_name', product.product_name)
            product.generic_name = request.form.get('generic_name', product.generic_name)
            product.brand = request.form.get('brand', product.brand)
            product.category = request.form.get('category', product.category)
            product.manufacturer = request.form.get('manufacturer', product.manufacturer)
            product.batch_number = request.form.get('batch_number', product.batch_number)
            product.barcode = barcode
            product.purchase_price = float(request.form.get('purchase_price', product.purchase_price))
            product.selling_price = float(request.form.get('selling_price', product.selling_price))
            product.mrp = float(request.form.get('mrp', product.mrp))
            product.tax_percentage = float(request.form.get('tax_percentage', product.tax_percentage))
            product.minimum_stock_level = int(request.form.get('minimum_stock_level', product.minimum_stock_level))
            product.reorder_level = int(request.form.get('reorder_level', product.reorder_level))
            product.prescription_required = request.form.get('prescription_required') == 'on'
            product.description = request.form.get('description', product.description)
            # update category/unit if provided
            try:
                cid = request.form.get('category_id')
                if cid:
                    product.category_id = int(cid)
                    cat = Category.query.get(int(cid))
                    if cat:
                        product.category = cat.name
                uid = request.form.get('unit_id')
                if uid:
                    product.unit_id = int(uid)
            except Exception:
                pass
            
            if request.form.get('manufacturing_date'):
                product.manufacturing_date = datetime.strptime(request.form.get('manufacturing_date'), '%Y-%m-%d')
            if request.form.get('expiry_date'):
                product.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d')
            
            # Handle image upload
            if 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old image
                    if product.image_path:
                        old_file = os.path.join('/workspaces/pharmacy-management-system-/app/static', product.image_path)
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    
                    filename = secure_filename(file.filename)
                    filename = f"{datetime.utcnow().timestamp()}_{filename}"
                    upload_folder = '/workspaces/pharmacy-management-system-/app/static/uploads'
                    file.save(os.path.join(upload_folder, filename))
                    product.image_path = f"uploads/{filename}"
            
            product.updated_date = datetime.utcnow()
            db.session.commit()
            
            flash('Product updated successfully.', 'success')
            return redirect(url_for('inventory.product_detail', product_id=product.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update product: {str(e)}', 'danger')
            return redirect(url_for('inventory.edit_product', product_id=product_id))
    
    categories = Category.query.filter_by(company_id=current_user.company_id, is_active=True).order_by(Category.name).all()
    units = Unit.query.filter_by(company_id=current_user.company_id, is_active=True).order_by(Unit.name).all()
    return render_template('inventory/edit_product.html', product=product, categories=categories, units=units)


@inventory_bp.route('/products/<int:product_id>/adjust-stock', methods=['POST'])
@login_required
def adjust_stock(product_id):
    """Adjust stock for a product"""
    product = Product.query.get(product_id)
    if not product or product.company_id != current_user.company_id:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    try:
        adjustment_type = request.json.get('adjustment_type')  # 'add' or 'remove'
        quantity = int(request.json.get('quantity', 0))
        reason = request.json.get('reason', '')
        batch_number = request.json.get('batch_number', product.batch_number)
        
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be greater than 0'}), 400
        
        if adjustment_type == 'add':
            product.quantity += quantity
        elif adjustment_type == 'remove':
            if product.quantity < quantity:
                return jsonify({'success': False, 'message': 'Insufficient stock'}), 400
            product.quantity -= quantity
        else:
            return jsonify({'success': False, 'message': 'Invalid adjustment type'}), 400
        
        # Record stock movement
        movement = StockMovement(
            product_id=product_id,
            movement_type='adjustment',
            quantity=quantity if adjustment_type == 'add' else -quantity,
            batch_number=batch_number,
            reason=reason
        )
        
        db.session.add(movement)
        product.updated_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock adjusted successfully',
            'new_quantity': product.quantity
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@inventory_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Soft delete product"""
    product = Product.query.get(product_id)
    if not product or product.company_id != current_user.company_id:
        flash('Product not found.', 'danger')
        return redirect(url_for('inventory.products_list'))
    
    try:
        product.is_active = False
        product.updated_date = datetime.utcnow()
        db.session.commit()
        flash('Product deleted successfully.', 'success')
        return redirect(url_for('inventory.products_list'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete product: {str(e)}', 'danger')
        return redirect(url_for('inventory.product_detail', product_id=product_id))


@inventory_bp.route('/low-stock')
@login_required
def low_stock_report():
    """Low stock report"""
    company_id = current_user.company_id
    products = Product.query.filter(
        db.and_(
            Product.company_id == company_id,
            Product.quantity <= Product.minimum_stock_level,
            Product.is_active == True
        )
    ).order_by(Product.quantity).all()
    
    return render_template('inventory/low_stock_report.html', products=products)


@inventory_bp.route('/expiry-report')
@login_required
def expiry_report():
    """Expiry report"""
    from datetime import timedelta
    from sqlalchemy import and_
    
    company_id = current_user.company_id
    today = datetime.utcnow().date()
    expiry_90_days = today + timedelta(days=90)
    
    products = Product.query.filter(
        and_(
            Product.company_id == company_id,
            Product.expiry_date.isnot(None),
            Product.expiry_date <= expiry_90_days,
            Product.is_active == True
        )
    ).order_by(Product.expiry_date).all()
    
    return render_template('inventory/expiry_report.html', products=products)


@inventory_bp.route('/stock-movement-report')
@login_required
def stock_movement_report():
    """Stock movement report"""
    company_id = current_user.company_id
    product_id = request.args.get('product_id', type=int)
    movement_type = request.args.get('type', '')
    
    query = db.session.query(StockMovement).join(Product).filter(
        Product.company_id == company_id
    )
    
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    
    movements = query.order_by(StockMovement.created_date.desc()).all()
    products = Product.query.filter_by(company_id=company_id, is_active=True).all()
    
    return render_template('inventory/stock_movement_report.html', 
                         movements=movements, 
                         products=products,
                         selected_product_id=product_id,
                         selected_type=movement_type)


@inventory_bp.route('/products/<int:product_id>/adjust-stock', methods=['POST'])
@login_required
def adjust_stock(product_id):
    """Adjust product stock"""
    product = Product.query.get(product_id)
    if not product or product.company_id != current_user.company_id:
        flash('Product not found.', 'danger')
        return redirect(url_for('inventory.products_list'))
    
    try:
        adjustment_type = request.form.get('adjustment_type')
        quantity = int(request.form.get('quantity'))
        reason = request.form.get('reason')
        
        if adjustment_type == 'add':
            product.quantity += quantity
            movement_qty = quantity
        else:
            if product.quantity < quantity:
                flash('Insufficient stock for removal.', 'danger')
                return redirect(url_for('inventory.product_detail', product_id=product_id))
            product.quantity -= quantity
            movement_qty = -quantity
        
        product.updated_date = datetime.utcnow()
        
        # Record movement
        movement = StockMovement(
            product_id=product_id,
            movement_type='adjustment',
            quantity=movement_qty,
            reason=reason
        )
        db.session.add(movement)
        db.session.commit()
        
        flash('Stock adjusted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to adjust stock: {str(e)}', 'danger')
    
    return redirect(url_for('inventory.product_detail', product_id=product_id))
