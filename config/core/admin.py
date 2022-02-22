from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.db.models import Count

from .forms import AreaAdminForm, VacancyAdminForm, ProfileAdminForm, MessageAdminForm
from .models import Vacancy, Area, Profile, Message


class AreaListFilter(SimpleListFilter):
    title = 'Области'
    parameter_name = 'decade'

    def lookups(self, request, model_admin):
        return Area.objects.annotate(one=Count('vacancies')).filter(one__gt=0).values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.all()
        else:
            return queryset.filter(area__id__exact=self.value())


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
    search_fields = ('vacancy_id', 'title')


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('area_id', 'in_search', 'parent_id', 'name',)
    list_editable = ('in_search',)
    search_fields = ('name',)
    form = AreaAdminForm


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'name',)
    search_fields = ('name',)
    form = ProfileAdminForm


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('profile', 'text', 'created_at',)
    search_fields = ('name',)
    form = MessageAdminForm
