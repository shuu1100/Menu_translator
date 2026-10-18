import os
import json

messages_dir = 'frontend/src/messages'
for fname in sorted(os.listdir(messages_dir)):
    if fname.endswith('.json'):
        fpath = os.path.join(messages_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            hero_pill = data.get('hero', {}).get('pill', 'N/A')
            print(f'{fname}: {len(data)} sections | hero.pill = "{hero_pill}"')
