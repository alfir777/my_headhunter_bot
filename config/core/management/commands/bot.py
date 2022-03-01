import os

from django.core.management.base import BaseCommand
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.utils.request import Request

from core.models import Profile, Message, Area, SearchQuery
from core.services import log_errors, update_status_vacancy, get_vacancies_in_api, send_message_to_telegram, get_areas


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Use /status, /get_vacancies, /add, /get_area or /search to test this bot.")


@log_errors
def status(update: Update, context: CallbackContext):
    update_status_vacancy()


@log_errors
def get_area(update: Update, context: CallbackContext):
    get_areas()


@log_errors
def get_vacancies(update: Update, context: CallbackContext):
    if len(Area.objects.all()) == 0:
        send_message_to_telegram('Выполните команду для заполнения областей:\n/get_area')
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


@log_errors
def add(update: Update, context: CallbackContext) -> None:
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

    try:
        area = Area.objects.filter(name__icontains=" ".join(context.args))
        if len(area) == 0:
            send_message_to_telegram('Не найдено не одного региона')
            return
        elif len(area) > 10:
            send_message_to_telegram('Будет выведено первые 10 результатов')
        keyboard = [[InlineKeyboardButton(f'{item.name}', callback_data=f'{item.name}'), ] for item in area[:10]]
        keyboard.append([InlineKeyboardButton('Отмена', callback_data=f'Отмена')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            'Выберите из возможных:',
            reply_markup=reply_markup
        )

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <text_search>')


@log_errors
def search(update: Update, context: CallbackContext) -> None:
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
    try:
        if not context.args:
            raise ValueError
        SearchQuery(
            search_text=text[7:],
            in_search=True,
        ).save()
        update.message.reply_text(f'Запрос {text[8:]} сохранен')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /search <text_search>')


@log_errors
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    query.answer()
    if query.data == 'Отмена':
        query.edit_message_text(text=f"Выбор отменен")
    else:
        area = Area.objects.get(name=query.data)
        area.in_search = True
        area.save()
        query.edit_message_text(text=f"Выбрана область поиска: {query.data}")


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

        updater.dispatcher.add_handler(CommandHandler('status', status))
        updater.dispatcher.add_handler(CommandHandler('get_vacancies', get_vacancies))
        updater.dispatcher.add_handler(CommandHandler('get_area', get_area))
        updater.dispatcher.add_handler(CommandHandler('start', start))
        updater.dispatcher.add_handler(CommandHandler('add', add))
        updater.dispatcher.add_handler(CallbackQueryHandler(button))
        updater.dispatcher.add_handler(CommandHandler('search', search))

        updater.start_polling()
        updater.idle()
