from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse
from .models import Product, InventoryTransaction
from .forms import ProductForm, ScanForm
import datetime
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import openpyxl
from io import BytesIO
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, InventoryTransaction
from .forms import ScanForm
from django.shortcuts import render, get_object_or_404
from .models import Product, InventoryTransaction
from .forms import ScanForm
from django.shortcuts import render
from django.utils.dateparse import parse_date
from .models import Product, InventoryTransaction
import io
from django.http import FileResponse, HttpResponse
from django.utils.dateparse import parse_date
from django.shortcuts import render
from .models import Product, InventoryTransaction
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Product

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect to a dashboard or homepage after login
            return redirect('warehouse:dashboard')  # change as needed
    else:
        form = AuthenticationForm()

    return render(request, 'warehouse/login.html', {'form': form})

@login_required
def dashboard(request):
    today = datetime.date.today()
    start_month = today.replace(day=1)
    daily_in = InventoryTransaction.objects.filter(created_at__date=today, tx_type=InventoryTransaction.INCOME).aggregate(total=Sum('quantity'))['total'] or 0
    daily_out = InventoryTransaction.objects.filter(created_at__date=today, tx_type=InventoryTransaction.OUTGOING).aggregate(total=Sum('quantity'))['total'] or 0
    month_in = InventoryTransaction.objects.filter(created_at__date__gte=start_month, tx_type=InventoryTransaction.INCOME).aggregate(total=Sum('quantity'))['total'] or 0
    month_out = InventoryTransaction.objects.filter(created_at__date__gte=start_month, tx_type=InventoryTransaction.OUTGOING).aggregate(total=Sum('quantity'))['total'] or 0
    top_products = (InventoryTransaction.objects.filter(created_at__date__gte=start_month, tx_type=InventoryTransaction.OUTGOING)
                    .values('product__sku','product__name').annotate(total=Sum('quantity')).order_by('-total')[:10])
    context = {'daily_in':daily_in,'daily_out':daily_out,'month_in':month_in,'month_out':month_out,'top_products':top_products}
    return render(request,'warehouse/dashboard.html',context)
@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request,'warehouse/product_list.html',{'products':products})
@login_required
def product_add(request):
    if request.method=='POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('warehouse:product_list')
    else:
        form = ProductForm()
    return render(request,'warehouse/product_add.html',{'form':form})

@login_required
def income(request):
    message = None
    form = ScanForm()

    if request.method == 'POST':
        if 'remove_id' in request.POST:
            tx_id = request.POST.get('remove_id')
            tx = get_object_or_404(
                InventoryTransaction, id=tx_id, tx_type=InventoryTransaction.INCOME
            )
            product = tx.product
            product.quantity = max(0, product.quantity - tx.quantity)
            product.save()
            tx.delete()
            # Save message to session so it can be shown after redirect
            request.session['message'] = f"Removed transaction #{tx_id} and adjusted stock."
            return redirect('warehouse:income')  # Use your url name here

        form = ScanForm(request.POST)
        if form.is_valid():
            sku = form.cleaned_data['sku'].strip()
            qty = form.cleaned_data['quantity']
            note = form.cleaned_data.get('note', '')

            product, created = Product.objects.get_or_create(
                sku=sku, defaults={'name': sku, 'quantity': 0}
            )
            product.quantity += qty
            product.save()

            InventoryTransaction.objects.create(
                product=product,
                tx_type=InventoryTransaction.INCOME,
                quantity=qty,
                note=note,
            )
            request.session['message'] = f"Added {qty} to {product.sku}"
            return redirect('warehouse:income')

    # GET or fallback

    # Retrieve and clear message from session
    message = request.session.pop('message', None)

    updates = InventoryTransaction.objects.filter(
        tx_type=InventoryTransaction.INCOME
    ).order_by('-created_at')[:20]

    return render(request, 'warehouse/income.html', {
        'form': form,
        'message': message,
        'updates': updates
    })

@login_required
def outgoing(request):
    if request.method == 'POST':
        if 'remove_id' in request.POST:
            tx_id = request.POST.get('remove_id')
            tx = get_object_or_404(
                InventoryTransaction, id=tx_id, tx_type=InventoryTransaction.OUTGOING
            )
            product = tx.product
            product.quantity += tx.quantity
            product.save()
            tx.delete()
            request.session['message'] = f"Removed outgoing transaction #{tx_id} and restored stock."
            return redirect('warehouse:outgoing')  # Adjust URL name accordingly

        form = ScanForm(request.POST)
        if form.is_valid():
            sku = form.cleaned_data['sku'].strip()
            qty = form.cleaned_data['quantity']
            note = form.cleaned_data.get('note', '')

            product = get_object_or_404(Product, sku=sku)
            product.quantity = max(0, product.quantity - qty)
            product.save()

            InventoryTransaction.objects.create(
                product=product,
                tx_type=InventoryTransaction.OUTGOING,
                quantity=qty,
                note=note,
            )
            request.session['message'] = f"Removed {qty} from {product.sku}"
            return redirect('warehouse:outgoing')
    else:
        form = ScanForm()

    # GET or fallback
    message = request.session.pop('message', None)
    updates = InventoryTransaction.objects.filter(
        tx_type=InventoryTransaction.OUTGOING
    ).order_by('-created_at')[:20]

    return render(request, 'warehouse/outgoing.html', {
        'form': form,
        'message': message,
        'updates': updates
    })

@login_required
def stock_report(request):
    date_range = request.GET.get('date_range', '')
    start_date, end_date = None, None

    if date_range and " to " in date_range:
        start_str, end_str = date_range.split(" to ")
        start_date, end_date = parse_date(start_str), parse_date(end_str)

    products = Product.objects.all()

    if start_date and end_date:
        tx_products = InventoryTransaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values_list('product_id', flat=True).distinct()
        products = products.filter(id__in=tx_products)

    # Export Excel
    if 'export' in request.GET and request.GET['export'] == 'excel':
        return export_stock_excel(products)

    # Export PDF
    if 'export' in request.GET and request.GET['export'] == 'pdf':
        return export_stock_pdf(products)

    return render(request, 'warehouse/stock_report.html', {
        'products': products,
        'date_range': date_range,
    })

@login_required
def export_stock_excel(products):
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Report"
    ws.append(["SKU", "Name", "Quantity", "Created At"])

    for p in products:
        ws.append([p.sku, p.name, p.quantity, p.created_at.strftime('%Y-%m-%d %H:%M')])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=stock_report.xlsx'
    wb.save(response)
    return response

@login_required
def export_stock_pdf(products):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    data = [["SKU", "Name", "Quantity", "Created At"]]
    for p in products:
        data.append([p.sku, p.name, str(p.quantity), p.created_at.strftime('%Y-%m-%d %H:%M')])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(Paragraph("Stock Report", styles['Title']))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename='stock_report.pdf')

@login_required
def report(request):
    txs = InventoryTransaction.objects.all().order_by('-created_at')[:200]
    return render(request,'warehouse/report.html',{'txs':txs})
@login_required
def export_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"
    ws.append(['Date','SKU','Product','Type','Quantity','Note'])
    for tx in InventoryTransaction.objects.all().order_by('-created_at'):
        ws.append([tx.created_at.strftime('%Y-%m-%d %H:%M:%S'), tx.product.sku, tx.product.name, tx.tx_type, tx.quantity, tx.note])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    resp = HttpResponse(bio.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename=inventory_report.xlsx'
    return resp
@login_required
def export_pdf(request):
    txs = InventoryTransaction.objects.all().order_by('-created_at')[:500]
    html = render_to_string('warehouse/report_pdf.html', {'txs':txs})
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    resp = HttpResponse(result.getvalue(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename=inventory_report.pdf'
    return resp

@login_required
def product_autocomplete(request):
    term = request.GET.get('term', '')
    products = Product.objects.filter(
        Q(name__icontains=term) | Q(sku__icontains=term)
    )[:10]

    results = []
    for p in products:
        results.append({
            'label': f"{p.name} ({p.sku})",  # what shows in the dropdown
            'value': p.sku,  # what gets inserted into the input
        })

    return JsonResponse(results, safe=False)

def user_logout(request):
    logout(request)
    return redirect('warehouse:login')  # or wherever you want to redirect
