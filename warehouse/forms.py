from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku','name','description','quantity']

class ScanForm(forms.Form):
    sku = forms.CharField(max_length=200)
    quantity = forms.IntegerField(min_value=1, initial=1)
    note = forms.CharField(required=False)
