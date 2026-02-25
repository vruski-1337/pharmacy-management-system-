from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from app.models import db, Sale, Purchase, Product, Customer, Supplier, StockMovement, Expense, SalesReturn, PurchaseReturn
from datetime import datetime, timedelta
from sqlalchemy import and_, func
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def reports_home():
    """Reports home"""
    return render_template('reports/index.html')


@reports_bp.route('/sales')
@login_required
def sales_report():
    """Sales report"""
    company_id = current_user.company_id
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    customer_id = request.args.get('customer_id', type=int)
    export_format = request.args.get('export', '')
    
    query = Sale.query.filter(
        and_(Sale.company_id == company_id, Sale.is_cancelled == False)
    )
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(and_(Sale.invoice_date >= start, Sale.invoice_date <= end))
    
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    
    sales = query.order_by(Sale.invoice_date.desc()).all()
    
    # Export to CSV
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Invoice Number', 'Date', 'Customer', 'Subtotal', 'Tax', 'Discount', 'Total', 'Payment Method'])
        
        for sale in sales:
            writer.writerow([
                sale.invoice_number,
                sale.invoice_date.strftime('%Y-%m-%d %H:%M'),
                sale.customer_name or 'Walk-in',
                sale.subtotal,
                sale.tax_amount,
                sale.discount_amount,
                sale.total_amount,
                sale.payment_method
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sales_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    customers = Customer.query.filter_by(company_id=company_id, is_active=True).all()
    
    return render_template('reports/sales_report.html',
                         sales=sales,
                         start_date=start_date,
                         end_date=end_date,
                         customers=customers,
                         customer_id=customer_id)


@reports_bp.route('/sales-returns')
@login_required
def sales_returns_report():
    """Sales returns report"""
    company_id = current_user.company_id
    
    returns = db.session.query(SalesReturn).join(Sale).filter(
        Sale.company_id == company_id
    ).order_by(SalesReturn.return_date.desc()).all()
    
    return render_template('reports/sales_returns_report.html', returns=returns)


@reports_bp.route('/purchase')
@login_required
def purchase_report():
    """Purchase report"""
    company_id = current_user.company_id
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    supplier_id = request.args.get('supplier_id', type=int)
    export_format = request.args.get('export', '')
    
    query = Purchase.query.filter_by(company_id=company_id)
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(and_(Purchase.purchase_date >= start, Purchase.purchase_date <= end))
    
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    purchases = query.order_by(Purchase.purchase_date.desc()).all()
    
    # Export to CSV
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['PO Number', 'Date', 'Supplier', 'Subtotal', 'Tax', 'Discount', 'Total', 'Status'])
        
        for purchase in purchases:
            writer.writerow([
                purchase.purchase_number,
                purchase.purchase_date.strftime('%Y-%m-%d'),
                purchase.supplier.supplier_name,
                purchase.subtotal,
                purchase.tax_amount,
                purchase.discount_amount,
                purchase.total_amount,
                purchase.payment_status
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'purchase_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    suppliers = Supplier.query.filter_by(company_id=company_id, is_active=True).all()
    
    return render_template('reports/purchase_report.html',
                         purchases=purchases,
                         start_date=start_date,
                         end_date=end_date,
                         suppliers=suppliers,
                         supplier_id=supplier_id)


@reports_bp.route('/purchase-returns')
@login_required
def purchase_returns_report():
    """Purchase returns report"""
    company_id = current_user.company_id
    
    returns = db.session.query(PurchaseReturn).join(Purchase).filter(
        Purchase.company_id == company_id
    ).order_by(PurchaseReturn.return_date.desc()).all()
    
    return render_template('reports/purchase_returns_report.html', returns=returns)


@reports_bp.route('/purchases')
@login_required
def purchases_report():
    """Purchase report"""
    company_id = current_user.company_id
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    supplier_id = request.args.get('supplier_id', type=int)
    export_format = request.args.get('export', '')
    
    query = Purchase.query.filter_by(company_id=company_id)
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(and_(Purchase.purchase_date >= start, Purchase.purchase_date <= end))
    
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    purchases = query.order_by(Purchase.purchase_date.desc()).all()
    
    # Export to CSV
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['PO Number', 'Date', 'Supplier', 'Subtotal', 'Tax', 'Discount', 'Total', 'Status'])
        
        for purchase in purchases:
            writer.writerow([
                purchase.purchase_number,
                purchase.purchase_date.strftime('%Y-%m-%d'),
                purchase.supplier.supplier_name,
                purchase.subtotal,
                purchase.tax_amount,
                purchase.discount_amount,
                purchase.total_amount,
                purchase.payment_status
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'purchase_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    suppliers = Supplier.query.filter_by(company_id=company_id, is_active=True).all()
    
    return render_template('reports/purchases.html',
                         purchases=purchases,
                         start_date=start_date,
                         end_date=end_date,
                         suppliers=suppliers,
                         supplier_id=supplier_id)


@reports_bp.route('/inventory')
@login_required
def inventory_report():
    """Inventory report"""
    company_id = current_user.company_id
    category = request.args.get('category', '')
    only_low_stock = request.args.get('low_stock', False, type=bool)
    export_format = request.args.get('export', '')
    
    query = Product.query.filter(
        and_(Product.company_id == company_id, Product.is_active == True)
    )
    
    if category:
        query = query.filter_by(category=category)
    
    if only_low_stock:
        query = query.filter(Product.quantity <= Product.minimum_stock_level)
    
    products = query.order_by(Product.product_name).all()
    
    # Export to CSV
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Product', 'SKU', 'Batch', 'Quantity', 'Min Stock', 'Purchase Price', 'Selling Price', 'Category'])
        
        for product in products:
            writer.writerow([
                product.product_name,
                product.sku,
                product.batch_number,
                product.quantity,
                product.minimum_stock_level,
                product.purchase_price,
                product.selling_price,
                product.category
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'inventory_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    categories = db.session.query(Product.category).filter_by(
        company_id=company_id, is_active=True).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('reports/inventory.html',
                         products=products,
                         category=category,
                         only_low_stock=only_low_stock,
                         categories=categories)


@reports_bp.route('/expiry')
@login_required
def expiry_report():
    """Expiry report"""
    company_id = current_user.company_id
    days_filter = request.args.get('days', '30', type=int)
    export_format = request.args.get('export', '')
    
    today = datetime.utcnow().date()
    expiry_date_limit = today + timedelta(days=days_filter)
    
    products = Product.query.filter(
        and_(
            Product.company_id == company_id,
            Product.expiry_date.isnot(None),
            Product.expiry_date <= expiry_date_limit,
            Product.is_active == True
        )
    ).order_by(Product.expiry_date).all()
    
    # Export to CSV
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Product', 'Batch', 'Quantity', 'Expiry Date', 'Days Left'])
        
        for product in products:
            days_left = (product.expiry_date.date() - today).days
            writer.writerow([
                product.product_name,
                product.batch_number,
                product.quantity,
                product.expiry_date.strftime('%Y-%m-%d'),
                days_left
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'expiry_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    return render_template('reports/expiry.html',
                         products=products,
                         days_filter=days_filter)


@reports_bp.route('/profit-loss')
@login_required
def profit_loss_report():
    """Profit and Loss report"""
    company_id = current_user.company_id
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    if not start_date or not end_date:
        # Default to current month
        today = datetime.utcnow().date()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate sales
    total_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        and_(
            Sale.company_id == company_id,
            Sale.invoice_date >= start,
            Sale.invoice_date <= end,
            Sale.is_cancelled == False
        )
    ).scalar() or 0
    
    # Calculate purchase costs
    total_purchase_cost = db.session.query(func.sum(Purchase.total_amount)).filter(
        and_(
            Purchase.company_id == company_id,
            Purchase.purchase_date >= start,
            Purchase.purchase_date <= end
        )
    ).scalar() or 0
    
    # Calculate expenses
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        and_(
            Expense.company_id == company_id,
            Expense.expense_date >= start,
            Expense.expense_date <= end
        )
    ).scalar() or 0
    
    # Calculate gross profit
    gross_profit = total_sales - total_purchase_cost
    
    # Calculate net profit
    net_profit = gross_profit - total_expenses
    
    return render_template('reports/profit_loss.html',
                         start_date=start_date,
                         end_date=end_date,
                         total_sales=total_sales,
                         total_purchase_cost=total_purchase_cost,
                         total_expenses=total_expenses,
                         gross_profit=gross_profit,
                         net_profit=net_profit)


@reports_bp.route('/tax-summary')
@login_required
def tax_summary():
    """Tax summary report"""
    company_id = current_user.company_id
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Sale.query.filter(
        and_(Sale.company_id == company_id, Sale.is_cancelled == False)
    )

    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(and_(Sale.invoice_date >= start, Sale.invoice_date <= end))

    sales = query.order_by(Sale.invoice_date.desc()).all()

    # Calculate tax breakdown by tax percentage
    tax_breakdown = {}
    for sale in sales:
        for item in sale.items:
            rate = item.tax_percentage or 0
            if rate not in tax_breakdown:
                tax_breakdown[rate] = {'items': 0, 'tax_amount': 0}
            tax_breakdown[rate]['items'] += item.quantity
            tax_breakdown[rate]['tax_amount'] += item.tax_amount or 0

    return render_template('reports/tax_summary.html',
                         tax_breakdown=tax_breakdown,
                         start_date=start_date,
                         end_date=end_date)


@reports_bp.route('/outstanding')
@login_required
def outstanding_payments():
    """Outstanding payments report"""
    company_id = current_user.company_id
    
    # Customer outstanding payments
    customers = db.session.query(Customer).filter(
        and_(
            Customer.company_id == company_id,
            Customer.current_balance > 0
        )
    ).all()
    
    # Supplier outstanding payments
    suppliers = db.session.query(Supplier, db.func.sum(Purchase.total_amount)).filter(
        and_(
            Supplier.company_id == company_id,
            Purchase.payment_status != 'paid'
        )
    ).outerjoin(Purchase).group_by(Supplier.id).all()
    
    return render_template('reports/outstanding_payments.html',
                         customers=customers,
                         suppliers=suppliers)
