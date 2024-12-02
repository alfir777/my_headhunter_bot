# Бот на python-telegram-bot с Django 3

Бот на python-telegram-bot с Django 3 для упрощения поиска работы с hh.ru  
Поиск выполняется из https://api.hh.ru  
Веб организован только с панелью администратора Django (изменен только пусть с 'admin/' на '/')

## Запуск
1. Клонировать репозиторий или форк
```
git clone https://github.com/alfir777/my_headhunter_bot.git
```
2. Выполнить копирование файла .env_template на .env и выставить свои параметры
```
cd my_headhunter_bot/
cp .env_template .env
```
- SECRET_KEY: хотя бы изменить несколько символов из шаблона
- Если TYPE_DATABASES укажете sqlite3, остальные связанные с БД можно оставить как есть
- TELEGRAM_BOT_TOKEN получить у [@BotFather](https://t.me/BotFather)
- DOMAINNAME не забыть так же указать в ALLOWED_HOSTS
3. В Dockerfile заменить user на Вашего пользователя и его UID/GID

4. Развернуть контейнеры с помощью в docker-compose
```
docker-compose -f docker-compose.yml up -d
```
5. Выполнить миграции/сбор статики
```
 docker exec -it job python3 manage.py makemigrations
 docker exec -it job python3 manage.py migrate
 docker exec -it job python3 manage.py collectstatic
```
6. Создать суперпользователя
```
 docker exec -it job python3 manage.py createsuperuser
```
Возможны проблемы с правами на папки, созданными docker/django
- Изменить права доступа для директорий на 755 (drwxr-xr-x)
```
find /path/to/target/dir -type d -exec chmod 755 {} \;
```
- Изменить права доступа для файлов на 644 (-rw-r--r--)
```
find /path/to/target/dir -type f -exec chmod 644 {} \;
```
- Не всегда выполняются все миграции, принудительно:
```
 docker exec -it web python3 manage.py migrate --run-syncdb
```