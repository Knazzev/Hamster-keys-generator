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
    1: {'title': 'Chain Cube 2048', 'token': 'd1690a07-3780-4068-810f-9b5bbf2931b2', 'promo_id': 'b4170868-cef0-424f-8eb9-be0622e8e8e3', 'interval': 25, 'max_attempts': 20},
    2: {'title': 'Train Miner', 'token': '82647f43-3f87-402d-88dd-09a90025313f', 'promo_id': 'c4480ac7-e178-4973-8061-9ed5b2e17954', 'interval': 20, 'max_attempts': 15},
    3: {'title': 'Merge Away', 'token': '8d1cc2ad-e097-4b86-90ef-7a27e19fb833', 'promo_id': 'dc128d28-c45b-411c-98ff-ac7726fbaea4', 'interval': 20, 'max_attempts': 25},
    4: {'title': 'Twerk Race 3D', 'token': '61308365-9d16-4040-8bb0-2f4a4c69074c',  'promo_id': '61308365-9d16-4040-8bb0-2f4a4c69074c', 'interval': 20, 'max_attempts': 20},
    5: {'title': 'Polysphere', 'token': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71', 'promo_id': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71', 'interval': 20, 'max_attempts': 20}, 
    6: {'title': 'Mow and Trim', 'token': 'ef319a80-949a-492e-8ee0-424fb5fc20a6', 'promo_id': 'ef319a80-949a-492e-8ee0-424fb5fc20a6', 'interval': 20, 'max_attempts': 20},
    7: {'title': 'Zoopolis', 'token': 'b2436c89-e0aa-4aed-8046-9b0515e1c46b', 'promo_id': 'b2436c89-e0aa-4aed-8046-9b0515e1c46b', 'interval': 20, 'max_attempts': 20},
    8: {'title': 'Fluff Crusade', 'token': '112887b0-a8af-4eb2-ac63-d82df78283d9', 'promo_id': '112887b0-a8af-4eb2-ac63-d82df78283d9', 'interval': 30, 'max_attempts': 20},
    9: {'title': 'Tile Trio', 'token': 'e68b39d2-4880-4a31-b3aa-0393e7df10c7', 'promo_id': 'e68b39d2-4880-4a31-b3aa-0393e7df10c7', 'interval': 20, 'max_attempts': 20},
    10: {'title': 'Stone Age', 'token': '04ebd6de-69b7-43d1-9c4b-04a6ca3305af', 'promo_id': '04ebd6de-69b7-43d1-9c4b-04a6ca3305af', 'interval': 20, 'max_attempts': 20},
    11: {'title': 'Bouncemasters', 'token': 'bc72d3b9-8e91-4884-9c33-f72482f0db37', 'promo_id': 'bc72d3b9-8e91-4884-9c33-f72482f0db37', 'interval': 20, 'max_attempts': 20},
    12: {'title': 'Hide Ball', 'token': '4bf4966c-4d22-439b-8ff2-dc5ebca1a600', 'promo_id': '4bf4966c-4d22-439b-8ff2-dc5ebca1a600', 'interval': 40, 'max_attempts': 20}
}

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
            msg = f"Authentication failed on attempt {attempt}: {e.message}" if language == 'EN' else f"Аутентификация не удалась на попытке {attempt}: {e.message}"
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
        error_msg = "Unknown error"
        if e.status == 400:
            try:
                error_data = await e.response.json()
                error_msg = error_data.get('error', 'Bad Request')
            except Exception:
                error_msg = 'Bad Request'
        msg = f"Error recording event: {error_msg}" if language == 'EN' else f"Ошибка при регистрации события: {error_msg}"
        logger.warning(msg)
        return False
    except Exception as e:
        msg = f"Unexpected error while recording event: {str(e)}" if language == 'EN' else f"Неожиданная ошибка при регистрации события: {str(e)}"
        logger.error(msg)
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

async def key_generation(app_token, promo_id, interval, max_attempts):
    client_id = await generate_client_id()
    msg = f"Generated client ID: {client_id}" if language == 'EN' else f"Сгенерирован ID клиента: {client_id}"
    logger.info(msg)

    async with ClientSession() as session:
        client_token = await authenticate(session, client_id, app_token)
        if not client_token:
            return None

        for i in range(1, max_attempts + 1):
            msg = f"Event {i}/{max_attempts} for {client_id}" if language == 'EN' else f"Событие {i}/{max_attempts} для {client_id}"
            logger.info(msg)
            await asyncio.sleep(interval * (random.random() / 3 + 1))
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
    app_token = game['token']
    promo_id = game['promo_id']
    interval = game['interval']
    max_attempts = game['max_attempts']

    loading_task = asyncio.create_task(loading_animation())
    tasks = [key_generation(app_token, promo_id, interval, max_attempts) for _ in range(num_keys)]
    results = await asyncio.gather(*tasks)
    loading_task.cancel()
    sys.stdout.write("\r")

    valid_keys = [key for key in results if key]

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

async def main():
    print("Select a game:" if language == 'EN' else "Выберите игру:")
    for k, v in games.items():
        print(f"{k}: {v['title']}")
    selected_game = int(input("Enter the game number: " if language == 'EN' else "Введите номер игры: "))

    if selected_game == 12:
        msg = ("Key generation for Hide Ball takes longer than for other games ~8 minutes."
               if language == 'EN'
               else "Генерация ключей для Hide Ball занимает больше времени, чем на другие игры ~8 мин.")
        print(msg)

    num_keys = int(input("Enter the number of keys to generate: " if language == 'EN' else "Введите количество ключей для генерации: "))

    msg = f"Starting generation of {num_keys} key(s) for {games[selected_game]['title']}" if language == 'EN' else f"Запуск генерации {num_keys} ключей для {games[selected_game]['title']}"
    logger.info(msg)

    await run_key_generation(selected_game, num_keys)
    input("Press Enter to exit." if language == 'EN' else "Нажмите Enter, чтобы выйти.")

if __name__ == "__main__":
    asyncio.run(main())
