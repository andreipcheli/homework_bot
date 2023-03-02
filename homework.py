import os
import logging
import requests
import telegram
import time

from dotenv import load_dotenv


load_dotenv()

class SystemExit(Exception):
    pass

class RequestException(Exception):
    pass


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='main.log',
    filemode='w'
    )



def check_tokens():
    """Check the availability of tokens"""
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID}
    for token in tokens:
        if tokens[token] == None:
            logging.critical(f'{token} does not exist')
            raise SystemExit()


def send_message(bot, message):
    """Send a message with an update to user."""
    try:
        bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
        )
        logging.debug('Message was sent by bot')
    except telegram.error.TelegramError:
        logging.error('Message was not sent!')


def get_api_answer(timestamp):
    """Get a data from https://practicum.yandex.ru/api/user_api/homework_statuses/ and return it in a format competible with python."""
    try:
        response = requests.get(ENDPOINT, headers = HEADERS, params={'from_date': timestamp})
    except Exception as error:
        logging.error(f'Endpoint does not respond: {error}')
    if response.status_code != 200:
        logging.error(f'Endpoint does not respond')
        raise RequestException('Server does not respond')
    return response.json()

    


def check_response(response):
    """Check the data from the response."""
    if not isinstance(response, dict):
        raise TypeError
    elif 'homeworks' not in response:
        raise Exception('Response does not contain "homeworks" key')
    elif not isinstance(response['homeworks'], list):
        raise TypeError
    try:
        homework = response['homeworks'][0]
    except KeyError:
        logging.error('Homework list is empty')
        raise KeyError('Homework list is empty')
    return homework

def parse_status(homework):
    """Generate a message with a homework update."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        raise KeyError('The name of homework does not exist')



def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    # timestamp = 0

    while True:
        try:
            response = get_api_answer(timestamp)
            checked_response = check_response(response)
            message = parse_status(checked_response)
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        
        time.sleep(RETRY_PERIOD)
            



if __name__ == '__main__':
    main()
