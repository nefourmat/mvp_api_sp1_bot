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
ANSWER = 'Практикум вернул неожиданный ответ: {unknown}'
WRONG = 'Неизвестный статус работы {unknown}'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
VALUES = {
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
    '''
JSON_ERROR_MESSAGE = 'Ошибка {error}'
BOT_ERROR_MESSAGE = 'Бот столкнулся с ошибкой: {found_error}'
# инициализация бота
bot = Bot(os.getenv('TELEGRAM_TOKEN'))
# получаем сообщение после корректного деплоя
bot.send_message(
    chat_id=CHAT_ID, text='Запущено отслеживание обновлений ревью')


def parse_homework_status(homework):
    name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in VALUES:
        raise ValueError(WRONG.format(unknown=name))
    return CHECK_WORK.format(
        homework_name=name, verdict=VALUES[homework_status])


def get_homeworks(current_timestamp):
    data = {
        'url': URL,
        'params': {'from_date': current_timestamp},
        'headers': HEADERS
    }
    try:
        response = requests.get(**data)
    except Exception as error:
        logging.exception(f'error {error}')
        raise ValueError(
            REQUEST_ERROR_MESSAGE.format(exception=error, **data.strip())
        )
    reply = response.json()
    key_words = ['error', 'code']
    for key in key_words:
        if key in reply:
            raise ValueError(
                JSON_ERROR_MESSAGE.format(error=reply[key], **data.strip()))
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
            time.sleep(20 * 60)  # Опрашивать раз в 20 минут

        except Exception as error:
            logger.debug(BOT_ERROR_MESSAGE.format(found_error=error))
            time.sleep(20 * 60)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    logger = logging.getLogger()
    # исключаем requests
    logging.getLogger('urllib3').setLevel('CRITICAL')
    main()
