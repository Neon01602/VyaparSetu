from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, VendorDocument


class InvestorSignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'phone',
            'aadhaar_pan', 'password1', 'password2'
        ]


class VendorSignupForm(UserCreationForm):
    doc_title = forms.CharField()
    document = forms.FileField()

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'phone',
            'aadhaar_pan', 'password1', 'password2'
        ]
