import json
import time

import pandas as pd
import requests
from django.core.handlers.base import logger
from pandas import json_normalize
from telegram import Update
from telegram.ext import CallbackContext

from core.models import Area, Vacancy


def update_status_vacancy(update: Update, context: CallbackContext):
    """
    Обновление статусов существующих вакансии
    Более подробная информация по ссылке:
    https://github.com/hhru/api/blob/master/docs/vacancies.md
    :return: None
    """

    vacancies = Vacancy.objects.all()
    for item in vacancies:
        request = requests.get(f'https://api.hh.ru/vacancies/{item.vacancy_id}')
        json_file = request.json()
        try:
            if json_file["archived"] and item.status == 'new':
                update.message.reply_text(f'Вакансия перенесена в архив \n\n {json_file["alternate_url"]}')
                item.status = 'archive'
                item.save()
            elif not json_file["archived"] and item.status == 'archive':
                update.message.reply_text(f'Вакансия восстановлена из архива \n\n {json_file["alternate_url"]}')
                item.status = 'new'
                item.save()
        except KeyError:
            logger.error(f'Ошибка с https://api.hh.ru/vacancies/{item.vacancy_id}')
    update.message.reply_text('Вакансии обновлены')


def get_areas(update: Update, context: CallbackContext):
    request = requests.get('https://api.hh.ru/areas')
    areas = request.json()
    df = pd.concat([
        json_normalize(areas),
        json_normalize(areas, record_path=['areas'] * 1),
        json_normalize(areas, record_path=['areas'] * 2),
    ])
    df.drop(['areas'], axis=1, inplace=True)
    result = df.to_json(orient="records")
    result_json = json.loads(result)
    for item in result_json:
        if item['parent_id'] is None:
            parent_id = 0
        else:
            parent_id = item['parent_id']
        try:
            area = Area.objects.get(area_id=item['id'])
            area.parent_id = parent_id
            area.name = item['name']
            area.save()
        except Area.DoesNotExist:
            area = Area(
                area_id=item['id'],
                parent_id=parent_id,
                name=item['name']
            ).save()
    update.message.reply_text('Области обновлены/добавлены')


def get_vacancies_in_api(update: Update, context: CallbackContext, area, search_text):
    """
    Создаем метод для получения вакансий по API.
    Аргументы:
        page - Индекс страницы, начинается с 0. Значение по умолчанию 0, т.е. первая страница
    """
    params = {
        # 'text': f'NAME:{TEXT_SEARCH}',
        'text': search_text,
        'area': area,
        'page': 0,
        'per_page': 100
    }

    req = requests.get('https://api.hh.ru/vacancies', params)
    data = req.content.decode()
    json_data = json.loads(data)
    req.close()
    for page in range(0, json_data['pages'] + 1):
        params = {
            'text': search_text,
            'area': area,
            'page': page,
            'per_page': 100
        }

        req = requests.get('https://api.hh.ru/vacancies', params)  # Посылаем запрос к API
        data = req.content.decode()  # Декодируем его ответ, чтобы Кириллица отображалась корректно
        json_data = json.loads(data)
        req.close()

        for item in json_data['items']:
            salary = item['salary']
            if salary is None:
                salary = 'Не указан доход'
            else:
                if item['salary']['from'] is None:
                    salary_from = ''
                else:
                    salary_from = item['salary']['from']
                if item['salary']['to'] is None:
                    salary_to = ''
                else:
                    salary_to = item['salary']['to']
                if item['salary']['currency'] is None:
                    salary_currency = ''
                else:
                    salary_currency = item['salary']['currency']
                if item['salary']['gross'] is None:
                    salary_gross = ''
                else:
                    salary_gross = 'до вычета налогов'
                salary = f'{salary_from} {salary_to} {salary_currency} {salary_gross}'
            try:
                vacancy = Vacancy.objects.get(vacancy_id=item['id'])
                vacancy.title = item['name']
                vacancy.company = item['employer']['name']
                vacancy.url_company = item['employer']['url']
                vacancy.url_vacancy = item['alternate_url']
                vacancy.updated_at = item['created_at']
                vacancy.salary = salary
                vacancy.save()
            except Vacancy.DoesNotExist:
                update.message.reply_text(f'Вакансия \n\n {item["alternate_url"]}')
                vacancy = Vacancy(
                    vacancy_id=item['id'],
                    area=Area.objects.get(area_id=area),
                    title=item['name'],
                    company=item['employer']['name'],
                    url_company=item['employer']['url'],
                    url_vacancy=item['alternate_url'],
                    updated_at=item['created_at'],
                    salary=salary,
                ).save()
        time.sleep(0.25)
    update.message.reply_text(
        f'{Area.objects.get(area_id=area)} - вакансии собраны/обновлены\n (запрос - "{search_text}")'
    )
