from django import forms
from django.contrib.auth.models import User
from .models import Products

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'description', 'price', 'stock', 'image', 'brand', 'type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }