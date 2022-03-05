from celery import shared_task

from core.models import Area, SearchQuery
from core.services import get_vacancies_in_api, update_status_vacancy


@shared_task
def get_vacancies():
    area = Area.objects.filter(in_search=True)
    search_text = SearchQuery.objects.filter(in_search=True)
    for i in area:
        for text in search_text:
            get_vacancies_in_api(update=None, context=None, area=i, search_text=text, is_bot=False)


@shared_task
def update_status_vacancies():
    update_status_vacancy(update=None, context=None, is_bot=False)
