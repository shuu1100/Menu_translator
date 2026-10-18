import urllib.request
import re

url = "http://localhost:3000/"
try:
    with urllib.request.urlopen(url) as response:
        html = response.read().decode("utf-8")
        print("HTML length:", len(html))
        scripts = re.findall(r'src="([^"]+?\.js[^"]*)"', html)
        print("Found scripts count:", len(scripts))
        for s in scripts:
            full_url = "http://localhost:3000" + s if s.startswith("/") else s
            try:
                with urllib.request.urlopen(full_url) as s_resp:
                    print(s_resp.status, s)
            except Exception as e:
                print("FAIL", s, e)
except Exception as e:
    print("Failed to open page:", e)
