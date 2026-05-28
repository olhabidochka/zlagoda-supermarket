from django.db import models


class Employee(models.Model):
    id_employee = models.CharField(max_length=10, primary_key=True)
    empl_surname = models.CharField(max_length=50)
    empl_name = models.CharField(max_length=50)
    empl_patronymic = models.CharField(max_length=50, null=True, blank=True)
    empl_role = models.CharField(max_length=10)
    salary = models.DecimalField(max_digits=13, decimal_places=4)
    date_of_birth = models.DateField()
    date_of_start = models.DateField()
    phone_number = models.CharField(max_length=13)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=9)

    class Meta:
        db_table = 'Employee'
        managed = True


class Category(models.Model):
    category_number = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50)

    class Meta:
        db_table = 'Category'
        managed = True


class Product(models.Model):
    id_product = models.AutoField(primary_key=True)
    category_number = models.ForeignKey(
        Category, on_delete=models.DO_NOTHING,
        db_column='category_number'
    )
    product_name = models.CharField(max_length=50)
    producer = models.CharField(max_length=50)
    characteristics = models.CharField(max_length=100)

    class Meta:
        db_table = 'Product'
        managed = True


class Store_Product(models.Model):
    UPC = models.CharField(max_length=12, primary_key=True)
    UPC_prom = models.CharField(max_length=12, null=True, blank=True)
    id_product = models.ForeignKey(
        Product, on_delete=models.DO_NOTHING,
        db_column='id_product'
    )
    selling_price = models.DecimalField(max_digits=13, decimal_places=4)
    products_number = models.IntegerField()
    promotional_product = models.BooleanField()

    class Meta:
        db_table = 'Store_Product'
        managed = True


class Customer_Card(models.Model):
    card_number = models.CharField(max_length=13, primary_key=True)
    cust_surname = models.CharField(max_length=50)
    cust_name = models.CharField(max_length=50)
    cust_patronymic = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=13)
    city = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=50, null=True, blank=True)
    zip_code = models.CharField(max_length=9, null=True, blank=True)
    percent = models.IntegerField()

    class Meta:
        db_table = 'Customer_Card'
        managed = True


class Chek(models.Model):
    check_number = models.CharField(max_length=10, primary_key=True)
    id_employee = models.ForeignKey(
        Employee, on_delete=models.DO_NOTHING,
        db_column='id_employee'
    )
    card_number = models.ForeignKey(
        Customer_Card, on_delete=models.DO_NOTHING,
        db_column='card_number', null=True, blank=True
    )
    print_date = models.DateTimeField()
    sum_total = models.DecimalField(max_digits=13, decimal_places=4)
    vat = models.DecimalField(max_digits=13, decimal_places=4)

    class Meta:
        db_table = 'Chek'
        managed = True


class Sale(models.Model):
    UPC = models.ForeignKey(
        Store_Product, on_delete=models.DO_NOTHING,
        db_column='UPC'
    )
    check_number = models.ForeignKey(
        Chek, on_delete=models.CASCADE,
        db_column='check_number'
    )
    product_number = models.IntegerField()
    selling_price = models.DecimalField(max_digits=13, decimal_places=4)

    class Meta:
        db_table = 'Sale'
        managed = True
        unique_together = (('UPC', 'check_number'),)