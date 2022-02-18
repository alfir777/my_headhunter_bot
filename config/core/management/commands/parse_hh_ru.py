from django.core.management.base import BaseCommand

from core.services import get_vacancies


class Command(BaseCommand):
    help = 'Парсинг hh.ru'

    def handle(self, *args, **options):
        get_vacancies()
