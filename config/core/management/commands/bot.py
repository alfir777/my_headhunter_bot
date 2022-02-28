import os

from django.core.management.base import BaseCommand
from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from telegram.utils.request import Request

from core.models import Profile, Message, Area, SearchQuery
from core.services import log_errors, update_status_vacancy, get_vacancies_in_api, send_message_to_telegram


@log_errors
def do_echo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    profile, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': update.message.from_user.username,
        }
    )
    Message(
        profile=profile,
        text=text,
    ).save()

    reply_text = f'Ваш ID = {chat_id}\n\n {text}'
    update.message.reply_text(
        text=reply_text,
    )


@log_errors
def do_count(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    profile, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': update.message.from_user.username,
        }
    )
    count = Message.objects.filter(profile=profile).count()

    update.message.reply_text(
        text=f'У Вас {count} сообщений',
    )


@log_errors
def do_status_vacancy(update: Update, context: CallbackContext):
    update_status_vacancy()


@log_errors
def do_get_vacancies_in_api(update: Update, context: CallbackContext):
    area = Area.objects.filter(in_search=True)
    search_text = SearchQuery.objects.filter(in_search=True)
    if len(area) == 0:
        send_message_to_telegram('Не выбрано не одного региона')
    elif len(search_text) == 0:
        send_message_to_telegram('Нет ни одного текстового запроса')
    else:
        for item in area:
            for text in search_text:
                get_vacancies_in_api(area=item.area_id, search_text=text)


class Command(BaseCommand):
    help = 'Telegram-bot'

    def handle(self, *args, **options):
        request = Request(
            connect_timeout=0.5,
            read_timeout=1.0,
        )
        bot = Bot(
            request=request,
            token=os.environ['TELEGRAM_BOT_TOKEN'],
        )

        updater = Updater(
            bot=bot,
            use_context=True
        )

        message_handler_count = CommandHandler('count', do_count)
        updater.dispatcher.add_handler(message_handler_count)

        message_handler_status = CommandHandler('status', do_status_vacancy)
        updater.dispatcher.add_handler(message_handler_status)

        message_handler_get_api_vacancies = CommandHandler('get_vacancies_in_api', do_get_vacancies_in_api)
        updater.dispatcher.add_handler(message_handler_get_api_vacancies)

        message_handler = MessageHandler(Filters.text, do_echo)
        updater.dispatcher.add_handler(message_handler)

        updater.start_polling()
        updater.idle()
