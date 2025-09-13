# Inventory Warehouse Django Project

Minimal Django project implementing:
- Navigation bar with: Income, Outgoing, Stock, Product, Dashboard, Report
- Income page: scan barcode (or paste barcode) + quantity to add incoming products
- Outgoing page: scan barcode to subtract quantity
- Product page: add new product
- Dashboard: daily & monthly monitoring (simple counts & usage)
- Report: export to Excel (.xlsx) and PDF

Setup:
1. Create virtualenv: `python -m venv venv && source venv/bin/activate` (on Windows use `venv\Scripts\activate`)
2. Install requirements: `pip install -r requirements.txt`
3. Apply migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Run server: `python manage.py runserver`

Notes:
- Barcode "scanning" works via a simple input field. Physical barcode scanners that act as keyboard will work automatically.
- PDF export uses xhtml2pdf; ensure wkhtmltopdf is NOT required for this basic setup.
- This is a starter project — further hardening, authentication, and production settings are needed for deployment.
