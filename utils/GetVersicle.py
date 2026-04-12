import json
import random

def getRandomVersicle():
    routes = [
        # 'resources/verses/verses.json', 
        'resources/verses/verses_diomedes.json'
    ]
    selected_route = random.choice(routes)
    try:
        with open(selected_route, 'r', encoding='utf-8') as file:
            verses = json.load(file)

        verse = random.choice(verses['verses'])
        text = verse['text'] + " - " + verse['reference']
        return text

    except Exception as e:
        print("❌ Error al leer versículos:", e)
        return "Error al obtener versículo."
