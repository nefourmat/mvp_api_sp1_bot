import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
CHECK_WORK = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
GOT_WORK = 'Работа {homework_name} взята в ревью'
APPROVED = 'Ревьюеру всё понравилось, работа зачтена!'
FIND_ERRORS = 'К сожалению, в работе нашлись ошибки.'
WRONG = 'Неизвестный статус работы {unknown}'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
VERDICTS = {
    'approved': APPROVED,
    'rejected': FIND_ERRORS,
    'reviewing': GOT_WORK
}
REQUEST_ERROR_MESSAGE = '''
    Получить ответ от Практикума не удалось.
    {url}
    Заголовок запроса: {headers}
    Параметры запроса: {params}
    {exception}
    '''.strip()
JSON_ERROR_MESSAGE = '''
    Ошибка сервера {error}
    {url}
    Заголовок запроса: {headers}
    Параметры запроса: {params}
    '''.strip()
BOT_ERROR_MESSAGE = 'Бот столкнулся с ошибкой: {error}'
# инициализация бота
bot = Bot(os.getenv('TELEGRAM_TOKEN'))
# получаем сообщение после корректного деплоя


class ServerErrorException(Exception):
    pass


def parse_homework_status(homework):
    name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in VERDICTS:
        raise ValueError(WRONG.format(unknown=homework_status))
    return CHECK_WORK.format(
        homework_name=name, verdict=VERDICTS[homework_status])


def get_homeworks(current_timestamp):
    request_data = {
        'url': URL,
        'params': {'from_date': current_timestamp},
        'headers': HEADERS
    }
    try:
        response = requests.get(**request_data)
    except requests.RequestException as error:
        raise ConnectionError(
            REQUEST_ERROR_MESSAGE.format(
                exception=error, **request_data)
        )
    reply = response.json()
    key_words = ['error', 'code']
    for key in key_words:
        if key in reply:
            raise ServerErrorException(
                JSON_ERROR_MESSAGE.format(
                    error=reply[key], **request_data))
    return reply


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())  # Начальное значение timestamp
    while True:
        try:
            new_homework = get_homeworks(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]))
            # обновить timestamp
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(1 * 60)  # Опрашивать раз в 1 минуту
        except Exception as error:
            logging.debug(BOT_ERROR_MESSAGE.format(error=error), exc_info=True)
            time.sleep(1 * 60)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    # исключаем requests
    logging.getLogger('urllib3').setLevel('CRITICAL')
    main()
