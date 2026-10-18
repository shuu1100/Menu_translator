import urllib.request
import json

api_key = 'b0d737a6-ad25-43eb-ad1e-bd4c92453857:fx'
url = 'https://api-free.deepl.com/v2/translate'

texts = [
  'Universal Menu Translator',
  'Local AI Lens',
  'Privacy-Preserving On-Device Vision & Culinary RAG',
  'Website Language',
  'Translate Menu To',
  'Scan',
  'Upload',
  'Reset'
]

for t in texts:
    payload = {'text': [t], 'target_lang': 'ES', 'tag_handling': 'xml', 'ignore_tags': ['ph']}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Authorization': f'DeepL-Auth-Key {api_key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode('utf-8'))
            print('SUCCESS:', t, '->', res['translations'][0]['text'])
    except urllib.error.HTTPError as e:
        print('FAILED:', t, e.code, e.read().decode('utf-8'))
