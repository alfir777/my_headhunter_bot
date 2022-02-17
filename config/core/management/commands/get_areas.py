from django.core.management.base import BaseCommand

from core.services import get_areas


class Command(BaseCommand):
    help = 'Получение/обновление areas hh.ru'

    def handle(self, *args, **options):
        get_areas()
