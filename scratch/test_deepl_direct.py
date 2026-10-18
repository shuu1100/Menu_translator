import urllib.request
import json

api_key = 'b0d737a6-ad25-43eb-ad1e-bd4c92453857:fx'
url = 'https://api-free.deepl.com/v2/translate'

payload1 = {'text': ['Hello <ph id="0"/> world'], 'target_lang': 'ES', 'tag_handling': 'xml', 'ignore_tags': ['ph']}
req1 = urllib.request.Request(url, data=json.dumps(payload1).encode('utf-8'), headers={'Authorization': f'DeepL-Auth-Key {api_key}', 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req1) as r:
        print('Array status:', r.status)
except urllib.error.HTTPError as e:
    print('Array error:', e.code, e.read().decode('utf-8'))

payload2 = {'text': ['Hello <ph id="0"/> world'], 'target_lang': 'ES', 'tag_handling': 'xml', 'ignore_tags': ['ph']}
# In JSON request to DeepL: ignore_tags should be a list of strings: ["ph"] or comma-separated string "ph"
payload3 = {'text': ['Hello <ph id="0"/> world'], 'target_lang': 'ES', 'tag_handling': 'xml', 'ignore_tags': ['ph']}
# What if tag_handling="xml" without ignore_tags? DeepL parses XML and preserves tags!
payload4 = {'text': ['Hello <x id="0"/> world'], 'target_lang': 'ES', 'tag_handling': 'xml'}
req4 = urllib.request.Request(url, data=json.dumps(payload4).encode('utf-8'), headers={'Authorization': f'DeepL-Auth-Key {api_key}', 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req4) as r:
        print('XML status:', r.status, r.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('XML error:', e.code, e.read().decode('utf-8'))
