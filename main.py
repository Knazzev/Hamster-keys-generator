import asyncio
import os
import random
import time
import uuid
import aiohttp
import sys
import logging
from aiohttp import ClientSession

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | Line %(lineno)d - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

games = {
    1: {'title': 'Riding Extreme 3D', 'token': 'd28721be-fd2d-4b45-869e-9f253b554e50', 'promo_id': '43e35910-c168-4634-ad4f-52fd764a843f'},
    2: {'title': 'Chain Cube 2048', 'token': 'd1690a07-3780-4068-810f-9b5bbf2931b2', 'promo_id': 'b4170868-cef0-424f-8eb9-be0622e8e8e3'},
    3: {'title': 'Train Miner', 'token': '82647f43-3f87-402d-88dd-09a90025313f', 'promo_id': 'c4480ac7-e178-4973-8061-9ed5b2e17954'},
    4: {'title': 'Merge Away', 'token' : '8d1cc2ad-e097-4b86-90ef-7a27e19fb833', 'promo_id': 'dc128d28-c45b-411c-98ff-ac7726fbaea4'},
    5: {'title': 'Twerk Race 3D', 'token': '61308365-9d16-4040-8bb0-2f4a4c69074c',  'promo_id': '61308365-9d16-4040-8bb0-2f4a4c69074c'},
    6: {'title': 'Polysphere', 'token': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71', 'promo_id': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71'}, 
    7: {'title': 'Mow and Trim', 'token': 'ef319a80-949a-492e-8ee0-424fb5fc20a6', 'promo_id': 'ef319a80-949a-492e-8ee0-424fb5fc20a6'},
    8: {'title': 'Mud Racing', 'token': '8814a785-97fb-4177-9193-ca4180ff9da8', 'promo_id': '8814a785-97fb-4177-9193-ca4180ff9da8'},
    9: {'title': 'Cafe Dash', 'token': 'bc0971b8-04df-4e72-8a3e-ec4dc663cd11', 'promo_id': 'bc0971b8-04df-4e72-8a3e-ec4dc663cd11'}
}

INTERVAL = 20

def choose_language():
    print("1: Русский\n2: English")
    choice = input("Введите номер для выбора языка: ").strip()
    if choice == '1':
        return 'RU'
    elif choice == '2':
        return 'EN'
    else:
        print("Некорректный выбор, используется русский язык по умолчанию.")
        return 'RU'

language = choose_language()

async def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_part = ''.join(str(random.randint(0, 9)) for _ in range(19))
    return f"{timestamp}-{random_part}"

async def authenticate(session, client_id, app_token, retries=5):
    url = 'https://api.gamepromo.io/promo/login-client'
    payload = {'appToken': app_token, 'clientId': client_id, 'clientOrigin': 'deviceid'}

    for attempt in range(1, retries + 1):
        try:
            msg = f"Attempt {attempt}/{retries} to authenticate for {client_id}" if language == 'EN' else f"Попытка {attempt}/{retries} аутентификации для {client_id}"
            logger.info(msg)
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                msg = f"Authentication successful for {client_id}" if language == 'EN' else f"Аутентификация успешна для {client_id}"
                logger.info(msg)
                return data['clientToken']
        except aiohttp.ClientResponseError as e:
            msg = f"Authentication failed on attempt {attempt}: {await e.response.json()}" if language == 'EN' else f"Аутентификация не удалась на попытке {attempt}: {await e.response.json()}"
            logger.error(msg)
        except Exception as e:
            msg = f"Unexpected error on attempt {attempt}: {str(e)}" if language == 'EN' else f"Неожиданная ошибка на попытке {attempt}: {str(e)}"
            logger.error(msg)
        await asyncio.sleep(2)
    msg = f"Failed to authenticate {client_id} after {retries} attempts" if language == 'EN' else f"Не удалось аутентифицировать {client_id} после {retries} попыток"
    logger.error(msg)
    return None

async def record_event(session, client_token, promo_id):
    url = 'https://api.gamepromo.io/promo/register-event'
    payload = {'promoId': promo_id, 'eventId': str(uuid.uuid4()), 'eventOrigin': 'undefined'}
    headers = {'Authorization': f'Bearer {client_token}'}

    try:
        async with session.post(url, headers=headers, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('hasCode', False)
    except aiohttp.ClientResponseError as e:
        msg = f"Error recording event: {await e.response.json()}" if language == 'EN' else f"Ошибка при регистрации события: {await e.response.json()}"
        logger.warning(msg)
        return False

async def get_promo_code(session, client_token, promo_id):
    url = 'https://api.gamepromo.io/promo/create-code'
    payload = {'promoId': promo_id}
    headers = {'Authorization': f'Bearer {client_token}'}

    try:
        async with session.post(url, headers=headers, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('promoCode')
    except aiohttp.ClientResponseError as e:
        msg = f"Failed to generate promo code: {await e.response.json()}" if language == 'EN' else f"Не удалось создать промокод: {await e.response.json()}"
        logger.error(msg)
        return None

async def key_generation(app_token, promo_id):
    client_id = await generate_client_id()
    msg = f"Generated client ID: {client_id}" if language == 'EN' else f"Сгенерирован ID клиента: {client_id}"
    logger.info(msg)

    async with ClientSession() as session:
        client_token = await authenticate(session, client_id, app_token)
        if not client_token:
            return None

        for i in range(1, 12):
            msg = f"Event {i}/11 for {client_id}" if language == 'EN' else f"Событие {i}/11 для {client_id}"
            logger.info(msg)
            await asyncio.sleep(INTERVAL * (random.random() / 3 + 1))
            if await record_event(session, client_token, promo_id):
                break

        return await get_promo_code(session, client_token, promo_id)

async def loading_animation():
    symbols = ["|", "/", "-", "\\"]
    idx = 0
    while True:
        msg = f"Loading... {symbols[idx]}" if language == 'EN' else f"Загрузка... {symbols[idx]}"
        sys.stdout.write(f"\r{msg}")
        sys.stdout.flush()
        idx = (idx + 1) % len(symbols)
        await asyncio.sleep(0.1)

async def run_key_generation(selected_game, num_keys):
    game = games[selected_game]
    msg = f"Starting key generation for {game['title']}" if language == 'EN' else f"Запуск генерации ключей для {game['title']}"
    logger.info(msg)

    loading_task = asyncio.create_task(loading_animation())
    tasks = [key_generation(game['token'], game['promo_id']) for _ in range(num_keys)]
    keys = await asyncio.gather(*tasks)
    loading_task.cancel()
    sys.stdout.write("\r")

    valid_keys = [key for key in keys if key]
    if valid_keys:
        msg = f"Keys generated for {game['title']}:" if language == 'EN' else f"Сгенерированные ключи для {game['title']}:"
        logger.info(msg)
        for i, key in enumerate(valid_keys, 1):
            print(f"{i}. {key}")
        save_keys(valid_keys, game['title'])
    else:
        msg = "No keys were generated." if language == 'EN' else "Ключи не были сгенерированы."
        logger.error(msg)

def save_keys(keys, game_title):
    file_name = f"{game_title.replace(' ', '_').lower()}_keys.txt"
    with open(file_name, 'a') as file:
        for key in keys:
            file.write(f"{key}\n")
    msg = f"Keys saved to file {file_name}" if language == 'EN' else f"Ключи сохранены в файл {file_name}"
    logger.info(msg)

def main():
    print("Select a game:" if language == 'EN' else "Выберите игру:")
    for k, v in games.items():
        print(f"{k}: {v['title']}")
    selected_game = int(input("Enter the game number: " if language == 'EN' else "Введите номер игры: "))
    num_keys = int(input("Enter the number of keys to generate: " if language == 'EN' else "Введите количество ключей для генерации: "))

    msg = f"Starting generation of {num_keys} key(s) for {games[selected_game]['title']}" if language == 'EN' else f"Запуск генерации {num_keys} ключей для {games[selected_game]['title']}"
    logger.info(msg)
    asyncio.run(run_key_generation(selected_game, num_keys))
    input("Press Enter to exit." if language == 'EN' else "Нажмите Enter, чтобы выйти.")

if __name__ == "__main__":
    main()
