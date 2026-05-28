from django.db import connection


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dictfetchone(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


# ═══════════════════════════════════════════════════════════
# EMPLOYEES
# ═══════════════════════════════════════════════════════════

def get_all_employees():
    with connection.cursor() as c:
        c.execute("""
            SELECT id_employee, empl_surname, empl_name, empl_patronymic,
                   empl_role, salary, date_of_birth, date_of_start,
                   phone_number, city, street, zip_code
            FROM Employee
            ORDER BY empl_surname
        """)
        return dictfetchall(c)


def get_cashiers():
    with connection.cursor() as c:
        c.execute("""
            SELECT id_employee, empl_surname, empl_name, empl_patronymic,
                   empl_role, salary, date_of_birth, date_of_start,
                   phone_number, city, street, zip_code
            FROM Employee
            WHERE empl_role = 'Cashier'
            ORDER BY empl_surname
        """)
        return dictfetchall(c)


def get_employee_by_id(eid):
    with connection.cursor() as c:
        c.execute("""
            SELECT id_employee, empl_surname, empl_name, empl_patronymic,
                   empl_role, salary, date_of_birth, date_of_start,
                   phone_number, city, street, zip_code
            FROM Employee
            WHERE id_employee = %s
        """, [eid])
        return dictfetchall(c)


def get_employee_phone_by_surname(surname):
    with connection.cursor() as c:
        c.execute("""
            SELECT id_employee, empl_surname, empl_name, empl_patronymic,
                   phone_number, city, street, zip_code
            FROM Employee
            WHERE empl_surname LIKE %s
            ORDER BY empl_surname
        """, [f'%{surname}%'])
        return dictfetchall(c)


def create_employee(d):
    with connection.cursor() as c:
        c.execute("""
            INSERT INTO Employee (
                id_employee, empl_surname, empl_name, empl_patronymic,
                empl_role, salary, date_of_birth, date_of_start,
                phone_number, city, street, zip_code
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            d['id_employee'], d['empl_surname'], d['empl_name'],
            d.get('empl_patronymic', ''), d['empl_role'], d['salary'],
            d['date_of_birth'], d['date_of_start'], d['phone_number'],
            d['city'], d['street'], d['zip_code']
        ])


def update_employee(d):
    with connection.cursor() as c:
        c.execute("""
            UPDATE Employee
            SET empl_surname = %s, empl_name = %s, empl_patronymic = %s,
                empl_role = %s, salary = %s, date_of_birth = %s,
                date_of_start = %s, phone_number = %s,
                city = %s, street = %s, zip_code = %s
            WHERE id_employee = %s
        """, [
            d['empl_surname'], d['empl_name'], d.get('empl_patronymic', ''),
            d['empl_role'], d['salary'], d['date_of_birth'],
            d['date_of_start'], d['phone_number'],
            d['city'], d['street'], d['zip_code'], d['id_employee']
        ])


def delete_employee(eid):
    with connection.cursor() as c:
        c.execute("DELETE FROM Employee WHERE id_employee = %s", [eid])


# ═══════════════════════════════════════════════════════════
# CATEGORIES
# ═══════════════════════════════════════════════════════════

def get_all_categories():
    with connection.cursor() as c:
        c.execute("""
            SELECT category_number, category_name
            FROM Category
            ORDER BY category_name
        """)
        return dictfetchall(c)


def get_category_by_id(num):
    with connection.cursor() as c:
        c.execute("""
            SELECT category_number, category_name
            FROM Category
            WHERE category_number = %s
        """, [num])
        return dictfetchone(c)


def create_category(name):
    with connection.cursor() as c:
        c.execute("""
            INSERT INTO Category (category_name) VALUES (%s)
        """, [name])


def update_category(num, name):
    with connection.cursor() as c:
        c.execute("""
            UPDATE Category SET category_name = %s
            WHERE category_number = %s
        """, [name, num])


def delete_category(num):
    with connection.cursor() as c:
        c.execute("""
            DELETE FROM Category WHERE category_number = %s
        """, [num])


# ═══════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════

def get_all_products(category=None, name=None):
    with connection.cursor() as c:
        sql = """
            SELECT P.id_product, P.category_number, P.product_name,
                   P.producer, P.characteristics, C.category_name
            FROM Product P
            JOIN Category C ON C.category_number = P.category_number
            WHERE 1=1
        """
        params = []
        if category:
            sql += " AND P.category_number = %s"
            params.append(category)
        if name:
            sql += " AND P.product_name LIKE %s"
            params.append(f'%{name}%')
        sql += " ORDER BY P.product_name"
        c.execute(sql, params)
        return dictfetchall(c)


def get_product_by_id(pid):
    with connection.cursor() as c:
        c.execute("""
            SELECT P.id_product, P.category_number, P.product_name,
                   P.producer, P.characteristics, C.category_name
            FROM Product P
            JOIN Category C ON C.category_number = P.category_number
            WHERE P.id_product = %s
        """, [pid])
        return dictfetchone(c)


def create_product(d):
    with connection.cursor() as c:
        c.execute("""
            INSERT INTO Product (category_number, product_name, producer, characteristics)
            VALUES (%s, %s, %s, %s)
        """, [d['category_number'], d['product_name'],
              d.get('producer', ''), d['characteristics']])


def update_product(d):
    with connection.cursor() as c:
        c.execute("""
            UPDATE Product
            SET category_number = %s, product_name = %s,
                producer = %s, characteristics = %s
            WHERE id_product = %s
        """, [d['category_number'], d['product_name'],
              d.get('producer', ''), d['characteristics'], d['id_product']])


# ═══════════════════════════════════════════════════════════
# STORE PRODUCTS
# ═══════════════════════════════════════════════════════════

def get_all_store_products(promo=None, order_by='products_number'):
    allowed_orders = ['products_number', 'product_name', 'selling_price']
    if order_by not in allowed_orders:
        order_by = 'products_number'
    with connection.cursor() as c:
        sql = """
            SELECT SP.UPC, SP.UPC_prom, SP.id_product, SP.selling_price,
                   SP.products_number, SP.promotional_product,
                   P.product_name, P.characteristics
            FROM Store_Product SP
            JOIN Product P ON P.id_product = SP.id_product
            WHERE 1=1
        """
        params = []
        if promo is True:
            sql += " AND SP.promotional_product = 1"
        elif promo is False:
            sql += " AND SP.promotional_product = 0"
        sql += f" ORDER BY {order_by}"
        c.execute(sql, params)
        return dictfetchall(c)


def get_store_product_by_upc(upc):
    with connection.cursor() as c:
        c.execute("""
            SELECT SP.UPC, SP.UPC_prom, SP.id_product, SP.selling_price,
                   SP.products_number, SP.promotional_product,
                   P.product_name, P.characteristics
            FROM Store_Product SP
            JOIN Product P ON P.id_product = SP.id_product
            WHERE SP.UPC = %s
        """, [upc])
        return dictfetchone(c)


def create_store_product(d):
    with connection.cursor() as c:
        c.execute("""
            INSERT INTO Store_Product (
                UPC, UPC_prom, id_product, selling_price,
                products_number, promotional_product
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, [
            d['UPC'], d.get('UPC_prom') or None, d['id_product'],
            d['selling_price'], d['products_number'], d['promotional_product']
        ])


def update_store_product(d):
    with connection.cursor() as c:
        c.execute("""
            UPDATE Store_Product
            SET UPC_prom = %s, id_product = %s, selling_price = %s,
                products_number = %s, promotional_product = %s
            WHERE UPC = %s
        """, [
            d.get('UPC_prom') or None, d['id_product'], d['selling_price'],
            d['products_number'], d['promotional_product'], d['UPC']
        ])


def delete_store_product(upc):
    with connection.cursor() as c:
        c.execute("DELETE FROM Store_Product WHERE UPC = %s", [upc])


# ═══════════════════════════════════════════════════════════
# CUSTOMER CARDS
# ═══════════════════════════════════════════════════════════

def get_all_customers(percent=None, surname=None):
    with connection.cursor() as c:
        sql = """
            SELECT card_number, cust_surname, cust_name, cust_patronymic,
                   phone_number, city, street, zip_code, percent
            FROM Customer_Card
            WHERE 1=1
        """
        params = []
        if percent:
            sql += " AND percent = %s"
            params.append(percent)
        if surname:
            sql += " AND cust_surname LIKE %s"
            params.append(f'%{surname}%')
        sql += " ORDER BY cust_surname"
        c.execute(sql, params)
        return dictfetchall(c)


def get_customer_by_card(card):
    with connection.cursor() as c:
        c.execute("""
            SELECT card_number, cust_surname, cust_name, cust_patronymic,
                   phone_number, city, street, zip_code, percent
            FROM Customer_Card
            WHERE card_number = %s
        """, [card])
        return dictfetchone(c)


def create_customer(d):
    with connection.cursor() as c:
        c.execute("""
            INSERT INTO Customer_Card (
                card_number, cust_surname, cust_name, cust_patronymic,
                phone_number, city, street, zip_code, percent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            d['card_number'], d['cust_surname'], d['cust_name'],
            d.get('cust_patronymic', ''), d['phone_number'],
            d.get('city', ''), d.get('street', ''),
            d.get('zip_code', ''), d['percent']
        ])


def update_customer(d):
    with connection.cursor() as c:
        c.execute("""
            UPDATE Customer_Card
            SET cust_surname = %s, cust_name = %s, cust_patronymic = %s,
                phone_number = %s, city = %s, street = %s,
                zip_code = %s, percent = %s
            WHERE card_number = %s
        """, [
            d['cust_surname'], d['cust_name'], d.get('cust_patronymic', ''),
            d['phone_number'], d.get('city', ''), d.get('street', ''),
            d.get('zip_code', ''), d['percent'], d['card_number']
        ])


def delete_customer(card):
    with connection.cursor() as c:
        c.execute("DELETE FROM Customer_Card WHERE card_number = %s", [card])


# ═══════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════

def get_checks(employee_id=None, date_from=None, date_to=None):
    with connection.cursor() as c:
        sql = """
            SELECT CH.check_number, CH.id_employee, CH.card_number,
                   CH.print_date, CH.sum_total, CH.vat,
                   E.empl_surname || ' ' || E.empl_name AS cashier_name,
                   CC.cust_surname
            FROM Chek CH
            JOIN Employee E ON E.id_employee = CH.id_employee
            LEFT JOIN Customer_Card CC ON CC.card_number = CH.card_number
            WHERE 1=1
        """
        params = []
        if employee_id:
            sql += " AND CH.id_employee = %s"
            params.append(employee_id)
        if date_from:
            sql += " AND DATE(CH.print_date) >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND DATE(CH.print_date) <= %s"
            params.append(date_to)
        sql += " ORDER BY CH.print_date DESC"
        c.execute(sql, params)
        return dictfetchall(c)


def get_check_by_number(check_number):
    with connection.cursor() as c:
        c.execute("""
            SELECT CH.check_number, CH.id_employee, CH.card_number,
                   CH.print_date, CH.sum_total, CH.vat,
                   E.empl_surname || ' ' || E.empl_name AS cashier_name,
                   CC.cust_surname, CC.percent
            FROM Chek CH
            JOIN Employee E ON E.id_employee = CH.id_employee
            LEFT JOIN Customer_Card CC ON CC.card_number = CH.card_number
            WHERE CH.check_number = %s
        """, [check_number])
        return dictfetchone(c)


def get_check_detail(check_number):
    with connection.cursor() as c:
        c.execute("""
            SELECT S.UPC, S.check_number, S.product_number, S.selling_price,
                   P.product_name,
                   S.product_number * S.selling_price AS line_total
            FROM Sale S
            JOIN Store_Product SP ON SP.UPC = S.UPC
            JOIN Product P ON P.id_product = SP.id_product
            WHERE S.check_number = %s
        """, [check_number])
        return dictfetchall(c)


def create_check(d, items):
    with connection.cursor() as c:
        c.execute("""
            INSERT INTO Chek (
                check_number, id_employee, card_number,
                print_date, sum_total, vat
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, [
            d['check_number'], d['id_employee'],
            d.get('card_number') or None,
            d['print_date'], d['sum_total'], d['vat']
        ])
        for item in items:
            c.execute("""
                INSERT INTO Sale (UPC, check_number, product_number, selling_price)
                VALUES (%s, %s, %s, %s)
            """, [
                item['UPC'], d['check_number'],
                item['product_number'], item['selling_price']
            ])
            c.execute("""
                UPDATE Store_Product
                SET products_number = products_number - %s
                WHERE UPC = %s
            """, [item['product_number'], item['UPC']])


def delete_check(check_number):
    with connection.cursor() as c:
        c.execute("DELETE FROM Sale WHERE check_number = %s", [check_number])
        c.execute("DELETE FROM Chek WHERE check_number = %s", [check_number])


def get_total_sales(employee_id=None, date_from=None, date_to=None):
    with connection.cursor() as c:
        sql = """
            SELECT COALESCE(SUM(sum_total), 0) AS total
            FROM Chek
            WHERE 1=1
        """
        params = []
        if employee_id:
            sql += " AND id_employee = %s"
            params.append(employee_id)
        if date_from:
            sql += " AND DATE(print_date) >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND DATE(print_date) <= %s"
            params.append(date_to)
        c.execute(sql, params)
        row = c.fetchone()
        return row[0] if row else 0


def get_product_units_sold(upc, date_from=None, date_to=None):
    with connection.cursor() as c:
        sql = """
            SELECT COALESCE(SUM(S.product_number), 0) AS total
            FROM Sale S
            JOIN Chek CH ON CH.check_number = S.check_number
            WHERE S.UPC = %s
        """
        params = [upc]
        if date_from:
            sql += " AND DATE(CH.print_date) >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND DATE(CH.print_date) <= %s"
            params.append(date_to)
        c.execute(sql, params)
        row = c.fetchone()
        return row[0] if row else 0


# ═══════════════════════════════════════════════════════════
# CUSTOM SQL QUERIES
# ═══════════════════════════════════════════════════════════

def query_categories_with_sales(date_from=None, date_to=None):
    with connection.cursor() as c:
        sql = """
            SELECT C.category_number,
                   C.category_name,
                   COUNT(DISTINCT SP.UPC)            AS distinct_products_count,
                   SUM(S.product_number)             AS total_units_sold,
                   SUM(S.product_number * S.selling_price) AS total_sales_amount,
                   AVG(S.selling_price)              AS avg_selling_price
            FROM Category C
            JOIN Product P       ON P.category_number = C.category_number
            JOIN Store_Product SP ON SP.id_product    = P.id_product
            JOIN Sale S          ON S.UPC             = SP.UPC
            JOIN Chek CH         ON CH.check_number   = S.check_number
            WHERE 1=1
        """
        params = []
        if date_from:
            sql += " AND DATE(CH.print_date) >= %s"
            params.append(date_from)
        if date_to:
            sql += " AND DATE(CH.print_date) <= %s"
            params.append(date_to)
        sql += """
            GROUP BY C.category_number, C.category_name
            HAVING SUM(S.product_number) > 100
            ORDER BY SUM(S.product_number * S.selling_price) DESC
        """
        c.execute(sql, params)
        return dictfetchall(c)


def query_cashiers_only_promo():
    with connection.cursor() as c:
        c.execute("""
            SELECT E.id_employee, E.empl_surname,
                   E.empl_name, E.empl_patronymic
            FROM Employee E
            WHERE EXISTS (
                SELECT 1
                FROM Chek CH
                WHERE CH.id_employee = E.id_employee
            )
            AND NOT EXISTS (
                SELECT 1
                FROM Chek CH
                JOIN Sale S          ON S.check_number = CH.check_number
                JOIN Store_Product SP ON SP.UPC         = S.UPC
                WHERE CH.id_employee = E.id_employee
                AND NOT EXISTS (
                    SELECT 1
                    FROM Store_Product SP2
                    WHERE SP2.UPC = S.UPC
                      AND SP2.promotional_product = 1
                )
            )
            ORDER BY E.empl_surname, E.empl_name
        """)
        return dictfetchall(c)