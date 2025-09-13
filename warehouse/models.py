from django.db import models

class Product(models.Model):
    sku = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.name} ({self.sku})'

class InventoryTransaction(models.Model):
    INCOME = 'IN'
    OUTGOING = 'OUT'
    TYPE_CHOICES = [(INCOME,'Income'),(OUTGOING,'Outgoing')]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    tx_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    quantity = models.IntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.tx_type} {self.product.sku} x{self.quantity} on {self.created_at}'
