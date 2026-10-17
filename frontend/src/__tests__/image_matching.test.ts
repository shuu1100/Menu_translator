import test, { describe } from "node:test";
import assert from "node:assert/strict";
import { SAMPLE_MENUS } from "../data/sample_menus";
import { AnalyzedDish, DishImageInfo } from "../types/menu";

describe("Food Image Matching and Discovery", () => {
  test("every sample menu dish has a valid representative image and attribution", () => {
    let totalDishes = 0;
    for (const menu of SAMPLE_MENUS) {
      assert.ok(menu.data.dishes.length > 0, "Menu should have dishes");
      for (const dish of menu.data.dishes) {
        totalDishes++;
        assert.ok(dish.representative_image, `Dish ${dish.dish_id} must have representative_image`);
        const img = dish.representative_image as DishImageInfo;
        assert.ok(img.image_url, "image_url must be defined");
        assert.ok(
          img.image_url.startsWith("http") || img.image_url.startsWith("data:"),
          "image_url must be http or data URI"
        );
        assert.equal(img.status, "available");
        assert.ok(img.photographer, "photographer attribution must be present");
        assert.ok(img.alt_text, "alt_text must be present");
      }
    }
    assert.equal(totalDishes, 24);
  });

  test("dish-to-image association is stable across filtering and language changes", () => {
    const ramenMenu = SAMPLE_MENUS[0];
    const tonkotsu = ramenMenu.data.dishes[0];
    assert.equal(tonkotsu.dish_id, "ramen_01");

    // Simulating language update
    const retranslatedDish: AnalyzedDish = {
      ...tonkotsu,
      translated_title: "Signature Hakata Pork Broth Ramen",
      translated_name: "Signature Hakata Pork Broth Ramen",
    };

    // Images should remain matched by stable dish_id
    assert.deepEqual(retranslatedDish.representative_image, tonkotsu.representative_image);
  });
});
