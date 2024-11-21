from django import forms
from .models import Item, UserRating

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'specification', 'brand', 'description', 'price', 'category', 'image', 'new_price']  # Ensure these match the Item model
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input-title', 'id': 'product-title', 'placeholder': 'Title eg. Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'id': 'product-description', 'placeholder': 'Description eg. Product details', 'rows': '4'}),
            'brand': forms.TextInput(attrs={'class': 'input-title', 'id': 'product-brand', 'placeholder': 'Brand eg. Brand Name'}),
            'specification': forms.Textarea(attrs={'class': 'form-control', 'id': 'product-specification', 'placeholder': 'Specification eg. Product specifications', 'rows': '4'}),
            'price': forms.NumberInput(attrs={'class': 'input-price', 'id': 'product-price', 'placeholder': 'Price Ksh.', 'step': '1'}),
            'new_price': forms.NumberInput(attrs={'class': 'input-price', 'id': 'product-price', 'placeholder': 'Price Ksh.', 'step': '1'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'product-category'}),
            'image': forms.ClearableFileInput(attrs={'class': 'input-image', 'id': 'image-id'}),
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = UserRating
        fields = ['stars', 'comment']
