from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.views.decorators.http import require_POST
import uuid, datetime
from . import db_utils as db
from .reports import generate_pdf_report

def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        emp = db.get_employee_by_id(request.user.username)
        if not emp or emp[0]['empl_role'] != 'Manager':
            return HttpResponseForbidden("Доступ заборонено")
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

@login_required
def dashboard(request):
    emp = db.get_employee_by_id(request.user.username)
    role = emp[0]['empl_role'] if emp else 'Cashier'
    return render(request, 'supermarket/dashboard.html', {'role': role, 'emp': emp[0] if emp else {}})

@login_required
def profile(request):
    emp = db.get_employee_by_id(request.user.username)
    return render(request, 'supermarket/profile.html', {'emp': emp[0] if emp else {}})

# ── EMPLOYEES ────────────────────────────────────────────────────────────────

@manager_required
def employees_list(request):
    surname = request.GET.get('surname', '')
    role = request.GET.get('role', '')
    emps = db.get_cashiers() if role == 'Cashier' else db.get_all_employees()
    if surname:
        emps = [e for e in emps if surname.lower() in e['empl_surname'].lower()]
    return render(request, 'supermarket/employees.html', {'employees': emps, 'surname': surname, 'role': role})

@manager_required
def employee_create(request):
    if request.method == 'POST':
        db.create_employee(request.POST)
        messages.success(request, 'Працівника додано')
        return redirect('employees')
    return render(request, 'supermarket/employee_form.html', {'action': 'Додати'})

@manager_required
def employee_edit(request, pk):
    emp = db.get_employee_by_id(pk)
    if request.method == 'POST':
        data = dict(request.POST)
        data['id_employee'] = pk
        data = {k: v[0] if isinstance(v, list) else v for k, v in data.items()}
        db.update_employee(data)
        messages.success(request, 'Дані оновлено')
        return redirect('employees')
    return render(request, 'supermarket/employee_form.html', {'action': 'Редагувати', 'emp': emp[0] if emp else {}})

@manager_required
def employee_delete(request, pk):
    db.delete_employee(pk)
    messages.success(request, 'Працівника видалено')
    return redirect('employees')

# ── CATEGORIES ───────────────────────────────────────────────────────────────

@login_required
def categories_list(request):
    cats = db.get_all_categories()
    return render(request, 'supermarket/categories.html', {'categories': cats})

@manager_required
def category_create(request):
    if request.method == 'POST':
        db.create_category(request.POST['category_name'])
        messages.success(request, 'Категорію додано')
        return redirect('categories')
    return render(request, 'supermarket/category_form.html', {'action': 'Додати'})

@manager_required
def category_edit(request, pk):
    if request.method == 'POST':
        db.update_category(pk, request.POST['category_name'])
        messages.success(request, 'Категорію оновлено')
        return redirect('categories')
    cats = db.get_all_categories()
    cat = next((c for c in cats if c['category_number'] == pk), {})
    return render(request, 'supermarket/category_form.html', {'action': 'Редагувати', 'cat': cat})

@manager_required
def category_delete(request, pk):
    db.delete_category(pk)
    messages.success(request, 'Категорію видалено')
    return redirect('categories')

# ── PRODUCTS ─────────────────────────────────────────────────────────────────

@login_required
def products_list(request):
    cat_id = request.GET.get('category')
    name = request.GET.get('name', '')
    prods = db.get_all_products(cat_id)
    if name:
        prods = [p for p in prods if name.lower() in p['product_name'].lower()]
    cats = db.get_all_categories()
    return render(request, 'supermarket/products.html',
                  {'products': prods, 'categories': cats, 'name': name, 'cat_id': cat_id})

@manager_required
def product_create(request):
    cats = db.get_all_categories()
    if request.method == 'POST':
        db.create_product(request.POST)
        messages.success(request, 'Товар додано')
        return redirect('products')
    return render(request, 'supermarket/product_form.html', {'action': 'Додати', 'categories': cats})

@manager_required
def product_edit(request, pk):
    cats = db.get_all_categories()
    prod = db.get_product_by_id(pk)
    if request.method == 'POST':
        data = {k: v[0] if isinstance(v, list) else v for k, v in request.POST.items()}
        data['id_product'] = pk
        db.update_product(data)
        messages.success(request, 'Товар оновлено')
        return redirect('products')
    return render(request, 'supermarket/product_form.html',
                  {'action': 'Редагувати', 'categories': cats, 'prod': prod[0] if prod else {}})

@manager_required
def product_delete(request, pk):
    db.delete_product(pk)
    messages.success(request, 'Товар видалено')
    return redirect('products')

# ── STORE PRODUCTS ────────────────────────────────────────────────────────────

@login_required
def store_products_list(request):
    promo_filter = request.GET.get('promo')
    order = request.GET.get('order', 'products_number')
    upc_search = request.GET.get('upc', '')
    if promo_filter == '1':
        items = db.get_all_store_products(promo=True, order_by=order)
    elif promo_filter == '0':
        items = db.get_all_store_products(promo=False, order_by=order)
    else:
        items = db.get_all_store_products(order_by=order)
    if upc_search:
        found = db.get_store_product_by_upc(upc_search)
        return render(request, 'supermarket/store_products.html',
                      {'items': found, 'promo_filter': promo_filter, 'upc_search': upc_search})
    return render(request, 'supermarket/store_products.html',
                  {'items': items, 'promo_filter': promo_filter, 'order': order})

@manager_required
def store_product_create(request):
    prods = db.get_all_products()
    if request.method == 'POST':
        data = {k: v[0] if isinstance(v, list) else v for k, v in request.POST.items()}
        data['promotional_product'] = 1 if data.get('promotional_product') == 'on' else 0
        db.create_store_product(data)
        messages.success(request, 'Товар у магазині додано')
        return redirect('store_products')
    return render(request, 'supermarket/store_product_form.html', {'action': 'Додати', 'products': prods})

@manager_required
def store_product_edit(request, pk):
    prods = db.get_all_products()
    item = db.get_store_product_by_upc(pk)
    if request.method == 'POST':
        data = {k: v[0] if isinstance(v, list) else v for k, v in request.POST.items()}
        data['UPC'] = pk
        data['promotional_product'] = 1 if data.get('promotional_product') == 'on' else 0
        db.update_store_product(data)
        messages.success(request, 'Оновлено')
        return redirect('store_products')
    return render(request, 'supermarket/store_product_form.html',
                  {'action': 'Редагувати', 'products': prods, 'item': item[0] if item else {}})

@manager_required
def store_product_delete(request, pk):
    db.delete_store_product(pk)
    messages.success(request, 'Видалено')
    return redirect('store_products')

# ── CUSTOMERS ─────────────────────────────────────────────────────────────────

@login_required
def customers_list(request):
    percent = request.GET.get('percent')
    surname = request.GET.get('surname', '')
    custs = db.get_all_customers(percent)
    if surname:
        custs = [c for c in custs if surname.lower() in c['cust_surname'].lower()]
    return render(request, 'supermarket/customers.html',
                  {'customers': custs, 'percent': percent, 'surname': surname})

@login_required
def customer_create(request):
    if request.method == 'POST':
        data = {k: v[0] if isinstance(v, list) else v for k, v in request.POST.items()}
        db.create_customer(data)
        messages.success(request, 'Карту клієнта додано')
        return redirect('customers')
    return render(request, 'supermarket/customer_form.html', {'action': 'Додати'})

@login_required
def customer_edit(request, pk):
    cust = db.get_customer_by_card(pk)
    if request.method == 'POST':
        data = {k: v[0] if isinstance(v, list) else v for k, v in request.POST.items()}
        data['card_number'] = pk
        db.update_customer(data)
        messages.success(request, 'Оновлено')
        return redirect('customers')
    return render(request, 'supermarket/customer_form.html',
                  {'action': 'Редагувати', 'cust': cust[0] if cust else {}})

@manager_required
def customer_delete(request, pk):
    db.delete_customer(pk)
    messages.success(request, 'Видалено')
    return redirect('customers')

# ── CHECKS ────────────────────────────────────────────────────────────────────

@login_required
def checks_list(request):
    emp_id = request.user.username
    emp = db.get_employee_by_id(emp_id)
    role = emp[0]['empl_role'] if emp else 'Cashier'
    filter_emp = request.GET.get('employee_id') if role == 'Manager' else emp_id
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    checks = db.get_checks(filter_emp, date_from, date_to)
    total = db.get_total_sales(filter_emp, date_from, date_to)
    cashiers = db.get_cashiers() if role == 'Manager' else []
    return render(request, 'supermarket/checks.html',
                  {'checks': checks, 'total': total, 'cashiers': cashiers,
                   'role': role, 'filter_emp': filter_emp,
                   'date_from': date_from, 'date_to': date_to})

@login_required
def check_detail(request, pk):
    items = db.get_check_detail(pk)
    checks = db.get_checks()
    chk = next((c for c in checks if c['check_number'] == pk), {})
    return render(request, 'supermarket/check_detail.html', {'items': items, 'chk': chk})

@login_required
def check_create(request):
    emp = db.get_employee_by_id(request.user.username)
    role = emp[0]['empl_role'] if emp else 'Cashier'
    if role != 'Cashier':
        return HttpResponseForbidden("Тільки касир може створювати чеки")
    store_prods = db.get_all_store_products()
    customers = db.get_all_customers()
    if request.method == 'POST':
        upcs = request.POST.getlist('upc')
        qtys = request.POST.getlist('qty')
        prices = request.POST.getlist('price')
        card = request.POST.get('card_number') or None
        items = []
        total = 0
        for u, q, p in zip(upcs, qtys, prices):
            if u and q and p:
                amount = int(q) * float(p)
                total += amount
                items.append({'UPC': u, 'product_number': int(q), 'selling_price': float(p)})
        if card:
            cust = db.get_customer_by_card(card)
            if cust:
                pct = cust[0]['percent']
                total = total * (1 - pct / 100)
        check_number = str(uuid.uuid4())[:10].upper()
        vat = round(total * 0.2, 4)
        chk_data = {
            'check_number': check_number,
            'id_employee': request.user.username,
            'card_number': card,
            'print_date': datetime.datetime.now(),
            'sum_total': round(total, 4),
            'vat': vat,
        }
        db.create_check(chk_data, items)
        messages.success(request, f'Чек {check_number} створено')
        return redirect('checks')
    return render(request, 'supermarket/check_create.html',
                  {'store_products': store_prods, 'customers': customers})

@manager_required
def check_delete(request, pk):
    db.delete_check(pk)
    messages.success(request, 'Чек видалено')
    return redirect('checks')

# ── REPORTS ────────────────────────────────────────────────────────────────────

@login_required
def reports_page(request):
    return render(request, 'supermarket/reports.html')

@login_required
def download_report(request, report_type):
    if report_type == 'employees':
        data = db.get_all_employees()
        headers = ['ID', 'Прізвище', 'Ім\'я', 'По батькові', 'Посада', 'Зарплата',
                   'Нар.', 'Початок роботи', 'Телефон', 'Місто', 'Вулиця', 'Індекс']
        title = 'Звіт: Всі працівники'
    elif report_type == 'customers':
        data = db.get_all_customers()
        headers = ['Карта', 'Прізвище', 'Ім\'я', 'По батькові', 'Телефон',
                   'Місто', 'Вулиця', 'Індекс', 'Знижка %']
        title = 'Звіт: Клієнти'
    elif report_type == 'products':
        data = db.get_all_products()
        headers = ['ID', 'Категорія', 'Назва', 'Характеристики', 'Назва категорії']
        title = 'Звіт: Товари'
    elif report_type == 'store_products':
        data = db.get_all_store_products()
        headers = ['UPC', 'UPC_акц', 'ID товару', 'Ціна', 'К-сть', 'Акційний', 'Назва', 'Харак.']
        title = 'Звіт: Товари в магазині'
    elif report_type == 'checks':
        emp_id = request.GET.get('employee_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        data = db.get_checks(emp_id, date_from, date_to)
        headers = ['Чек №', 'Касир ID', 'Карта', 'Дата', 'Сума', 'ПДВ', 'Касир', 'Клієнт']
        title = 'Звіт: Чеки'
    else:
        return HttpResponse("Невідомий тип звіту", status=400)
    buffer = generate_pdf_report(title, headers, data)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.pdf"'
    return response

# ── CUSTOM QUERIES ─────────────────────────────────────────────────────────────

@login_required
def custom_queries(request):
    emp = db.get_employee_by_id(request.user.username)
    role = emp[0]['empl_role'] if emp else 'Cashier'
    if role != 'Manager':
        return HttpResponseForbidden("Доступ заборонено")
    query1_data = []
    query2_data = []
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if request.GET.get('run_q1'):
        query1_data = db.query_categories_with_sales(date_from, date_to)
    if request.GET.get('run_q2'):
        query2_data = db.query_cashiers_only_promo()
    return render(request, 'supermarket/queries.html',
                  {'q1': query1_data, 'q2': query2_data,
                   'date_from': date_from, 'date_to': date_to})
