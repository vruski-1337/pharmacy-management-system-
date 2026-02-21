from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app.models import db, Sale, SaleItem, Product, Customer, SalesReturn, StockMovement
from datetime import datetime
from sqlalchemy import and_, func
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')


def generate_invoice_number():
    """Generate unique invoice number"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    import random
    random_suffix = random.randint(1000, 9999)
    return f"INV{timestamp}{random_suffix}"


@sales_bp.route('/pos')
@login_required
def pos():
    """POS interface"""
    customers = Customer.query.filter_by(company_id=current_user.company_id, is_active=True).all()
    return render_template('sales/pos.html', customers=customers)


@sales_bp.route('/api/products/search')
@login_required
def search_products():
    """Search products by name or barcode"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    company_id = current_user.company_id
    products = Product.query.filter(
        and_(
            Product.company_id == company_id,
            Product.is_active == True,
            db.or_(
                Product.product_name.ilike(f'%{query}%'),
                Product.barcode.ilike(f'%{query}%'),
                Product.sku.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.product_name,
        'barcode': p.barcode,
        'sku': p.sku,
        'price': p.selling_price,
        'mrp': p.mrp,
        'quantity': p.quantity,
        'tax_percentage': p.tax_percentage,
        'batch_number': p.batch_number
    } for p in products])


@sales_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Process checkout and create invoice"""
    try:
        data = request.json
        items = data.get('items', [])
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', '')
        customer_phone = data.get('customer_phone', '')
        payment_method = data.get('payment_method', 'cash')
        discount = float(data.get('discount', 0))
        include_tax = data.get('include_tax', True)
        notes = data.get('notes', '')
        
        if not items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        company_id = current_user.company_id
        
        # Validate and prepare items
        sale_items = []
        subtotal = 0
        total_tax = 0
        
        for item in items:
            # Accept product identifier from front-end as either 'product_id' or 'id'
            pid = item.get('product_id') or item.get('id')
            try:
                pid = int(pid)
            except Exception:
                pid = None

            product = Product.query.get(pid) if pid else None
            if not product or product.company_id != company_id:
                return jsonify({'success': False, 'message': 'Invalid product'}), 400
            
            quantity = int(item.get('quantity', 1))
            if product.quantity < quantity:
                return jsonify({'success': False, 'message': f'Insufficient stock for {product.product_name}'}), 400
            
            unit_price = float(item.get('price', product.selling_price))
            item_discount = float(item.get('discount', 0))
            
            tax_amount = 0
            if include_tax:
                tax_amount = (unit_price * quantity - item_discount) * (product.tax_percentage / 100)
            
            item_total = (unit_price * quantity) - item_discount + tax_amount
            
            sale_items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'tax_percentage': product.tax_percentage,
                'tax_amount': tax_amount,
                'item_discount': item_discount,
                'item_total': item_total,
                'batch_number': product.batch_number
            })
            
            subtotal += (unit_price * quantity) - item_discount
            total_tax += tax_amount
        
        # Calculate total
        total_amount = subtotal + total_tax - discount
        if total_amount < 0:
            total_amount = 0
        
        # Create sale
        sale = Sale(
            company_id=company_id,
            customer_id=customer_id,
            invoice_number=generate_invoice_number(),
            invoice_date=datetime.utcnow(),
            customer_name=customer_name,
            customer_phone=customer_phone,
            subtotal=subtotal,
            tax_amount=total_tax,
            discount_amount=discount,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status='paid' if payment_method != 'credit' else 'pending',
            notes=notes
        )
        
        db.session.add(sale)
        db.session.flush()
        
        # Add items and deduct stock
        for item in sale_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item['product'].id,
                batch_number=item['batch_number'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                tax_percentage=item['tax_percentage'],
                tax_amount=item['tax_amount'],
                discount_amount=item['item_discount'],
                total_amount=item['item_total']
            )
            db.session.add(sale_item)
            
            # Deduct stock
            product = item['product']
            product.quantity -= item['quantity']
            product.updated_date = datetime.utcnow()
            
            # Record stock movement
            movement = StockMovement(
                product_id=product.id,
                movement_type='sale',
                quantity=-item['quantity'],
                batch_number=item['batch_number'],
                reference_id=sale.id
            )
            db.session.add(movement)
        
        # Update customer balance if credit sale
        if customer_id and payment_method == 'credit':
            customer = Customer.query.get(customer_id)
            if customer:
                customer.current_balance += total_amount
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sale completed successfully',
            'invoice_number': sale.invoice_number,
            'sale_id': sale.id,
            'total_amount': total_amount
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@sales_bp.route('/invoices')
@login_required
def invoices_list():
    """List all invoices"""
    company_id = current_user.company_id
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Sale.query.filter_by(company_id=company_id)
    
    if search:
        query = query.filter(
            db.or_(
                Sale.invoice_number.ilike(f'%{search}%'),
                Sale.customer_name.ilike(f'%{search}%'),
                Sale.customer_phone.ilike(f'%{search}%')
            )
        )
    
    sales = query.order_by(Sale.invoice_date.desc()).paginate(page=page, per_page=20)
    
    return render_template('sales/invoices_list.html', sales=sales, search=search)


@sales_bp.route('/invoices/<int:sale_id>')
@login_required
def invoice_detail(sale_id):
    """View invoice"""
    sale = Sale.query.get(sale_id)
    if not sale or sale.company_id != current_user.company_id:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('sales.invoices_list'))
    
    return render_template('sales/invoice_detail.html', sale=sale)


@sales_bp.route('/invoices/<int:sale_id>/print')
@login_required
def print_invoice(sale_id):
    """Print invoice"""
    sale = Sale.query.get(sale_id)
    if not sale or sale.company_id != current_user.company_id:
        return jsonify({'success': False, 'message': 'Invoice not found'}), 404
    
    return render_template('sales/print_invoice.html', sale=sale)


@sales_bp.route('/invoices/<int:sale_id>/pdf')
@login_required
def download_invoice_pdf(sale_id):
    """Download invoice as PDF"""
    sale = Sale.query.get(sale_id)
    if not sale or sale.company_id != current_user.company_id:
        return jsonify({'success': False, 'message': 'Invoice not found'}), 404
    
    try:
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=(4.25*inch, 8.5*inch), 
                              topMargin=0.5*inch, bottomMargin=0.5*inch,
                              leftMargin=0.3*inch, rightMargin=0.3*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Company and invoice details
        company = sale.company
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=10, alignment=1)
        elements.append(Paragraph(company.company_name, title_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Invoice details
        invoice_info = f"Invoice: {sale.invoice_number}<br/>Date: {sale.invoice_date.strftime('%Y-%m-%d %H:%M')}"
        elements.append(Paragraph(invoice_info, styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Customer details
        customer_info = f"Customer: {sale.customer_name or 'Walk-in'}<br/>Phone: {sale.customer_phone or 'N/A'}"
        elements.append(Paragraph(customer_info, styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Items table
        table_data = [['Item', 'Qty', 'Price', 'Tax', 'Total']]
        for item in sale.items:
            table_data.append([
                item.product.product_name[:20],
                str(item.quantity),
                f"₹{item.unit_price:.2f}",
                f"₹{item.tax_amount:.2f}",
                f"₹{item.total_amount:.2f}"
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 0.5*inch, 0.8*inch, 0.6*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Summary
        summary = f"""
        <b>Subtotal:</b> ₹{sale.subtotal:.2f}<br/>
        <b>Tax:</b> ₹{sale.tax_amount:.2f}<br/>
        <b>Discount:</b> ₹{sale.discount_amount:.2f}<br/>
        <b>Total:</b> ₹{sale.total_amount:.2f}<br/>
        <b>Payment:</b> {sale.payment_method.upper()}
        """
        elements.append(Paragraph(summary, styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', 
                        as_attachment=True, 
                        download_name=f"invoice_{sale.invoice_number}.pdf")
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@sales_bp.route('/invoices/<int:sale_id>/cancel', methods=['POST'])
@login_required
def cancel_invoice(sale_id):
    """Cancel invoice"""
    sale = Sale.query.get(sale_id)
    if not sale or sale.company_id != current_user.company_id:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('sales.invoices_list'))
    
    if sale.is_cancelled:
        flash('Invoice is already cancelled.', 'info')
        return redirect(url_for('sales.invoice_detail', sale_id=sale_id))
    
    try:
        reason = request.form.get('cancellation_reason', '')
        
        # Reverse stock movements
        for item in sale.items:
            item.product.quantity += item.quantity
            item.product.updated_date = datetime.utcnow()
            
            # Record reversal movement
            movement = StockMovement(
                product_id=item.product_id,
                movement_type='sale',
                quantity=item.quantity,
                batch_number=item.batch_number,
                reason=f'Cancelled invoice {sale.invoice_number}'
            )
            db.session.add(movement)
        
        # Update customer balance if credit sale
        if sale.customer_id and sale.payment_method == 'credit':
            customer = sale.customer
            if customer:
                customer.current_balance -= sale.total_amount
        
        sale.is_cancelled = True
        sale.cancellation_reason = reason
        sale.updated_date = datetime.utcnow()
        
        db.session.commit()
        flash('Invoice cancelled successfully.', 'success')
        return redirect(url_for('sales.invoice_detail', sale_id=sale_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to cancel invoice: {str(e)}', 'danger')
        return redirect(url_for('sales.invoice_detail', sale_id=sale_id))


@sales_bp.route('/returns')
@login_required
def sales_returns_list():
    """List all sales returns"""
    company_id = current_user.company_id
    returns = db.session.query(SalesReturn).join(Sale).filter(
        Sale.company_id == company_id
    ).order_by(SalesReturn.return_date.desc()).all()
    
    return render_template('sales/returns_list.html', returns=returns)


@sales_bp.route('/invoices/<int:sale_id>/return', methods=['GET', 'POST'])
@login_required
def process_return(sale_id):
    """Process sales return"""
    sale = Sale.query.get(sale_id)
    if not sale or sale.company_id != current_user.company_id:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('sales.invoices_list'))
    
    if request.method == 'POST':
        try:
            is_full_return = request.form.get('return_type') == 'full'
            reason = request.form.get('return_reason', '')
            refund_mode = request.form.get('refund_mode', 'cash')
            
            if is_full_return:
                # Full return
                return_credit = sale.total_amount
                for item in sale.items:
                    item.product.quantity += item.quantity
                    item.product.updated_date = datetime.utcnow()
            else:
                # Partial return
                product_id = request.form.get('product_id', type=int)
                quantity = request.form.get('quantity', type=int)
                
                # Find the sale item
                sale_item = SaleItem.query.filter_by(sale_id=sale_id, product_id=product_id).first()
                if not sale_item or sale_item.quantity < quantity:
                    flash('Invalid return quantity.', 'danger')
                    return redirect(url_for('sales.process_return', sale_id=sale_id))
                
                # Return stock
                product = sale_item.product
                product.quantity += quantity
                product.updated_date = datetime.utcnow()
                
                # Calculate refund amount
                return_credit = (sale_item.unit_price * quantity) + (sale_item.tax_amount * quantity / sale_item.quantity)
            
            # Create return record
            credit_note = SalesReturn(
                sale_id=sale_id,
                credit_note_number=generate_invoice_number().replace('INV', 'CN'),
                return_date=datetime.utcnow(),
                quantity=sum(item.quantity for item in sale.items) if is_full_return else quantity,
                is_full_return=is_full_return,
                reason=reason,
                refund_amount=return_credit,
                refund_mode=refund_mode
            )
            
            db.session.add(credit_note)
            
            # Update customer balance if applicable
            if sale.customer_id and sale.payment_method == 'credit':
                sale.customer.current_balance -= return_credit
            
            db.session.commit()
            flash('Return processed successfully.', 'success')
            return redirect(url_for('sales.invoice_detail', sale_id=sale_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to process return: {str(e)}', 'danger')
            return redirect(url_for('sales.process_return', sale_id=sale_id))
    
    return render_template('sales/process_return.html', sale=sale)
