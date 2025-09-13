from django.contrib import admin
from .models import Product, InventoryTransaction

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku','name','quantity')

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('product','tx_type','quantity','created_at')
