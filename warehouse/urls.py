from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.user_login, name='login'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('income/', views.income, name='income'),
    path('outgoing/', views.outgoing, name='outgoing'),
    path('stock-report/', views.stock_report, name='stock'),
    path('report/', views.report, name='report'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('product-autocomplete/', views.product_autocomplete, name='product_autocomplete'),
    path('logout/', views.user_logout, name='logout'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),

]
