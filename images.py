import asyncio
import aiohttp
import aiofiles
import os
import json
import config

def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

async def save_image(session, url, file_path):
    async with session.get(url) as response:
        if response.status == 200:
            async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())

async def get_pokemon_sprites(session, pokemon_slug, pokemon_id, base_folder):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/"
    async with session.get(url) as response:
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
                    tasks.append(save_image(session, image_url, file_path))

            await asyncio.gather(*tasks)

async def download_pokemon_sprites():
    base_folder = config.Images_path
    ensure_folder_exists(base_folder)

    with open(config.Pokemon_data_path, 'r', encoding='utf-8') as f:
        pokemon_data = json.load(f)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for pokemon in pokemon_data:
            pokemon_id = pokemon['idx']
            pokemon_slug = pokemon['slug']
            tasks.append(get_pokemon_sprites(session, pokemon_slug, pokemon_id, base_folder))

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(download_pokemon_sprites())
