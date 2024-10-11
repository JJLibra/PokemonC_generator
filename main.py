import asyncio
import aiohttp
import json
import config

async def get_generation_pokemon(session, genid):
    url = f"https://pokeapi.co/api/v2/generation/{genid}/"
    async with session.get(url) as response:
        generation_data = await response.json()
        pokemon_species_list = generation_data['pokemon_species']
        return pokemon_species_list

async def get_pokemon_details(session, pokemon_url, genid):
    async with session.get(pokemon_url) as response:
        pokemon_data = await response.json()

        names = {}
        for name_entry in pokemon_data['names']:
            lang = name_entry['language']['name'].lower()
            names[lang] = name_entry['name']

        descriptions = {}
        for flavor_text in pokemon_data['flavor_text_entries']:
            lang = flavor_text['language']['name'].lower()
            if lang not in descriptions:
                descriptions[lang] = flavor_text['flavor_text']

        forms = []
        for variety in pokemon_data['varieties']:
            if not variety['is_default']:
                forms.append(variety['pokemon']['name'])

        pokemon_info = {
            'idx': pokemon_data['id'],
            'slug': pokemon_data['name'],
            'gen': genid,
            'name': names,
            'desc': descriptions,
            'forms': forms
        }
        return pokemon_info

async def fetch_generation_data(session, genid):
    pokemon_species_list = await get_generation_pokemon(session, genid)
    
    tasks = []
    for species in pokemon_species_list:
        pokemon_url = species['url']
        tasks.append(get_pokemon_details(session, pokemon_url, genid))
    
    generation_pokemon_data = await asyncio.gather(*tasks)
    return generation_pokemon_data

async def main():
    all_pokemon_data = []

    gens = config.Gens

    async with aiohttp.ClientSession() as session:
        tasks = []
        for genid in range(1, gens + 1):
            tasks.append(fetch_generation_data(session, genid))
        
        generations_data = await asyncio.gather(*tasks)

        for gen_data in generations_data:
            all_pokemon_data.extend(gen_data)

    all_pokemon_data.sort(key=lambda x: x['idx'])

    with open(config.Pokemon_data_path, 'w', encoding='utf-8') as f:
        json.dump(all_pokemon_data, f, ensure_ascii=True, indent=4)

if __name__ == '__main__':
    asyncio.run(main())
