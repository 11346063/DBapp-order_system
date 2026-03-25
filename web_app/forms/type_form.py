from django import forms
from ..models.type import Type

class TypeForm(forms.ModelForm):
    class Meta:
        model = Type
        fields = ["type_name"]