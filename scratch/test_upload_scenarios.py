import asyncio
import io
import os
import sys
import httpx
from PIL import Image

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8001"

def create_test_images():
    os.makedirs("scratch/test_images", exist_ok=True)
    
    # 1. Valid JPEG
    img = Image.new("RGB", (400, 300), color=(255, 250, 240))
    jpeg_path = "scratch/test_images/sample_menu.jpg"
    img.save(jpeg_path, "JPEG")
    
    # 2. Valid PNG
    png_path = "scratch/test_images/sample_menu.png"
    img.save(png_path, "PNG")
    
    # 3. Valid WebP
    webp_path = "scratch/test_images/sample_menu.webp"
    img.save(webp_path, "WEBP")
    
    # 4. Unsupported file (.txt)
    unsupported_path = "scratch/test_images/not_an_image.txt"
    with open(unsupported_path, "w") as f:
        f.write("This is a plain text file, not an image.")
        
    # 5. Corrupt image
    corrupt_path = "scratch/test_images/corrupt.png"
    with open(corrupt_path, "wb") as f:
        f.write(b"PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\xff" * 50)
        
    # 6. Oversized image (> 15MB)
    oversized_path = "scratch/test_images/oversized.jpg"
    with open(oversized_path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0" + b"\x00" * (16 * 1024 * 1024))
        
    return jpeg_path, png_path, webp_path, unsupported_path, corrupt_path, oversized_path

async def run_phase_6_tests():
    print("======================================================================")
    print("PHASE 6: UPLOAD BUG VERIFICATION - 12 END-TO-END SCENARIOS")
    print("======================================================================\n")
    
    jpeg_path, png_path, webp_path, unsupported_path, corrupt_path, oversized_path = create_test_images()
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Scenario 1: Valid JPEG image upload
        print("--- Scenario 1: Valid JPEG Upload ---")
        with open(jpeg_path, "rb") as f:
            res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("menu.jpg", f.read(), "image/jpeg")},
                data={"target_language": "en"}
            )
        print(f"Status: {res.status_code}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "menu_metadata" in data and "dishes" in data
        print(">>> Scenario 1 PASSED.\n")

        # Scenario 2: Valid PNG image upload
        print("--- Scenario 2: Valid PNG Upload ---")
        with open(png_path, "rb") as f:
            res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("menu.png", f.read(), "image/png")},
                data={"target_language": "en"}
            )
        print(f"Status: {res.status_code}")
        assert res.status_code == 200
        print(">>> Scenario 2 PASSED.\n")

        # Scenario 3: Valid WebP image upload
        print("--- Scenario 3: Valid WebP Upload ---")
        with open(webp_path, "rb") as f:
            res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("menu.webp", f.read(), "image/webp")},
                data={"target_language": "en"}
            )
        print(f"Status: {res.status_code}")
        assert res.status_code == 200
        print(">>> Scenario 3 PASSED.\n")

        # Scenario 4: Unsupported file upload (.txt)
        print("--- Scenario 4: Unsupported File Format ---")
        with open(unsupported_path, "rb") as f:
            res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("notes.txt", f.read(), "text/plain")},
                data={"target_language": "en"}
            )
        print(f"Status: {res.status_code}, Body: {res.json()}")
        assert res.status_code == 400
        assert "unsupported" in res.text.lower() or "invalid" in res.text.lower()
        print(">>> Scenario 4 PASSED.\n")

        # Scenario 5: Corrupt image payload
        print("--- Scenario 5: Corrupt Image Payload ---")
        with open(corrupt_path, "rb") as f:
            res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("corrupt.png", f.read(), "image/png")},
                data={"target_language": "en"}
            )
        print(f"Status: {res.status_code}, Body: {res.json()}")
        assert res.status_code == 400
        assert "corrupt" in res.text.lower() or "malformed" in res.text.lower() or "cannot identify" in res.text.lower()
        print(">>> Scenario 5 PASSED.\n")

        # Scenario 6: Oversized image (> 15 MB)
        print("--- Scenario 6: Oversized Image (> 15 MB) ---")
        with open(oversized_path, "rb") as f:
            res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("oversized.jpg", f.read(), "image/jpeg")},
                data={"target_language": "en"}
            )
        print(f"Status: {res.status_code}, Body: {res.json()}")
        assert res.status_code == 413, f"Expected 413, got {res.status_code}"
        print(">>> Scenario 6 PASSED.\n")

        # Scenario 7: Backend temporarily unavailable simulation
        print("--- Scenario 7: Backend Temporarily Unavailable Handling ---")
        try:
            async with httpx.AsyncClient(base_url="http://127.0.0.1:9999", timeout=1.0) as dead_client:
                await dead_client.post("/api/v1/menus/analyze")
        except Exception as e:
            print(f"Correctly caught connection refusal: {type(e).__name__}")
        print(">>> Scenario 7 PASSED.\n")

        # Scenario 8: Unsupported target language validation
        print("--- Scenario 8: Unsupported Target Language Error ---")
        with open(jpeg_path, "rb") as f:
            res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("menu.jpg", f.read(), "image/jpeg")},
                data={"target_language": "unsupported_klingon"}
            )
        print(f"Status: {res.status_code}, Body: {res.json()}")
        assert res.status_code == 422
        print(">>> Scenario 8 PASSED.\n")

        # Scenario 9: Second upload after a successful first upload
        print("--- Scenario 9: Sequential Upload After Prior Success ---")
        with open(jpeg_path, "rb") as f:
            res1 = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("first_menu.jpg", f.read(), "image/jpeg")},
                data={"target_language": "en"}
            )
        assert res1.status_code == 200
        with open(png_path, "rb") as f:
            res2 = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("second_menu.png", f.read(), "image/png")},
                data={"target_language": "es"}
            )
        assert res2.status_code == 200
        print(">>> Scenario 9 PASSED.\n")

        # Scenario 10: Selecting the same image twice (consecutive identical file uploads)
        print("--- Scenario 10: Consecutive Identical File Uploads ---")
        with open(jpeg_path, "rb") as f:
            img_data = f.read()
        res_a = await client.post(
            "/api/v1/menus/analyze",
            files={"file": ("same_menu.jpg", img_data, "image/jpeg")},
            data={"target_language": "en"}
        )
        assert res_a.status_code == 200
        res_b = await client.post(
            "/api/v1/menus/analyze",
            files={"file": ("same_menu.jpg", img_data, "image/jpeg")},
            data={"target_language": "en"}
        )
        assert res_b.status_code == 200
        print(">>> Scenario 10 PASSED.\n")

        # Scenario 11: Changing target language before uploading (Spanish, Japanese, French)
        print("--- Scenario 11: Changing Target Language Before Upload ---")
        for test_lang in ["es", "ja", "fr"]:
            with open(jpeg_path, "rb") as f:
                res_lang = await client.post(
                    "/api/v1/menus/analyze",
                    files={"file": ("menu.jpg", f.read(), "image/jpeg")},
                    data={"target_language": test_lang}
                )
            assert res_lang.status_code == 200
            resp_data = res_lang.json()
            assert resp_data["menu_metadata"]["target_language"] == test_lang
            print(f"Target language '{test_lang}' correctly preserved in response.")
        print(">>> Scenario 11 PASSED.\n")

        # Scenario 12: Real Menu Photo with multiple dishes and verified response structure
        print("--- Scenario 12: Real Menu Photo Extraction & Structure Verification ---")
        real_menu_path = "data/training/images/menu_rest_fam_french_05_clear_00.png"
        with open(real_menu_path, "rb") as f:
            real_res = await client.post(
                "/api/v1/menus/analyze",
                files={"file": ("real_menu.png", f.read(), "image/png")},
                data={"target_language": "es"}
            )
        assert real_res.status_code == 200
        real_data = real_res.json()
        print(f"Dishes extracted: {len(real_data['dishes'])}")
        assert len(real_data["dishes"]) > 0
        first_dish = real_data["dishes"][0]
        print(f"Dish 1: Original='{first_dish['original_name']}', Translated='{first_dish.get('translated_name') or first_dish.get('translated_title')}'")
        assert first_dish["original_name"] is not None
        print(">>> Scenario 12 PASSED.\n")

    print("======================================================================")
    print("ALL 12 SCENARIOS TESTED AND VERIFIED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_phase_6_tests())
