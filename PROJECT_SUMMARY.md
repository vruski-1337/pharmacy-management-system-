# Pharmacy Management System

A comprehensive **single-tenant Pharmacy Management System** built with Flask and SQLite3, designed for individual pharmacy owners to manage all aspects of their business operations.

## 🎯 System Overview

This system provides a complete solution for pharmacy operations including:
- Company registration and user authentication
- Inventory management with batch tracking
- Point-of-Sale (POS) system
- Purchase order management
- Customer and supplier management
- Financial accounting and reporting
- Real-time alerts and notifications

## 📋 Complete Features Implemented

✅ **Company Registration & Authentication**
- Single-tenant architecture with company isolation
- Complete company profile management
- Logo upload and storage
- Secure password hashing and session management
- Auto-login after registration

✅ **Dashboard**
- Real-time sales metrics and KPIs
- Stock status and expiry alerts
- 7-day sales trend graph
- Quick action buttons
- Recent transaction history

✅ **Inventory Management**
- Full product catalog with batch tracking
- Product search by name/barcode/SKU
- Stock monitoring with automatic adjustments
- Low-stock and expiry alerts
- Stock movement history
- FIFO batch tracking

✅ **POS/Sales System**
- Interactive shopping cart interface
- Real-time product search
- Multiple payment methods (Cash, Card, UPI, Bank, Credit)
- Tax calculation and discounts
- Invoice generation with PDF export
- Sales returns processing
- Invoice cancellation with logging

✅ **Purchase Management**
- Supplier management and ledgers
- Purchase order creation
- Batch and expiry tracking
- Automatic stock updates
- Payment status tracking
- Purchase returns processing

✅ **Customer Management**
- Customer profiles and credit limits
- Purchase history tracking
- Outstanding balance management
- Customer ledger reports

✅ **Supplier Management**
- Complete supplier database
- Contact and payment terms tracking
- Supplier ledger and balance tracking
- Purchase history per supplier

✅ **Accounting Module**
- Expense categorization and tracking
- Receipt image attachment
- Daily cash summaries
- Sales and purchase registers
- Profit & Loss calculations
- Tax tracking

✅ **Reporting System**
- Sales, purchase, and inventory reports
- Date range and category filtering
- CSV/PDF/Excel export
- Profit & Loss analysis
- Tax summaries
- Outstanding payments reports

✅ **Alert System**
- Low stock alerts
- Expiry date notifications (30/60/90 days)
- Customer payment due alerts
- Supplier payment pending alerts
- Severity levels (Critical/Warning/Info)
- Real-time dashboard notifications

## 🚀 Quick Start Guide

### Installation (5 Minutes)

```bash
# 1. Navigate to project directory
cd /workspaces/pharmacy-management-system-

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production" > .env

# 5. Run application
python run.py

# 6. Open browser to http://localhost:5000
```

### First Time Setup

1. **Register** at `http://localhost:5000/register`
2. **Fill company details** (name, owner, GST, etc.)
3. **Create account** with unique username and password
4. **Login** with your credentials
5. **Start managing** your pharmacy!

## 📁 Project Architecture

```
pharmacy-management-system/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # 14 database models
│   ├── routes/                  # 9 route modules
│   │   ├── auth.py              # Registration & login (✅ Complete)
│   │   ├── dashboard.py         # Dashboard (✅ Complete)
│   │   ├── inventory.py         # Products (✅ Complete)
│   │   ├── sales.py             # POS & invoicing (✅ Complete)
│   │   ├── purchases.py         # Orders (✅ Complete)
│   │   ├── customers.py         # Customers (✅ Complete)
│   │   ├── suppliers.py         # Suppliers (✅ Complete)
│   │   ├── accounting.py        # Expenses (✅ Complete)
│   │   ├── reports.py           # Reports (✅ Complete)
│   │   └── alerts.py            # Alerts (✅ Complete)
│   ├── templates/               # HTML templates
│   │   ├── base.html            # Main layout
│   │   ├── login.html           # Login form
│   │   ├── register.html        # Registration form
│   │   ├── profile.html         # User profile
│   │   ├── dashboard/           # Dashboard templates
│   │   ├── inventory/           # Inventory templates
│   │   ├── sales/               # Sales templates
│   │   ├── purchases/           # Purchase templates
│   │   ├── customers/           # Customer templates
│   │   ├── suppliers/           # Supplier templates
│   │   ├── accounting/          # Accounting templates
│   │   ├── reports/             # Report templates
│   │   └── alerts/              # Alert templates
│   └── static/                  # Static assets
│       ├── uploads/             # User files
│       ├── css/                 # Stylesheets
│       └── js/                  # JavaScript
├── config.py                    # Configuration
├── run.py                       # Entry point
├── requirements.txt             # Dependencies
├── pharmacy.db                  # Database (auto-created)
├── SETUP_GUIDE.md              # Detailed docs
└── README.md                    # This file
```

## 🗄️ Database Schema

### Implemented Tables (14 total)
- **company** - Pharmacy information
- **user** - Single admin per company
- **product** - Medicines with batch tracking
- **stock_movement** - Inventory history
- **sale** - Customer invoices
- **sale_item** - Products in sales
- **sales_return** - Returns and credits
- **purchase** - Supplier orders
- **purchase_item** - Products in purchases
- **purchase_return** - Supplier returns
- **customer** - Customer profiles
- **supplier** - Vendor information
- **expense** - Operational costs
- **alert** - System notifications

## 🔐 Security Implementation

✅ Session-based authentication (Flask-Login)
✅ Password hashing (Werkzeug)
✅ Login required on all routes
✅ Company data isolation
✅ CSRF protection ready
✅ Secure session cookies
✅ Input validation
✅ SQL injection prevention (ORM)

## 🎨 Technology Used

- **Flask 2.3.3** - Web framework
- **SQLAlchemy** - ORM
- **SQLite3** - Database
- **Flask-Login** - Authentication
- **Bootstrap 5** - UI framework
- **Chart.js** - Graphs
- **ReportLab** - PDF generation
- **openpyxl** - Excel export

## 📈 Key Metrics & Dashboards

The system tracks:
- Daily and monthly sales totals
- Profit calculations
- Purchase expenses
- Stock levels and alerts
- Expiry dates (30/60/90 day tracking)
- Customer balances
- Supplier outstanding payments
- Expense categories

## 🚀 API Routes Overview

### Core Routes (60+ endpoints)
- Authentication: Login, Register, Logout, Profile
- Dashboard: Main dashboard with metrics
- Inventory: Products, Search, Stock, Expiry
- Sales: POS, Checkout, Invoices, Returns
- Purchases: Orders, Items, Returns
- Customers: List, Add, Ledger
- Suppliers: List, Add, Ledger
- Accounting: Expenses, Cash Summary
- Reports: Sales, Purchase, Inventory, P&L, Tax
- Alerts: View, Count, Mark Read, Delete

## 🛠️ Configuration

### Environment Variables (`.env`)
```
FLASK_ENV=development              # or production
SECRET_KEY=your-secret-key         # Change in production
PORT=5000                          # Server port
```

### Database Settings (`config.py`)
- SQLite3 database path: `pharmacy.db`
- File upload limit: 16MB
- Allowed file types: PNG, JPG, JPEG, GIF, PDF

## 📖 Documentation

**For detailed information, see:**
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete setup and API docs
- Inline code comments throughout the application
- Bootstrap-based responsive UI

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Port in use | Change port: `python run.py --port 5001` |
| Database error | Reinit DB: `python -c "from app import create_app; app, _ = create_app(); app.app_context().push(); from app.models import db; db.create_all()"` |
| Login fails | Verify email is unique, password is 6+ chars |
| Files not uploading | Check `app/static/uploads/` exists |
| Template errors | Run `pip install -r requirements.txt` again |

## 🎯 Next Steps

1. **Register your pharmacy** at /register
2. **Add products** from inventory menu
3. **Create suppliers** and purchase stock
4. **Start making sales** using POS
5. **Monitor alerts** for stock/expiry
6. **Generate reports** for analysis
7. **Track finances** in accounting module

## 📊 Business Workflows

### Daily Operations
1. Open POS → Scan products → Select payment → Confirm sale
2. Review dashboard for alerts and sales
3. Process any sales returns
4. Check stock levels

### Weekly Tasks
1. Create purchase orders for low-stock items
2. Review sales reports
3. Check customer outstanding balances

### Monthly Tasks
1. Generate P&L report
2. Review expense categories
3. Pay supplier invoices
4. Collect customer payments
5. Analyze sales trends

## 🚀 Production Deployment

Before going live:
1. Change SECRET_KEY to a secure random value
2. Set FLASK_ENV=production
3. Use PostgreSQL (optional, better for production)
4. Configure HTTPS/SSL certificate
5. Use production WSGI server (Gunicorn)
6. Set up database backups
7. Configure logging and monitoring
8. Test all workflows thoroughly

## 💡 Tips & Best Practices

- ✅ Regularly backup your database
- ✅ Keep product information updated
- ✅ Review alerts daily
- ✅ Use consistent naming for categories
- ✅ Maintain supplier and customer records
- ✅ Monitor low-stock items
- ✅ Review P&L reports monthly
- ✅ Keep receipts for expenses

## 🤝 Extensibility

The system is designed for easy extension:
- Add new product fields in `models.py`
- Create new reports in `reports.py`
- Add custom alerts in `alerts.py`
- Extend templates for custom branding
- Add new modules following the pattern

## 📞 Support & Troubleshooting

**If you encounter issues:**

1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed docs
2. Review Flask debug output in terminal
3. Check database file exists (pharmacy.db)
4. Verify all dependencies installed
5. Check file/directory permissions
6. Review browser console for JavaScript errors

## 📄 License & Usage

This system is provided for pharmacy business management. Use it to efficiently manage your pharmacy operations.

## 🎉 Features Summary

| Feature | Status | Module |
|---------|--------|--------|
| Company Registration | ✅ | Auth |
| User Authentication | ✅ | Auth |
| Dashboard | ✅ | Dashboard |
| Product Management | ✅ | Inventory |
| Stock Tracking | ✅ | Inventory |
| POS/Sales | ✅ | Sales |
| Invoicing | ✅ | Sales |
| Purchases | ✅ | Purchases |
| Customers | ✅ | Customers |
| Suppliers | ✅ | Suppliers |
| Accounting | ✅ | Accounting |
| Reports | ✅ | Reports |
| Alerts | ✅ | Alerts |

---

**Version**: 1.0
**Last Updated**: February 20, 2026
**Framework**: Flask + SQLAlchemy
**Database**: SQLite3
**UI**: Bootstrap 5

**Ready to go!** 🚀 Start your pharmacy management journey now! 💊
