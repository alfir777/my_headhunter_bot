from django import forms

from .models import Area, Vacancy


class VacancyAdminForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = '__all__'


class AreaAdminForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = (
            'area_id',
            'parent_id',
            'name',
        )
        widgets = {
            'area_id': forms.TextInput,
            'parent_id': forms.TextInput,
            'name': forms.TextInput,
        }
