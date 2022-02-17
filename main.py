import csv
import datetime
import json
import os
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# patch to chromedriver
# chromedriver = r"C:\patch\to\file\chromedriver.exe"

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

text_search = 'Python'
area = '99'
vacancies = {}

try:
    current_time = datetime.datetime.now().strftime('%Y%m%d')

    with open(f'hh.ru_{text_search}_{area}_{current_time}.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(
            (
                'ID вакансии',
                'Статус',
                'Дата размещения',
                'Название вакансии',
                'Компания',
                'Ссылка на компанию',
                'Ссылка на вакансию',
                'Зарплата'
            )
        )

    browser.get(f'https://hh.ru/search/vacancy?area={area}&text={text_search}')

    try:
        pages_count = int(browser.find_elements_by_xpath("//div[@data-qa='pager-block']")[0].text.split()[-2])
    except IndexError as exc:
        pages_count = 1

    for page in range(pages_count):
        browser.get(f'https://hh.ru/search/vacancy?area={area}&text={text_search}&page={page}')
        time.sleep(5)

        with open(f"index_selenium_{page}.html", "w", encoding="utf-8") as file:
            file.write(browser.page_source)

        with open(f"index_selenium_{page}.html", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'html.parser')

        vacancies_items = soup.find('div', class_='vacancy-serp').find_all('div', class_='vacancy-serp-item')

        for vacancy in vacancies_items:
            try:
                vacancy_id = vacancy.find('a', class_='bloko-link').get('href').split('?')[0].split('/')[-1]
            except AttributeError as exc:
                vacancy_id = 'Нет ID вакансии'

            try:
                vacancy_data = vacancy.find(attrs={"data-qa": "vacancy-serp__vacancy-date"}).text.strip()
            except AttributeError as exc:
                vacancy_data = 'Нет даты размещения'

            try:
                vacancy_header = vacancy.find(attrs={"data-qa": "vacancy-serp__vacancy-title"}).text.strip()
            except AttributeError as exc:
                vacancy_header = 'Нет названия вакансии'

            try:
                vacancy_company = vacancy.find(attrs={"data-qa": "vacancy-serp__vacancy-employer"}).text.strip()
            except AttributeError as exc:
                vacancy_company = 'Нет названия компании'

            try:
                vacancy_company_href = vacancy.find(
                    'a', class_='bloko-link bloko-link_kind-tertiary'
                ).get('href').split('?')[0]
                vacancy_company_href = 'https://hh.ru/' + vacancy_company_href
            except AttributeError as exc:
                vacancy_company_href = 'Нет ссылки на компанию'

            try:
                vacancy_href = vacancy.find('a', class_='bloko-link').get('href').split('?')[0]
            except AttributeError as exc:
                vacancy_href = 'Нет ссылки на вакансию'

            try:
                vacancy_salary = vacancy.find(attrs={"data-qa": "vacancy-serp__vacancy-compensation"}).text.strip()
            except AttributeError as exc:
                vacancy_salary = 'Не указан доход'

            vacancies[f'{vacancy_id}'] = {
                'Статус': 'активно',
                'Дата размещения': vacancy_data,
                'vacancy_header': vacancy_header,
                'vacancy_company': vacancy_company,
                'vacancy_company_href': vacancy_company_href,
                'vacancy_href': vacancy_href,
                'vacancy_salary': vacancy_salary
            }

            with open(f'hh.ru_{text_search}_{area}_{current_time}.csv', 'a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(
                    (
                        vacancy_id,
                        'активно',
                        vacancy_data,
                        vacancy_header,
                        vacancy_company,
                        vacancy_company_href,
                        vacancy_href,
                        vacancy_salary
                    )
                )
        print(f'Обработано {page + 1}/{pages_count}')
        os.remove(f"index_selenium_{page}.html")

    with open(f'hh.ru_{text_search}_{area}_{current_time}.json', 'w+', encoding='utf-8') as file:
        json.dump(vacancies, file, indent=4, ensure_ascii=False)

except Exception as exc:
    print(exc)
finally:
    browser.close()
    browser.quit()
