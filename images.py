import asyncio
import aiohttp
import aiofiles
import os
import json
import config
import time

TIMEOUT = aiohttp.ClientTimeout(total=10)
MAX_RETRIES = 3
CONCURRENT_REQUESTS = 10

def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

async def save_image(session, url, file_path, semaphore, retries=0):
    async with semaphore:
        try:
            async with session.get(url, timeout=TIMEOUT) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(await response.read())
                elif response.status == 404:
                    print(f"Image not found {url}, status code: {response.status}")
                else:
                    print(f"Failed to download {url}, status code: {response.status}")
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            if retries < MAX_RETRIES:
                print(f"Retrying download {url}... ({retries+1}/{MAX_RETRIES})")
                await asyncio.sleep(2)
                await save_image(session, url, file_path, semaphore, retries + 1)
            else:
                print(f"Failed to download {url} after {MAX_RETRIES} retries: {str(e)}")

async def get_pokemon_sprites(session, pokemon_slug, pokemon_id, base_folder, semaphore):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/"
    try:
        async with session.get(url, timeout=TIMEOUT) as response:
            if response.status == 200:
                pokemon_data = await response.json()
                sprites = pokemon_data.get("sprites", {})

                image_urls = {
                    "back_default": sprites.get("back_default"),
                    "back_shiny": sprites.get("back_shiny"),
                    "front_default": sprites.get("front_default"),
                    "front_shiny": sprites.get("front_shiny")
                }

                for image_type in image_urls.keys():
                    folder_path = os.path.join(base_folder, image_type)
                    ensure_folder_exists(folder_path)

                tasks = []
                for image_type, image_url in image_urls.items():
                    if image_url:
                        file_path = os.path.join(base_folder, image_type, f"{pokemon_slug}.png")
                        tasks.append(save_image(session, image_url, file_path, semaphore))

                await asyncio.gather(*tasks)
            else:
                print(f"Failed to fetch data for {pokemon_slug}, status code: {response.status}")
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Error while fetching data for {pokemon_slug}: {str(e)}")

async def get_form_sprites(session, form_id, base_folder, semaphore):
    url = f"https://pokeapi.co/api/v2/pokemon/{form_id}/"
    try:
        async with session.get(url, timeout=TIMEOUT) as response:
            if response.status == 200:
                form_data = await response.json()
                form_name = form_data.get("name")
                sprites = form_data.get("sprites", {})

                image_urls = {
                    "back_default": sprites.get("back_default"),
                    "back_shiny": sprites.get("back_shiny"),
                    "front_default": sprites.get("front_default"),
                    "front_shiny": sprites.get("front_shiny")
                }

                for image_type in image_urls.keys():
                    folder_path = os.path.join(base_folder, image_type)
                    ensure_folder_exists(folder_path)

                tasks = []
                for image_type, image_url in image_urls.items():
                    if image_url:
                        file_path = os.path.join(base_folder, image_type, f"{form_name}.png")
                        tasks.append(save_image(session, image_url, file_path, semaphore))

                await asyncio.gather(*tasks)
            else:
                print(f"Failed to fetch form data for {form_id}, status code: {response.status}")
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f"Error while fetching form data for {form_id}: {str(e)}")

async def download_pokemon_sprites():
    base_folder = config.Images_path
    ensure_folder_exists(base_folder)

    with open(config.Pokemon_data_path, 'r', encoding='utf-8') as f:
        pokemon_data = json.load(f)

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for pokemon in pokemon_data:
            pokemon_id = pokemon['idx']
            pokemon_slug = pokemon['slug']
            tasks.append(get_pokemon_sprites(session, pokemon_slug, pokemon_id, base_folder, semaphore))

        await asyncio.gather(*tasks)

async def download_form_sprites():
    base_folder = config.Images_path
    ensure_folder_exists(base_folder)

    with open(config.Pokemon_data_path, 'r', encoding='utf-8') as f:
        pokemon_data = json.load(f)

    total_forms = 0
    for pokemon in pokemon_data:
        total_forms += len(pokemon.get('forms', []))

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for form_id in range(10001, 10001 + total_forms):
            tasks.append(get_form_sprites(session, form_id, base_folder, semaphore))

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    print("Downloading normal images...")
    asyncio.run(download_pokemon_sprites())
    print("Downloading form images...")
    asyncio.run(download_form_sprites())
    print("Done!")
