from django.contrib import admin

from .forms import AreaAdminForm, VacancyAdminForm
from .models import Vacancy, Area


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = (
        'vacancy_id', 'status', 'title', 'company', 'url_vacancy', 'status', 'created_at', 'updated_at', 'salary'
    )
    list_filter = (
        'status', 'company'
    )
    ordering = ('created_at',)

    form = VacancyAdminForm


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('area_id', 'parent_id', 'name',)
    form = AreaAdminForm
