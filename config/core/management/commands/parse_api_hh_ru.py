from django.core.management.base import BaseCommand

from core.services import get_vacancies_in_api


class Command(BaseCommand):
    help = 'Парсинг api.hh.ru'

    def handle(self, *args, **options):
        get_vacancies_in_api()
