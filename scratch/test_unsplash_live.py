import urllib.request
import urllib.parse
import json

def test():
    key = "1Hb2pCYogKgVV6To-3ybUeldLdyDHS6IcLAviZP0F1g"
    dishes = [
        ("Tonkotsu Ramen", "豚骨ラーメン", "Japanese", "Tonkotsu Ramen Japanese soup noodles"),
        ("Kimchi Fried Rice", "김치볶음밥", "Korean", "Korean Kimchi Fried Rice dish"),
        ("Mango Smoothie", "망고 스무디", "Korean", "Mango Smoothie drink beverage"),
        ("Pad Thai", "ผัดไทย", "Thai", "Pad Thai noodles dish"),
    ]

    for name, native, cuisine, q in dishes:
        url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(q)}&per_page=4&orientation=landscape&content_filter=high"
        req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            rem = resp.headers.get("X-Ratelimit-Remaining")
            results = data.get("results", [])
            print(f"\n=== Dish: {name} ({cuisine}) | Query: '{q}' | Rate Remaining: {rem} ===")
            print(f"Total results: {data.get('total')}, returned: {len(results)}")
            for idx, r in enumerate(results):
                desc = r.get("description") or r.get("alt_description") or "No description"
                user = r.get("user", {}).get("name", "Unknown")
                tags = [t.get("title") for t in r.get("tags", []) if t.get("title")]
                download_loc = r.get("links", {}).get("download_location")
                print(f"  [{idx}] ID: {r.get('id')} | By: {user}")
                print(f"      Desc: {desc[:60]}")
                print(f"      Tags: {tags[:5]}")
                print(f"      Download Location: {download_loc}")

if __name__ == "__main__":
    test()
