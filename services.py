import json
import os

import requests
import pandas as pd
from pandas import json_normalize


def create_folder(folder='tmp'):
    if not os.path.isdir(folder):
        os.mkdir(folder)


def get_areas():
    r = requests.get('https://api.hh.ru/areas')
    areas = r.json()
    df = pd.concat([
        json_normalize(areas),
        json_normalize(areas, record_path=['areas'] * 1),
        json_normalize(areas, record_path=['areas'] * 2)
    ])
    df.drop(['areas'], axis=1, inplace=True)
    result = df.to_json(orient="records")
    parsed = json.loads(result)
    create_folder(folder='json')
    with open(f'json/areas_records.json', 'w+', encoding='utf-8') as file:
        json.dump(parsed, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    get_areas()
