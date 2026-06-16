from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from datetime import date
import uuid
import datetime
from . import db_utils as db
from .reports import generate_html_report


def get_current_emp(request):
    emp_list = db.get_employee_by_id(request.user.username)
    return emp_list[0] if emp_list else None


def get_current_role(request):
    emp = get_current_emp(request)
    if emp:
        return emp['empl_role']
    return None


def is_manager(role):
    return role in ('Manager', 'Менеджер')


def is_cashier(role):
    return role in ('Cashier', 'Касир')


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_current_role(request)
        if not is_manager(role):
            return HttpResponseForbidden("Доступ заборонено. Тільки для менеджерів.")
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def flatten_post(post):
    return {k: v[0] if isinstance(v, list) else v for k, v in post.items()}


def validate_employee(data):
    errors = []
    if data.get('date_of_birth'):
        try:
            if isinstance(data['date_of_birth'], str):
                dob = date.fromisoformat(data['date_of_birth'])
            else:
                dob = data['date_of_birth']
            today = date.today()
            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
            if age < 18:
                errors.append('Вік працівника не може бути меншим за 18 років')
        except ValueError:
            errors.append('Невірний формат дати народження')
    if data.get('phone_number'):
        if len(data['phone_number']) > 13:
            errors.append('Номер телефону не може перевищувати 13 символів')
    if data.get('salary'):
        try:
            if float(data['salary']) < 0:
                errors.append('Зарплата не може бути від\'ємною')
        except ValueError:
            errors.append('Невірний формат зарплати')
    return errors


@login_required
def dashboard(request):
    emp = get_current_emp(request)
    role = emp.get('empl_role', '') if emp else ''
    return render(request, 'supermarket/dashboard.html', {'role': role, 'emp': emp or {}})


@login_required
def profile(request):
    emp = get_current_emp(request)
    return render(request, 'supermarket/profile.html', {'emp': emp or {}})


@manager_required
def employees_list(request):
    role_filter = request.GET.get('role_filter', '')
    surname = request.GET.get('surname', '')

    if role_filter in ('Cashier', 'Касир'):
        emps = db.get_cashiers()
    elif role_filter in ('Manager', 'Менеджер'):
        emps = db.get_managers()
    else:
        emps = db.get_all_employees()

    if surname:
        emps = [e for e in emps if surname.lower() in e['empl_surname'].lower()]

    return render(request, 'supermarket/employees.html', {
        'employees': emps,
        'surname': surname,
        'role_filter': role_filter,
    })


@manager_required
def employee_create(request):
    from dateutil.relativedelta import relativedelta
    max_date = (date.today() - relativedelta(years=18)).isoformat()
    if request.method == 'POST':
        data = flatten_post(request.POST)
        if data.get('password') != data.get('password_confirm'):
            messages.error(request, 'Паролі не співпадають')
            return render(request, 'supermarket/employee_form.html',
                         {'action': 'Додати', 'emp': data, 'max_date': max_date})
        if len(data.get('password', '')) < 8:
            messages.error(request, 'Пароль має бути мінімум 8 символів')
            return render(request, 'supermarket/employee_form.html',
                         {'action': 'Додати', 'emp': data, 'max_date': max_date})
        errors = validate_employee(data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'supermarket/employee_form.html',
                         {'action': 'Додати', 'emp': data, 'max_date': max_date})
        db.create_employee(data)
        from django.contrib.auth.models import User
        if not User.objects.filter(username=data['id_employee']).exists():
            User.objects.create_user(
                username=data['id_employee'],
                password=data['password']
            )
        messages.success(request, 'Працівника додано успішно')
        return redirect('employees')
    return render(request, 'supermarket/employee_form.html', {
        'action': 'Додати', 'emp': {}, 'max_date': max_date
    })


@manager_required
def employee_edit(request, pk):
    from dateutil.relativedelta import relativedelta
    max_date = (date.today() - relativedelta(years=18)).isoformat()
    emp_list = db.get_employee_by_id(pk)
    emp = emp_list[0] if emp_list else {}

    if emp:
        if emp.get('date_of_birth'):
            try:
                dob = str(emp['date_of_birth'])
                if len(dob) > 10:
                    dob = dob[:10]
                emp['date_of_birth'] = dob
            except:
                emp['date_of_birth'] = ''
        if emp.get('date_of_start'):
            try:
                dos = str(emp['date_of_start'])
                if len(dos) > 10:
                    dos = dos[:10]
                emp['date_of_start'] = dos
            except:
                emp['date_of_start'] = ''

    if request.method == 'POST':
        data = flatten_post(request.POST)
        data['id_employee'] = pk
        errors = validate_employee(data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'supermarket/employee_form.html',
                         {'action': 'Редагувати', 'emp': data, 'max_date': max_date})
        db.update_employee(data)
        new_password = data.get('new_password', '')
        if new_password:
            if len(new_password) < 8:
                messages.error(request, 'Пароль має бути мінімум 8 символів')
                return render(request, 'supermarket/employee_form.html',
                             {'action': 'Редагувати', 'emp': data, 'max_date': max_date})
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(username=pk)
                user.set_password(new_password)
                user.save()
            except User.DoesNotExist:
                User.objects.create_user(username=pk, password=new_password)
        messages.success(request, 'Дані працівника оновлено')
        return redirect('employees')

    return render(request, 'supermarket/employee_form.html', {
        'action': 'Редагувати', 'emp': emp, 'max_date': max_date
    })


@manager_required
def employee_delete(request, pk):
    db.delete_employee(pk)
    messages.success(request, 'Працівника видалено')
    return redirect('employees')


@login_required
def categories_list(request):
    cats = db.get_all_categories()
    role = get_current_role(request)
    return render(request, 'supermarket/categories.html', {
        'categories': cats, 'role': role
    })


@manager_required
def category_create(request):
    if request.method == 'POST':
        db.create_category(request.POST.get('category_name'))
        messages.success(request, 'Категорію додано')
        return redirect('categories')
    return render(request, 'supermarket/category_form.html', {
        'action': 'Додати', 'cat': {}
    })


@manager_required
def category_edit(request, pk):
    cat = db.get_category_by_id(pk)
    if request.method == 'POST':
        db.update_category(pk, request.POST.get('category_name'))
        messages.success(request, 'Категорію оновлено')
        return redirect('categories')
    return render(request, 'supermarket/category_form.html', {
        'action': 'Редагувати', 'cat': cat or {}
    })


@manager_required
def category_delete(request, pk):
    db.delete_category(pk)
    messages.success(request, 'Категорію видалено')
    return redirect('categories')


@login_required
def products_list(request):
    cat_id = request.GET.get('category', '')
    name = request.GET.get('name', '')
    role = get_current_role(request)
    prods = db.get_all_products(
        category=cat_id if cat_id else None,
        name=name if name else None
    )
    cats = db.get_all_categories()
    return render(request, 'supermarket/products.html', {
        'products': prods, 'categories': cats,
        'name': name, 'cat_id': cat_id, 'role': role
    })


@manager_required
def product_create(request):
    cats = db.get_all_categories()
    if request.method == 'POST':
        data = flatten_post(request.POST)
        db.create_product(data)
        messages.success(request, 'Товар додано')
        return redirect('products')
    return render(request, 'supermarket/product_form.html', {
        'action': 'Додати', 'categories': cats, 'prod': {}
    })


@manager_required
def product_edit(request, pk):
    prod = db.get_product_by_id(pk)
    cats = db.get_all_categories()
    if request.method == 'POST':
        data = flatten_post(request.POST)
        data['id_product'] = pk
        db.update_product(data)
        messages.success(request, 'Товар оновлено')
        return redirect('products')
    return render(request, 'supermarket/product_form.html', {
        'action': 'Редагувати', 'categories': cats, 'prod': prod or {}
    })


@manager_required
def product_delete(request, pk):
    db.delete_product(pk)
    messages.success(request, 'Товар видалено')
    return redirect('products')


@login_required
def store_products_list(request):
    promo_filter = request.GET.get('promo', '')
    order = request.GET.get('order', 'products_number')
    upc_search = request.GET.get('upc', '')
    role = get_current_role(request)

    if upc_search:
        item = db.get_store_product_by_upc(upc_search)
        items = [item] if item else []
    elif promo_filter == '1':
        items = db.get_all_store_products(promo=True, order_by=order)
    elif promo_filter == '0':
        items = db.get_all_store_products(promo=False, order_by=order)
    else:
        items = db.get_all_store_products(order_by=order)

    return render(request, 'supermarket/store_products.html', {
        'items': items, 'promo_filter': promo_filter,
        'order': order, 'upc_search': upc_search, 'role': role
    })


@manager_required
def store_product_create(request):
    prods = db.get_all_products()
    store_prods = db.get_all_store_products()
    if request.method == 'POST':
        data = flatten_post(request.POST)
        data['promotional_product'] = 1 if data.get('promotional_product') == 'on' else 0
        db.create_store_product(data)
        messages.success(request, 'Товар у магазині додано')
        return redirect('store_products')
    return render(request, 'supermarket/store_product_form.html', {
        'action': 'Додати', 'products': prods,
        'store_products': store_prods, 'item': {}
    })


@manager_required
def store_product_edit(request, pk):
    item = db.get_store_product_by_upc(pk)
    prods = db.get_all_products()
    store_prods = db.get_all_store_products()
    if request.method == 'POST':
        data = flatten_post(request.POST)
        data['UPC'] = pk
        data['promotional_product'] = 1 if data.get('promotional_product') == 'on' else 0
        db.update_store_product(data)
        messages.success(request, 'Товар у магазині оновлено')
        return redirect('store_products')
    return render(request, 'supermarket/store_product_form.html', {
        'action': 'Редагувати', 'products': prods,
        'store_products': store_prods, 'item': item or {}
    })


@manager_required
def store_product_delete(request, pk):
    db.delete_store_product(pk)
    messages.success(request, 'Товар видалено')
    return redirect('store_products')


@login_required
def customers_list(request):
    percent = request.GET.get('percent', '')
    surname = request.GET.get('surname', '')
    role = get_current_role(request)
    custs = db.get_all_customers(
        percent=percent if percent else None,
        surname=surname if surname else None
    )
    return render(request, 'supermarket/customers.html', {
        'customers': custs, 'percent': percent,
        'surname': surname, 'role': role
    })


@login_required
def customer_create(request):
    if request.method == 'POST':
        data = flatten_post(request.POST)
        db.create_customer(data)
        messages.success(request, 'Карту клієнта додано')
        return redirect('customers')
    return render(request, 'supermarket/customer_form.html', {
        'action': 'Додати', 'cust': {}
    })


@login_required
def customer_edit(request, pk):
    cust = db.get_customer_by_card(pk)
    if request.method == 'POST':
        data = flatten_post(request.POST)
        data['card_number'] = pk
        db.update_customer(data)
        messages.success(request, 'Дані клієнта оновлено')
        return redirect('customers')
    return render(request, 'supermarket/customer_form.html', {
        'action': 'Редагувати', 'cust': cust or {}
    })


@manager_required
def customer_delete(request, pk):
    db.delete_customer(pk)
    messages.success(request, 'Клієнта видалено')
    return redirect('customers')


@login_required
def checks_list(request):
    role = get_current_role(request)
    emp_id = request.user.username
    today = date.today().isoformat()

    if is_manager(role):
        filter_emp = request.GET.get('employee_id', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
    else:
        filter_emp = emp_id
        date_from = request.GET.get('date_from', today)
        date_to = request.GET.get('date_to', today)

    checks = db.get_checks(
        employee_id=filter_emp if filter_emp else None,
        date_from=date_from if date_from else None,
        date_to=date_to if date_to else None
    )
    total = db.get_total_sales(
        employee_id=filter_emp if filter_emp else None,
        date_from=date_from if date_from else None,
        date_to=date_to if date_to else None
    )
    cashiers = db.get_cashiers() if is_manager(role) else []

    return render(request, 'supermarket/checks.html', {
        'checks': checks, 'total': total,
        'cashiers': cashiers, 'role': role,
        'filter_emp': filter_emp,
        'date_from': date_from, 'date_to': date_to,
        'today': today,
    })


@login_required
def check_detail(request, pk):
    role = get_current_role(request)
    emp_id = request.user.username
    chk = db.get_check_by_number(pk)
    if not chk:
        messages.error(request, 'Чек не знайдено')
        return redirect('checks')
    if is_cashier(role) and chk['id_employee'] != emp_id:
        return HttpResponseForbidden("Доступ заборонено")
    items = db.get_check_detail(pk)
    return render(request, 'supermarket/check_detail.html', {
        'chk': chk, 'items': items, 'role': role
    })


@login_required
def check_create(request):
    role = get_current_role(request)
    if not is_cashier(role):
        return HttpResponseForbidden("Тільки касир може створювати чеки")

    store_prods = db.get_all_store_products()
    customers = db.get_all_customers()

    if request.method == 'POST':
        upcs = request.POST.getlist('upc')
        qtys = request.POST.getlist('qty')
        card = request.POST.get('card_number', '') or None

        items = []
        total = 0.0

        for upc, qty in zip(upcs, qtys):
            if not upc or not qty:
                continue
            prod = db.get_store_product_by_upc(upc)
            if not prod:
                continue
            price = float(prod['selling_price'])
            quantity = int(qty)
            total += price * quantity
            items.append({
                'UPC': upc,
                'product_number': quantity,
                'selling_price': price
            })

        if not items:
            messages.error(request, 'Додайте хоча б один товар')
            return render(request, 'supermarket/check_create.html', {
                'store_products': store_prods, 'customers': customers
            })

        if card:
            cust = db.get_customer_by_card(card)
            if cust:
                pct = cust['percent']
                total = total * (1 - pct / 100)

        check_number = str(uuid.uuid4())[:10].upper()
        vat = round(total * 0.2, 4)

        chk_data = {
            'check_number': check_number,
            'id_employee': request.user.username,
            'card_number': card,
            'print_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sum_total': round(total, 4),
            'vat': vat,
        }
        db.create_check(chk_data, items)
        messages.success(request, f'Чек {check_number} створено успішно')
        return redirect('checks')

    return render(request, 'supermarket/check_create.html', {
        'store_products': store_prods,
        'customers': customers
    })


@manager_required
def check_delete(request, pk):
    db.delete_check(pk)
    messages.success(request, 'Чек видалено')
    return redirect('checks')


@login_required
def units_sold(request):
    role = get_current_role(request)
    if not is_manager(role):
        return HttpResponseForbidden("Доступ заборонено")
    store_prods = db.get_all_store_products()
    result = None
    upc = request.GET.get('upc', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if upc:
        result = db.get_product_units_sold(
            upc,
            date_from if date_from else None,
            date_to if date_to else None
        )
    return render(request, 'supermarket/units_sold.html', {
        'store_products': store_prods,
        'result': result, 'upc': upc,
        'date_from': date_from, 'date_to': date_to,
    })


@login_required
def reports_page(request):
    role = get_current_role(request)
    if not is_manager(role):
        return HttpResponseForbidden("Доступ заборонено")
    cashiers = db.get_cashiers()
    return render(request, 'supermarket/reports.html', {'cashiers': cashiers})


@login_required
def download_report(request, report_type):
    role = get_current_role(request)
    if not is_manager(role):
        return HttpResponseForbidden("Доступ заборонено")

    emp_id = request.GET.get('employee_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if report_type == 'employees':
        data = db.get_all_employees()
        headers = ['ID', 'Прізвище', 'Ім\'я', 'По батькові', 'Посада',
                   'Зарплата', 'Дата нар.', 'Початок роботи',
                   'Телефон', 'Місто', 'Вулиця', 'Індекс']
        title = 'Звіт: Всі працівники'
    elif report_type == 'cashiers':
        data = db.get_cashiers()
        headers = ['ID', 'Прізвище', 'Ім\'я', 'По батькові', 'Посада',
                   'Зарплата', 'Дата нар.', 'Початок роботи',
                   'Телефон', 'Місто', 'Вулиця', 'Індекс']
        title = 'Звіт: Касири'
    elif report_type == 'customers':
        data = db.get_all_customers()
        headers = ['Карта №', 'Прізвище', 'Ім\'я', 'По батькові',
                   'Телефон', 'Місто', 'Вулиця', 'Індекс', 'Знижка %']
        title = 'Звіт: Клієнти'
    elif report_type == 'categories':
        data = db.get_all_categories()
        headers = ['№', 'Назва категорії']
        title = 'Звіт: Категорії'
    elif report_type == 'products':
        data = db.get_all_products()
        headers = ['ID', 'Категорія №', 'Назва', 'Виробник', 'Характеристики', 'Назва категорії']
        title = 'Звіт: Товари'
    elif report_type == 'store_products':
        data = db.get_all_store_products()
        headers = ['UPC', 'UPC акц.', 'ID товару', 'Ціна',
                   'К-сть', 'Акційний', 'Назва', 'Характеристики']
        title = 'Звіт: Товари в магазині'
    elif report_type == 'checks':
        data = db.get_checks(
            employee_id=emp_id if emp_id else None,
            date_from=date_from if date_from else None,
            date_to=date_to if date_to else None
        )
        headers = ['Чек №', 'Касир ID', 'Карта', 'Дата', 'Сума', 'ПДВ', 'Касир', 'Клієнт']
        title = 'Звіт: Чеки'
    else:
        return HttpResponse("Невідомий тип звіту", status=400)

    html = generate_html_report(title, headers, data, report_type)
    return HttpResponse(html, content_type='text/html; charset=utf-8')


@manager_required
def custom_queries(request):
    query1_data = []
    query2_data = []
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if request.GET.get('run_q1'):
        query1_data = db.query_categories_with_sales(
            date_from if date_from else None,
            date_to if date_to else None
        )
    if request.GET.get('run_q2'):
        query2_data = db.query_cashiers_only_promo()

    return render(request, 'supermarket/queries.html', {
        'q1': query1_data, 'q2': query2_data,
        'date_from': date_from, 'date_to': date_to
    })

@login_required
def profile(request):
    emp = get_current_emp(request)
    return render(request, 'supermarket/profile.html', {'emp': emp or {}})


@login_required
def profile_edit(request):
    from dateutil.relativedelta import relativedelta
    max_date = (date.today() - relativedelta(years=18)).isoformat()
    emp = get_current_emp(request)
    if not emp:
        return redirect('dashboard')

    if emp.get('date_of_birth'):
        try:
            dob = str(emp['date_of_birth'])
            if len(dob) > 10:
                dob = dob[:10]
            emp['date_of_birth'] = dob
        except:
            emp['date_of_birth'] = ''

    if emp.get('date_of_start'):
        try:
            dos = str(emp['date_of_start'])
            if len(dos) > 10:
                dos = dos[:10]
            emp['date_of_start'] = dos
        except:
            emp['date_of_start'] = ''

    if request.method == 'POST':
        data = flatten_post(request.POST)
        data['id_employee'] = request.user.username
        data['empl_role'] = emp['empl_role']
        data['salary'] = emp['salary']

        errors = validate_employee(data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'supermarket/profile_edit.html', {
                'emp': data, 'max_date': max_date
            })

        db.update_employee(data)

        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'Паролі не співпадають')
                return render(request, 'supermarket/profile_edit.html', {
                    'emp': data, 'max_date': max_date
                })
            if len(new_password) < 8:
                messages.error(request, 'Пароль має бути мінімум 8 символів')
                return render(request, 'supermarket/profile_edit.html', {
                    'emp': data, 'max_date': max_date
                })
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(username=request.user.username)
                user.set_password(new_password)
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
            except User.DoesNotExist:
                pass

        messages.success(request, 'Профіль оновлено успішно')
        return redirect('profile')

    return render(request, 'supermarket/profile_edit.html', {
        'emp': emp, 'max_date': max_date
    })