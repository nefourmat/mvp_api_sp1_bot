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

# проинициализация бота
bot = Bot(os.getenv('TELEGRAM_TOKEN'))


#  взята ли ваша домашка в ревью, провалена или принята
def parse_homework_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status == 'rejected':
        return FIND_ERRORS
    if homework_status == 'approved':
        verdict = APPROVED
    return CHECK_WORK.format(homework_name=homework_name, verdict=verdict)


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    data = {
        'from_date': current_timestamp
    }
    homework_statuses = requests.get(url=URL, headers=headers, params=data)
    return homework_statuses.json()


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
            current_timestamp = new_homework.get('current_date')
            time.sleep(20 * 60)  # Опрашивать раз в пять минут

        except Exception:
            logger.debug(f'Бот упал с ошибкой: {Exception}')
            time.sleep(20 * 60)


logging.basicConfig(
    level='DEBUG',
    filename=__file__ + '.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger()

if __name__ == '__main__':
    #main()
    send_message('Запущено отслеживание обновлений ревью')
