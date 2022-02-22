from django import forms

from .models import Area, Vacancy, Profile, Message


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


class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'


class MessageAdminForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = '__all__'
