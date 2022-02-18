import json
import os
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pandas import json_normalize
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import TEXT_SEARCH, AREA
from core.models import Area, Vacancy


def update_status_vacancy():
    # https://github.com/hhru/api/blob/master/docs/vacancies.md
    vacancies = Vacancy.objects.all()
    for item in vacancies:
        request = requests.get(f'https://api.hh.ru/vacancies/{item.vacancy_id}')
        json_file = request.json()
        if json_file["archived"]:
            item.status = 'archive'
            item.save()


def get_areas():
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


def get_vacancies():
    # options
    options = webdriver.ChromeOptions()

    # user-agent
    useragent = UserAgent()
    options.add_argument(f"user-agent={useragent.chrome}")

    # headless mode
    # options.add_argument("--headless")
    options.headless = True

    # disable webdriver mode
    options.add_argument("--disable-blink-features=AutomationControlled")

    # browser = webdriver.Chrome(executable_path=chromedriver, options=options)
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        browser.get(f'https://hh.ru/search/vacancy?area={AREA}&text={TEXT_SEARCH}')

        try:
            pages_count = browser.find_elements_by_xpath("//div[@data-qa='pager-block']")[0].text.split()[-2]
            pages_count = int(pages_count.replace('...', ''))
        except IndexError as exc:
            pages_count = 1
        except Exception as exc:
            print('Не предвиденная ошибка!!! pages_count!!!')

        for page in range(pages_count):
            browser.get(f'https://hh.ru/search/vacancy?area={AREA}&text={TEXT_SEARCH}&page={page}')
            time.sleep(5)

            with open(f"index_selenium_{page}.html", "w", encoding="utf-8") as file:
                file.write(browser.page_source)

            with open(f"index_selenium_{page}.html", encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'html.parser')

            vacancies_items = soup.find('div', class_='vacancy-serp').find_all('div', class_='vacancy-serp-item')

            for item in vacancies_items:
                try:
                    vacancy_id = item.find('a', class_='bloko-link').get('href').split('?')[0].split('/')[-1]
                except AttributeError as exc:
                    vacancy_id = 'Нет ID вакансии'
                except Exception as exc:
                    print('Не предвиденная ошибка!!! vacancy_id!!!')

                try:
                    vacancy_data = item.find(attrs={"data-qa": "vacancy-serp__vacancy-date"}).text.strip()
                except AttributeError as exc:
                    vacancy_data = '01.01.1970'
                except Exception as exc:
                    print('Не предвиденная ошибка!!! vacancy_data!!!')

                vacancy_data = datetime.strptime(vacancy_data, "%d.%m.%Y")

                try:
                    vacancy_title = item.find(attrs={"data-qa": "vacancy-serp__vacancy-title"}).text.strip()
                except AttributeError as exc:
                    vacancy_title = 'Нет названия вакансии'
                except Exception as exc:
                    print('Не предвиденная ошибка!!! vacancy_title!!!')

                try:
                    vacancy_company = item.find(attrs={"data-qa": "vacancy-serp__vacancy-employer"}).text.strip()
                except AttributeError as exc:
                    vacancy_company = 'Нет названия компании'
                except Exception as exc:
                    print('Не предвиденная ошибка!!! vacancy_company!!!')

                try:
                    vacancy_company_href = item.find(
                        'a', class_='bloko-link bloko-link_kind-tertiary'
                    ).get('href').split('?')[0]
                    vacancy_company_href = 'https://hh.ru/' + vacancy_company_href
                except AttributeError as exc:
                    vacancy_company_href = 'Нет ссылки на компанию'
                except Exception as exc:
                    print('Не предвиденная ошибка!!! vacancy_company_href!!!')

                try:
                    vacancy_href = item.find('a', class_='bloko-link').get('href').split('?')[0]
                except AttributeError as exc:
                    vacancy_href = 'Нет ссылки на вакансию'
                except Exception as exc:
                    print('Не предвиденная ошибка!!! vacancy_href!!!')

                try:
                    vacancy_salary = item.find(attrs={"data-qa": "vacancy-serp__vacancy-compensation"}).text.strip()
                except AttributeError as exc:
                    vacancy_salary = 'Не указан доход'
                except Exception as exc:
                    print('Не предвиденная ошибка!!! vacancy_salary!!!')

                try:
                    vacancy = Vacancy.objects.get(vacancy_id=vacancy_id)
                    vacancy.title = vacancy_title
                    vacancy.company = vacancy_company
                    vacancy.url_company = vacancy_company_href
                    vacancy.url_vacancy = vacancy_href
                    vacancy.updated_at = vacancy_data
                    vacancy.salary = vacancy_salary
                    vacancy.save()
                except Vacancy.DoesNotExist:
                    vacancy = Vacancy(
                        vacancy_id=vacancy_id,
                        area=Area.objects.get(area_id=AREA),
                        title=vacancy_title,
                        company=vacancy_company,
                        url_company=vacancy_company_href,
                        url_vacancy=vacancy_href,
                        updated_at=vacancy_data,
                        salary=vacancy_salary,
                    ).save()
                except Exception as exc:
                    print('Не предвиденная ошибка!!! Vacancy.objects!!!')

            print(f'Обработано {page + 1}/{pages_count}')
            os.remove(f"index_selenium_{page}.html")
    except Exception as exc:
        print(exc)
        print('Не предвиденная ошибка!!! browser')
    finally:
        browser.close()
        browser.quit()
