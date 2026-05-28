from django.contrib import admin
from .models import Employee, Category, Product, Store_Product, Customer_Card, Chek, Sale


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['id_employee', 'empl_surname', 'empl_name', 'empl_role', 'salary', 'phone_number']
    list_filter = ['empl_role']
    search_fields = ['empl_surname', 'empl_name', 'id_employee']
    ordering = ['empl_surname']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_number', 'category_name']
    search_fields = ['category_number','category_name']
    ordering = ['category_number','category_name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id_product', 'product_name', 'category_number', 'producer', 'characteristics']
    list_filter = ['category_number']
    search_fields = ['product_name','producer']
    ordering = ['product_name']


@admin.register(Store_Product)
class StoreProductAdmin(admin.ModelAdmin):
    list_display = ['UPC', 'id_product', 'selling_price', 'products_number', 'promotional_product']
    list_filter = ['promotional_product']
    search_fields = ['UPC']
    ordering = ['products_number']


@admin.register(Customer_Card)
class CustomerCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'cust_surname', 'cust_name', 'phone_number', 'percent']
    search_fields = ['cust_surname', 'card_number']
    ordering = ['cust_surname']


@admin.register(Chek)
class ChekAdmin(admin.ModelAdmin):
    list_display = ['check_number', 'id_employee', 'print_date', 'sum_total', 'vat']
    list_filter = ['print_date']
    search_fields = ['check_number']
    ordering = ['-print_date']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['UPC', 'check_number', 'product_number', 'selling_price']
    search_fields = ['check_number']
