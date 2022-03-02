from celery import shared_task
from telegram import Update
from telegram.ext import CallbackContext

from core.models import Area, SearchQuery
from core.services import get_vacancies_in_api


@shared_task
def get_vacancies(update: Update, context: CallbackContext):
    area = Area.objects.filter(in_search=True)
    search_text = SearchQuery.objects.filter(in_search=True)
    for item in area:
        for text in search_text:
            get_vacancies_in_api(update, context, area=item.area_id, search_text=text)
