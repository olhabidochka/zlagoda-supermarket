from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Employees
    path('employees/', views.employees_list, name='employees'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<str:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<str:pk>/delete/', views.employee_delete, name='employee_delete'),

    # Categories
    path('categories/', views.categories_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Products
    path('products/', views.products_list, name='products'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Store Products
    path('store-products/', views.store_products_list, name='store_products'),
    path('store-products/create/', views.store_product_create, name='store_product_create'),
    path('store-products/<str:pk>/edit/', views.store_product_edit, name='store_product_edit'),
    path('store-products/<str:pk>/delete/', views.store_product_delete, name='store_product_delete'),

    # Customers
    path('customers/', views.customers_list, name='customers'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<str:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<str:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Checks
    path('checks/', views.checks_list, name='checks'),
    path('checks/create/', views.check_create, name='check_create'),
    path('checks/<str:pk>/', views.check_detail, name='check_detail'),
    path('checks/<str:pk>/delete/', views.check_delete, name='check_delete'),

    # Reports
    path('reports/', views.reports_page, name='reports'),
    path('reports/pdf/<str:report_type>/', views.download_report, name='download_report'),

    # Custom queries
    path('queries/', views.custom_queries, name='queries'),

    # Profile
    path('profile/', views.profile, name='profile'),
]