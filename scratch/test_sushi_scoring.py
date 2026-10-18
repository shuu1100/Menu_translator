import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from backend.app.services.images.query_builder import calculate_match_relevance, build_image_search_query
from backend.app.services.images.providers.unsplash import UnsplashImageProvider

sushi_candidate = {
    "description": "Assorted sushi and kimbap rolls on wooden platter",
    "alt_description": "Delicious traditional sushi roll with salmon and rice",
    "tags": [
        {"title": "sushi"},
        {"title": "japanese food"},
        {"title": "korean"},
        {"title": "food"},
        {"title": "meal"},
        {"title": "dish"},
        {"title": "roll"},
    ]
}

provider = UnsplashImageProvider(access_key="dummy_key_1234567890")

# Test 1: Milk tea item
score_milktea = provider._score_candidate(
    photo=sushi_candidate,
    dish_name="Brown Sugar Milk Tea",
    native_name="브라운슈가 밀크티",
    category="beverage",
)
print("Score for Milk Tea vs Sushi Candidate:", score_milktea)

# Test 2: "브라운소프트 시그니처"
score_soft = provider._score_candidate(
    photo=sushi_candidate,
    dish_name="브라운소프트 시그니처",
    native_name="브라운소프트 시그니처",
    category="main_dish",
)
print("Score for 브라운소프트 시그니처 vs Sushi Candidate:", score_soft)
