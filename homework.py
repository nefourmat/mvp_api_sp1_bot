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
APPROVED = 'Ревьюеру всё понравилось, работа зачтена!'
FIND_ERRORS = 'К сожалению, в работе нашлись ошибки.'
ANSWER = 'Практикум вернул неожиданный ответ: {homework_name}'
STATUS = 'Непредвиденный статус работы: {homework_status}'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}

# проинициализация бота
bot = Bot(os.getenv('TELEGRAM_TOKEN'))


#  взята ли ваша домашка в ревью, провалена или принята
def parse_homework_status(homework):
    name = homework['homework_name']
    if name is None:
        logging.error(ANSWER.format(homework_name=name))
    homework_status = homework['status']
    if homework_status not in ('approved', 'rejected'):
        logging.error(ANSWER.format(homework_status=homework_status))
    if homework_status == 'rejected':
        return CHECK_WORK.format(homework_name=name, verdict=FIND_ERRORS)
    if homework_status == 'approved':
        return CHECK_WORK.format(homework_name=name, verdict=APPROVED)
    return CHECK_WORK.format(homework_name=name)


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    data = {
        'from_date': current_timestamp
    }
    try:
        homework_statuses = requests.get(url=URL, headers=HEADERS, params=data)
        return homework_statuses.json()
    except Exception:
        logging.exception(f'error {Exception}')
        return {}


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())  # Начальное значение timestamp
    send_message('Запущено отслеживание обновлений ревью')

    while True:
        try:
            new_homework = get_homeworks(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]))
            # обновить timestamp
            current_timestamp = new_homework.get('current_date')
            time.sleep(20 * 60)  # Опрашивать раз в 20 минут

        except Exception:
            logger.debug(f'Бот упал с ошибкой: {Exception}')
            time.sleep(20 * 60)


if __name__ == '__main__':
    main()

logging.basicConfig(
    level='DEBUG',
    filename=os.path.expanduser(~__file__ + '.log'),
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger()
logging.getLogger('urllib3').setLevel('CRITICAL')  # исключаем requests
