import json
import urllib.request
import os
import time

messages_dir = 'frontend/src/messages'

with open(os.path.join(messages_dir, 'en.json'), 'r', encoding='utf-8') as f:
    en_dict = json.load(f)

def flatten(d, prefix=''):
    items = []
    for k, v in d.items():
        new_key = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key))
        else:
            items.append((new_key, v))
    return items

def unflatten(items):
    res = {}
    for k, v in items:
        parts = k.split('.')
        curr = res
        for part in parts[:-1]:
            curr = curr.setdefault(part, {})
        curr[parts[-1]] = v
    return res

en_flat = dict(flatten(en_dict))

deepl_langs = ['es', 'fr', 'ja', 'ko', 'zh', 'it', 'pt', 'ru', 'ar']

for lang in deepl_langs:
    lpath = os.path.join(messages_dir, f'{lang}.json')
    if not os.path.exists(lpath):
        current_dict = {}
    else:
        with open(lpath, 'r', encoding='utf-8') as f:
            current_dict = json.load(f)

    cur_flat = dict(flatten(current_dict))
    
    # Keys that need translation: missing or identically equal to English text
    missing_keys = []
    for k, en_text in en_flat.items():
        if k not in cur_flat or (cur_flat[k] == en_text and len(en_text) > 3 and not k.endswith('.scan') and not k.endswith('.upload') and not k.endswith('.reset') and not k.endswith('.halal') and not k.endswith('.vegan')):
            missing_keys.append(k)

    if not missing_keys:
        print(f'{lang}.json is 100% complete.')
        continue

    print(f'{lang}: translating {len(missing_keys)} missing/untranslated keys via DeepL...')
    
    # Batch in groups of 10
    chunk_size = 10
    for i in range(0, len(missing_keys), chunk_size):
        chunk_keys = missing_keys[i:i+chunk_size]
        chunk_texts = [en_flat[k] for k in chunk_keys]
        payload = json.dumps({'texts': chunk_texts, 'target_language': lang}).encode('utf-8')
        req = urllib.request.Request(
            'http://127.0.0.1:8001/api/v1/translate/ui',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for k, item in zip(chunk_keys, data['translations']):
                    cur_flat[k] = item['translated']
        except Exception as e:
            print(f'Error on {lang} chunk: {e}')
        time.sleep(0.3)

    # Re-save complete dictionary
    complete_dict = unflatten(list(cur_flat.items()))
    with open(lpath, 'w', encoding='utf-8') as f:
        json.dump(complete_dict, f, ensure_ascii=False, indent=2)
    print(f'Saved {lang}.json with {len(cur_flat)} total keys.')
