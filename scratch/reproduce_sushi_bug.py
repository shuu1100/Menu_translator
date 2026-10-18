import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
import asyncio
from backend.app.schemas.image_search import DishImageQuery
from backend.app.services.images.providers.curated import CuratedImageProvider

async def main():
    provider = CuratedImageProvider()
    q = DishImageQuery(
        dish_id="test",
        dish_name="브라운소프트 시그니처",
        native_name="브라운소프트 시그니처",
        transliteration="Beuraunsopeuteu Sigeunicheo",
    )
    result = await provider.search_image(q)
    print("Result dish:", result.alt_text)
    print("Result image_url:", result.image_url)
    print("Is fallback:", result.is_fallback)

asyncio.run(main())
