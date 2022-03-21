import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

from exceptions import TelegramNotResponse

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 1740
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format=('%(asctime)s - %(name)s - %(levelname)s - '
            '%(lineno)s - %(funcName)s - %(message)s')
)
handler = logging.StreamHandler()
logger.addHandler(handler)


def send_message(bot, message):
    """Бот отправляет сообщение."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except TelegramNotResponse:
        logger.error('С серверами телеграм что-то не так.')
    logger.info(f'Отправка сообщения: {message}')


def get_api_answer(current_timestamp):
    """Запрос данных к API."""
    timestamp = current_timestamp or int(time.time())
    if not isinstance(timestamp, int):
        raise Exception('Неверный тип времени.')
    params = {'from_date': timestamp}
    try:
        response_hw_status = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
        logger.info('Сервер работает.')
        if response_hw_status.status_code == HTTPStatus.OK:
            logger.info('Ответ получен.')
            response = response_hw_status.json()
            return response
        raise Exception('Ошибка состояния статуса HTTP.')
    except RequestException as error:
        logger.error('Ошибка ответа сервера.')
        raise error


def check_response(response):
    """Проверка ответа API на корректность."""
    try:
        homeworks = response['homeworks']
        if not isinstance(homeworks, list):
            assert False
    except KeyError:
        raise KeyError('В ответе отсутствует ключ "homeworks".')
    except TypeError:
        raise TypeError('Недопустимый тип данных.')
    return homeworks


def parse_status(homework: dict) -> str:
    """Функция возвращает статус домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except homework_status not in HOMEWORK_STATUSES:
        logger.error('Неизвестный статус д.з.')
        raise KeyError(f'Неизвестный статус: {homework_status}')
    except homework_status not in homework:
        logger.error('Отсутствует статус д.з.')
        raise KeyError(f'Отсутствует статус: {homework_status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных TOKENS."""
    logger.info(all)
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens:
        logger.critical('Отсутствуют обязательные переменные окружения.')
        return SystemExit

    def __init__(self, bot):
        self.bot = bot

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1635750000
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            logger.info('Домашняя работа.')
            if isinstance(homework, list) and homework:
                status = parse_status(homework[0])
                send_message(bot, status)
            else:
                logger.info('Нет домашней работы.')
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Остановка программы.')
        raise SystemExit
