import json
import os

import pandas as pd
import requests
from django.core.exceptions import ObjectDoesNotExist
from pandas import json_normalize
from telegram import Update
from telegram.ext import CallbackContext

from core.enums import VacancyStatus
from core.models import Area, Vacancy


def send_message_to_telegram(message: str) -> None:
    """
    Для отправки сообщении из Celery на TELEGRAM_CHAT_ID по заданиям
    :param message:
    :return:
    """
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']

    url = 'https://api.telegram.org/bot' + token + '/sendMessage'
    data = {'chat_id': chat_id, 'text': message, }
    request = requests.post(url, data=data)


def send_message(update: Update, context: CallbackContext, message: str, is_bot=False):
    if is_bot:
        return update.message.reply_text(message)
    else:
        return send_message_to_telegram(message)


def update_vacancy(
        update: Update or None, context: CallbackContext or None, is_bot=False, all_vacancies: bool = False
) -> None:
    """
    Обновление статусов существующих вакансии
    Более подробная информация по ссылке:
    https://github.com/hhru/api/blob/master/docs/vacancies.md
    :return: None
    """

    send_message(update, context, message='Пожалуйста, подождите...', is_bot=is_bot)

    if all_vacancies:
        vacancies = Vacancy.objects.all()
    else:
        vacancies = Vacancy.objects.filter(status__in=[VacancyStatus.new.value, VacancyStatus.archive.value])

    for item in vacancies:
        request = requests.get(f'https://api.hh.ru/vacancies/{item.vacancy_id}', timeout=10)
        if request.status_code == 404:
            if item.status == VacancyStatus.not_found.value:
                continue
            item.status = 'not_found'
            item.save()
            send_message(update, context, is_bot=is_bot, message=f'Вакансия не найдена \n\n {item.alternate_url}')
            continue
        vacancy = request.json()
        try:
            if vacancy["archived"] and item.status == VacancyStatus.new.value:
                if item.watch:
                    send_message(update, context, is_bot=is_bot,
                                 message=f'Вакансия перенесена в архив \n\n {vacancy["alternate_url"]}')
                item.status = VacancyStatus.archive.value
            elif not vacancy["archived"] and item.status == VacancyStatus.archive.value:
                if item.watch:
                    send_message(update, context, is_bot=is_bot,
                                 message=f'Вакансия восстановлена из архива \n\n {vacancy["alternate_url"]}')
                item.status = VacancyStatus.new.value
            elif item.status == VacancyStatus.not_found.value:
                if item.watch:
                    send_message(update, context, is_bot=is_bot,
                                 message=f'Вакансия восстановлена из не найденных \n\n {vacancy["alternate_url"]}')
                item.status = VacancyStatus.new.value
        except KeyError:
            if item.watch:
                send_message(update, context, is_bot=is_bot,
                             message=f'Вакансия недоступна \n\n {item.alternate_url}')
            item.status = VacancyStatus.unavailable.value
        if item.status != VacancyStatus.unavailable.value:
            item.name = vacancy['name']
            item.employer_name = vacancy['employer']['name']
            item.employer_url = vacancy['employer']['url']
            item.description = vacancy['description']
            item.alternate_url = vacancy['alternate_url']
            item.updated_at = vacancy['created_at']
            item.salary = get_salary(salary=vacancy['salary'])
        item.save()
    count_all = Vacancy.objects.all().count()
    count_new = Vacancy.objects.filter(status=VacancyStatus.new.value).count()
    count_archive = Vacancy.objects.filter(status=VacancyStatus.archive.value).count()
    count_unavailable = Vacancy.objects.filter(status=VacancyStatus.unavailable.value).count()
    count_not_found = Vacancy.objects.filter(status=VacancyStatus.not_found.value).count()
    message = 'Вакансии обновлены \n' \
              f' всего вакансии {count_all} \n' \
              f' доступно {count_new} \n' \
              f' в архиве {count_archive} \n' \
              f' не найдено {count_not_found} \n' \
              f' недоступно {count_unavailable} \n'
    send_message(update, context, message=message, is_bot=is_bot)


def get_areas(update: Update, context: CallbackContext, is_bot=False) -> None:
    send_message(update, context, message='Пожалуйста, подождите...', is_bot=is_bot)

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
        parent_id = [0 if item['parent_id'] is None else item['parent_id']]
        try:
            area = Area.objects.get(area_id=item['id'])
            area.parent_id = parent_id
            area.name = item['name']
            area.save()
        except ObjectDoesNotExist:
            area = Area(
                area_id=item['id'],
                parent_id=parent_id[0],
                name=item['name']
            ).save()
    send_message(update, context, message='Области обновлены/добавлены', is_bot=is_bot)


def get_salary(salary) -> str:
    if salary is None:
        return 'Не указан доход'

    salary_from = ['' if salary['from'] is None else salary['from']]
    salary_to = ['' if salary['to'] is None else salary['to']]
    salary_currency = ['' if salary['currency'] is None else salary['currency']]
    salary_gross = ['' if salary['gross'] is None else 'до вычета налогов']

    return f'{salary_from[0]} {salary_to[0]} {salary_currency[0]} {salary_gross[0]}'


def get_description(url):
    request = requests.get(url)
    json_file = request.json()
    return json_file.get('description', '')


def get_vacancies_in_api(update: Update or None,
                         context: CallbackContext or None,
                         area: Area,
                         search_text: str,
                         is_bot=False) -> None:
    params = {
        'text': search_text,  # 'text': f'NAME:{TEXT_SEARCH}'
        'area': area.area_id,
        'page': 0,
        'per_page': 100
    }

    req = requests.get('https://api.hh.ru/vacancies', params)
    data = req.content.decode()
    json_data = json.loads(data)
    req.close()
    send_message(update, context, message='Пожалуйста, подождите...', is_bot=is_bot)
    count = 0

    for page in range(0, json_data['pages'] + 1):
        params = {
            'text': search_text,
            'area': area.area_id,
            'page': page,
            'per_page': 100
        }

        req = requests.get('https://api.hh.ru/vacancies', params)
        data = req.content.decode()
        json_data = json.loads(data)
        req.close()

        for item in json_data['items']:
            salary = get_salary(salary=item['salary'])
            try:
                vacancy = Vacancy.objects.get(vacancy_id=item['id'])
                vacancy.name = item['name']
                vacancy.employer_name = item['employer']['name']
                vacancy.employer_url = item['employer']['url']
                vacancy.description = get_description(item['url'])
                vacancy.alternate_url = item['alternate_url']
                vacancy.updated_at = item['created_at']
                vacancy.salary = salary
                vacancy.save()
            except ObjectDoesNotExist:
                send_message(update, context, is_bot=is_bot, message=f'Вакансия \n\n {item["alternate_url"]}')
                vacancy = Vacancy(
                    vacancy_id=item['id'],
                    area=area,
                    name=item['name'],
                    employer_name=item['employer']['name'],
                    employer_url=item['employer']['url'],
                    alternate_url=item['alternate_url'],
                    description=get_description(item['url']),
                    updated_at=item['created_at'],
                    salary=salary,
                ).save()
                count += 1
    if count > 0:
        message = f'{area} - вакансии собраны/обновлены\n (запрос - "{search_text}")'
    else:
        message = f'{area} - новых вакансии нет..\n (запрос - "{search_text}")'
    send_message(update, context, is_bot=is_bot, message=message)
