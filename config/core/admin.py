from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter

from .forms import AreaAdminForm, VacancyAdminForm
from .models import Vacancy, Area


class AreaListFilter(SimpleListFilter):
    title = 'Области'
    parameter_name = 'decade'

    def lookups(self, request, model_admin):
        return (
            ('Уфа', 'Уфа'),
            ('Екатеринбург', 'Екатеринбург'),
        )

    def queryset(self, request, queryset):
        # TODO Найти более правильное решение..
        if self.value() == 'Уфа':
            return Vacancy.objects.filter(area=Area.objects.get(area_id=99))
        if self.value() == 'Екатеринбург':
            return Vacancy.objects.filter(area=Area.objects.get(area_id=3))


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    form = VacancyAdminForm
    list_display = (
        'vacancy_id', 'area', 'status', 'title', 'company', 'url_vacancy', 'created_at', 'updated_at', 'salary'
    )
    list_filter = (
        'status', AreaListFilter, 'company'
    )
    list_editable = ('status',)
    ordering = ('created_at',)
    search_fields = ('vacancy_id', )


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('area_id', 'parent_id', 'name',)
    search_fields = ('name',)
    form = AreaAdminForm
