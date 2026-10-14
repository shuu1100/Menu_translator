"""Allergen Reasoning & Dietary Safety Engine.

Enforces strict safety guardrails:
1. Inferred absence is NEVER proof of safety (not_listed != allergen-free).
2. Four-state allergen classification: contains, may_contain, not_listed, unknown.
3. Tri-state dietary assessment: yes, no, possible, unknown.
4. Prompt-injection defense: treats menu text and external records as untrusted data.
5. Deterministic calculation of user dietary conflicts with prominent staff confirmation warnings.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.app.db.models import DishRecord
from backend.app.schemas.menu_analysis import (
    AllergenWarning,
    DietaryCompatibility,
    DietaryFlagStatus,
    EvidenceStatus,
)

# Canonical 14 major allergens + religious/dietary restrictions
ALLERGEN_TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    "gluten": {
        "keywords": [
            "wheat", "flour", "pasta", "bread", "crust", "toast", "semolina", "spelt",
            "barley", "rye", "oats", "noodles", "ramen", "udon", "soba", "panko",
            "soy sauce", "shoyu", "batter", "roux", "malt", "seitan", "brioche", "crouton"
        ],
        "substitutes": ["gluten-free", "tamari", "rice flour", "corn flour"],
    },
    "dairy": {
        "keywords": [
            "milk", "cream", "butter", "cheese", "parmigiano", "mozzarella", "ricotta",
            "mascarpone", "cheddar", "pecorino", "paneer", "ghee", "yogurt", "whey",
            "casein", "lactose", "curd", "brie", "gouda", "custard", "gelato"
        ],
        "substitutes": ["dairy-free", "plant milk", "oat milk", "soy milk", "almond milk", "vegan cheese"],
    },
    "egg": {
        "keywords": [
            "egg", "eggs", "yolk", "albumin", "mayonnaise", "mayo", "aioli", "meringue",
            "hollandaise", "tagliatelle", "carbonara", "custard"
        ],
        "substitutes": ["egg-free", "vegan mayo"],
    },
    "fish": {
        "keywords": [
            "fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "bonito", "dashi",
            "fish sauce", "mackerel", "halibut", "seabass", "snapper", "sardine"
        ],
        "substitutes": [],
    },
    "crustaceans": {
        "keywords": [
            "shrimp", "prawn", "crab", "lobster", "crawfish", "crayfish", "krill", "langoustine"
        ],
        "substitutes": [],
    },
    "molluscs": {
        "keywords": [
            "squid", "calamari", "octopus", "clam", "clams", "mussel", "mussels",
            "oyster", "oysters", "scallop", "scallops", "snail", "escargot"
        ],
        "substitutes": [],
    },
    "peanuts": {
        "keywords": [
            "peanut", "peanuts", "groundnut", "arachis", "peanut butter", "satay", "groundnuts"
        ],
        "substitutes": [],
    },
    "tree_nuts": {
        "keywords": [
            "nut", "nuts", "almond", "walnut", "cashew", "pecan", "pistachio", "hazelnut",
            "macadamia", "pine nut", "pine nuts", "praline", "marzipan", "chestnut"
        ],
        "substitutes": ["nut-free"],
    },
    "soy": {
        "keywords": [
            "soy", "soya", "soybean", "soybeans", "tofu", "edamame", "miso", "shoyu",
            "tamari", "tempeh", "natto", "soy lecithin"
        ],
        "substitutes": ["soy-free"],
    },
    "sesame": {
        "keywords": [
            "sesame", "tahini", "tahina", "gomashio", "sesame oil", "sesame seeds", "halva"
        ],
        "substitutes": [],
    },
    "celery": {
        "keywords": ["celery", "celeriac", "celery salt", "celery stalk"],
        "substitutes": [],
    },
    "mustard": {
        "keywords": ["mustard", "dijon", "moutarde", "senf", "mustard seed", "mustard powder"],
        "substitutes": [],
    },
    "lupin": {
        "keywords": ["lupin", "lupine", "lupini"],
        "substitutes": [],
    },
    "sulphites": {
        "keywords": ["sulphite", "sulfite", "sulfur dioxide", "wine preservative"],
        "substitutes": [],
    },
    "pork": {
        "keywords": [
            "pork", "bacon", "ham", "prosciutto", "pancetta", "guanciale", "lard",
            "chashu", "carnitas", "al pastor", "chorizo", "sausage", "pork belly", "ribs"
        ],
        "substitutes": ["beef bacon", "turkey bacon"],
    },
    "alcohol": {
        "keywords": [
            "wine", "beer", "rum", "mirin", "sake", "bourbon", "whiskey", "vodka",
            "marsala", "cognac", "liqueur", "brandy", "schnapps"
        ],
        "substitutes": ["non-alcoholic", "alcohol-free"],
    },
}

# Suspicious phrases indicating prompt injection in menu text
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"system\s*:", re.IGNORECASE),
    re.compile(r"you\s+are\s+now", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?safety", re.IGNORECASE),
    re.compile(r"guaranteed\s+(100%\s+)?allergen[- ]free", re.IGNORECASE),
    re.compile(r"mark\s+this\s+dish\s+as\s+safe", re.IGNORECASE),
]

# Patterns detecting mysterious or undisclosed sauces
UNDISCLOSED_SAUCE_PATTERN = re.compile(
    r"\b(secret\s+sauce|house\s+sauce|special\s+sauce|chef'?s\s+sauce|house\s+dressing|gravy|mystery\s+sauce|curry\s+sauce|signature\s+sauce)\b",
    re.IGNORECASE,
)


class CulinarySafetyEngine:
    """Evaluates allergens, tri-state dietary compliance, and user conflicts with zero false safety claims."""

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> str:
        """Strip known prompt injection attempts from OCR text."""
        cleaned = text
        for pattern in PROMPT_INJECTION_PATTERNS:
            cleaned = pattern.sub("[REDACTED_SUSPICIOUS_TEXT]", cleaned)
        return cleaned

    @classmethod
    def detect_undisclosed_sauce(cls, text: str) -> bool:
        """Detect whether text mentions an unspecified or secret sauce."""
        return bool(UNDISCLOSED_SAUCE_PATTERN.search(text))

    @classmethod
    def assess_allergens(
        cls,
        original_name: str,
        printed_desc: str,
        extracted_ingredients: List[str],
        rag_record: Optional[DishRecord] = None,
    ) -> List[AllergenWarning]:
        """Synthesize allergen disclosures grounded in verified records and printed text."""
        warnings: List[AllergenWarning] = []
        covered_allergens: Set[str] = set()

        combined_text = cls.sanitize_untrusted_text(
            f"{original_name} {printed_desc} {' '.join(extracted_ingredients)}"
        ).lower()

        # 1. Authoritative groundings from verified RAG record
        if rag_record is not None:
            is_verified = rag_record.verification_status == "verified"
            for all_ev in rag_record.allergen_evidence:
                canonical_allergen = all_ev.allergen.lower().replace("-", "_")
                covered_allergens.add(canonical_allergen)

                status_map = {
                    "contains": EvidenceStatus.CONFIRMED if is_verified else EvidenceStatus.POSSIBLE,
                    "may_contain": EvidenceStatus.POSSIBLE,
                    "not_listed": EvidenceStatus.NOT_LISTED,
                    "unknown": EvidenceStatus.UNKNOWN,
                }
                status = status_map.get(all_ev.status.lower(), EvidenceStatus.UNKNOWN)

                severity = "critical" if status == EvidenceStatus.CONFIRMED else (
                    "warning" if status == EvidenceStatus.POSSIBLE else "advisory"
                )
                icon = "shield-alert" if severity == "critical" else (
                    "alert-triangle" if severity == "warning" else "info"
                )

                warnings.append(
                    AllergenWarning(
                        allergen=canonical_allergen,
                        status=status,
                        source=all_ev.evidence_source,
                        notes=f"Culinary KB [{all_ev.status}]: {all_ev.reviewer_metadata or 'Verified Record'}",
                        icon=icon,
                        severity=severity,
                    )
                )

        # 2. Text keyword scanning for printed disclosures not yet in RAG
        for allergen_name, data in ALLERGEN_TAXONOMY.items():
            if allergen_name in covered_allergens:
                continue

            # Check if keywords are in printed text
            matched_keywords = [kw for kw in data["keywords"] if kw in combined_text]
            if matched_keywords:
                warnings.append(
                    AllergenWarning(
                        allergen=allergen_name,
                        status=EvidenceStatus.POSSIBLE,
                        source="printed_menu_text",
                        notes=f"Keyword match from printed description: '{', '.join(matched_keywords)}'",
                        icon="alert-triangle",
                        severity="warning",
                    )
                )
                covered_allergens.add(allergen_name)

        # 3. Check for undisclosed/secret sauce
        if cls.detect_undisclosed_sauce(combined_text):
            warnings.append(
                AllergenWarning(
                    allergen="undisclosed_sauce_base",
                    status=EvidenceStatus.UNKNOWN,
                    source="printed_menu_warning",
                    notes="Dish mentions an undisclosed or house sauce; base ingredients cannot be verified. Confirm formulation with restaurant staff.",
                    icon="alert-circle",
                    severity="warning",
                )
            )

        return warnings

    @classmethod
    def evaluate_dietary_compatibility(
        cls,
        original_name: str,
        printed_desc: str,
        allergens: List[AllergenWarning],
        rag_record: Optional[DishRecord] = None,
    ) -> DietaryCompatibility:
        """Evaluate tri-state (yes/no/unknown) dietary flags with proof grounding."""
        combined_text = cls.sanitize_untrusted_text(f"{original_name} {printed_desc}").lower()

        # Check explicit meat / seafood presence
        is_meat = any(
            w in combined_text
            for w in [
                "beef", "pork", "chicken", "meat", "bacon", "prosciutto", "guanciale",
                "ham", "duck", "lamb", "veal", "steak", "ragu", "ragù", "chashu", "carnitas"
            ]
        ) or any(w.allergen in ["pork"] and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE] for w in allergens)

        is_seafood = any(
            w.allergen in ["fish", "crustaceans", "molluscs"]
            and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
            for w in allergens
        ) or any(w in combined_text for w in ["salmon", "tuna", "shrimp", "calamari", "dashi", "fish sauce"])

        # Check dairy / egg
        is_dairy = any(
            w.allergen == "dairy" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
            for w in allergens
        ) or any(w in combined_text for w in ["cheese", "butter", "cream", "milk", "parmigiano", "mozzarella"])

        is_egg = any(
            w.allergen == "egg" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
            for w in allergens
        ) or any(w in combined_text for w in ["egg", "yolk", "mayo", "mayonnaise"])

        # Check gluten
        is_gluten = any(
            w.allergen == "gluten" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
            for w in allergens
        ) or any(w in combined_text for w in ["pasta", "bread", "wheat", "flour", "ramen", "udon"])

        # Check pork / alcohol for halal
        has_pork = any(
            w.allergen == "pork" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
            for w in allergens
        ) or any(w in combined_text for w in ["pork", "bacon", "ham", "guanciale", "lard"])

        has_alcohol = any(
            w.allergen == "alcohol" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
            for w in allergens
        ) or any(w in combined_text for w in ["wine", "beer", "mirin", "sake", "rum", "liqueur"])

        # 1. Base derivation from detected ingredients
        vegan = DietaryFlagStatus.NO if (is_meat or is_seafood or is_dairy or is_egg) else DietaryFlagStatus.UNKNOWN
        vegetarian = DietaryFlagStatus.NO if (is_meat or is_seafood) else DietaryFlagStatus.UNKNOWN
        gluten_free = DietaryFlagStatus.NO if is_gluten else DietaryFlagStatus.UNKNOWN
        halal = DietaryFlagStatus.NO if (has_pork or has_alcohol) else DietaryFlagStatus.UNKNOWN

        confidence_notes = "Derived from menu text; unverified by authoritative culinary records."

        # 2. Upgrade with verified RAG records if present
        if rag_record is not None and rag_record.dietary_flags:
            flags = rag_record.dietary_flags
            is_verified = (rag_record.verification_status == "verified")

            def resolve_flag(rag_val: Any, derived: DietaryFlagStatus) -> DietaryFlagStatus:
                if derived == DietaryFlagStatus.NO:
                    return DietaryFlagStatus.NO  # Ingredient evidence overrides claims of YES
                if rag_val is True:
                    return DietaryFlagStatus.YES if is_verified else DietaryFlagStatus.POSSIBLE
                elif rag_val is False:
                    return DietaryFlagStatus.NO
                return derived

            vegan = resolve_flag(flags.get("is_vegan"), vegan)
            vegetarian = resolve_flag(flags.get("is_vegetarian"), vegetarian)
            gluten_free = resolve_flag(flags.get("is_gluten_free"), gluten_free)
            halal = resolve_flag(flags.get("is_halal"), halal)

            confidence_notes = (
                f"Grounded by culinary KB record '{rag_record.dish_id}' ({rag_record.verification_status})."
            )

        return DietaryCompatibility(
            vegan=vegan,
            vegetarian=vegetarian,
            gluten_free=gluten_free,
            halal=halal,
            confidence_notes=confidence_notes,
        )

    @classmethod
    def calculate_user_conflicts(
        cls,
        dietary: DietaryCompatibility,
        allergens: List[AllergenWarning],
        user_restrictions: List[str],
    ) -> List[str]:
        """Cross-check user dietary restrictions against evidence and flags.
        
        Strict rule: If user restriction is present but formulation is unknown,
        flag explicit advisory to confirm with staff.
        """
        conflicts: List[str] = []
        clean_restrictions = [r.strip().lower().replace("-", "_") for r in user_restrictions if r.strip()]

        for r in clean_restrictions:
            # 1. Lifestyle restrictions
            if "vegan" in r:
                if dietary.vegan == DietaryFlagStatus.NO:
                    conflicts.append("Non-vegan ingredients detected (violates vegan restriction)")
                elif dietary.vegan == DietaryFlagStatus.UNKNOWN:
                    conflicts.append("Vegan status unverified: Confirm formulation with restaurant staff")

            elif "vegetarian" in r:
                if dietary.vegetarian == DietaryFlagStatus.NO:
                    conflicts.append("Meat or seafood detected (violates vegetarian restriction)")
                elif dietary.vegetarian == DietaryFlagStatus.UNKNOWN:
                    conflicts.append("Vegetarian status unverified: Confirm formulation with restaurant staff")

            elif "halal" in r:
                if dietary.halal == DietaryFlagStatus.NO:
                    conflicts.append("Pork, alcohol, or non-halal ingredients detected (violates halal restriction)")
                elif dietary.halal == DietaryFlagStatus.UNKNOWN:
                    conflicts.append("Halal status unverified: Confirm meat sourcing and alcohol absence with restaurant staff")

            # 2. Specific allergen restrictions
            elif "gluten" in r or "celiac" in r:
                has_gluten = any(
                    w.allergen == "gluten" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
                    for w in allergens
                ) or (dietary.gluten_free == DietaryFlagStatus.NO)
                if has_gluten:
                    conflicts.append("Gluten containing ingredients detected (violates gluten-free restriction)")
                elif dietary.gluten_free == DietaryFlagStatus.UNKNOWN:
                    conflicts.append("Gluten-free status unverified: Confirm cross-contact risks with restaurant staff")

            elif "dairy" in r or "lactose" in r or "milk" in r:
                has_dairy = any(
                    w.allergen == "dairy" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
                    for w in allergens
                )
                if has_dairy:
                    conflicts.append("Dairy / milk ingredients detected (violates dairy restriction)")

            elif "nut" in r or "peanut" in r:
                has_nuts = any(
                    w.allergen in ["peanuts", "tree_nuts"]
                    and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
                    for w in allergens
                )
                if has_nuts:
                    conflicts.append("Nut or peanut ingredients detected (violates nut allergy restriction)")
                else:
                    conflicts.append("Nut allergy caution: Absence of listed nuts is not proof of allergen safety. Confirm with staff.")

            elif "shellfish" in r or "crustacean" in r:
                has_shellfish = any(
                    w.allergen in ["crustaceans", "molluscs"]
                    and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
                    for w in allergens
                )
                if has_shellfish:
                    conflicts.append("Shellfish / crustacean ingredients detected (violates shellfish restriction)")

            elif "soy" in r:
                has_soy = any(
                    w.allergen == "soy" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
                    for w in allergens
                )
                if has_soy:
                    conflicts.append("Soy ingredients detected (violates soy restriction)")

            elif "egg" in r:
                has_egg = any(
                    w.allergen == "egg" and w.status in [EvidenceStatus.CONFIRMED, EvidenceStatus.POSSIBLE]
                    for w in allergens
                )
                if has_egg:
                    conflicts.append("Egg ingredients detected (violates egg restriction)")

        # Undisclosed sauce warning
        if any(w.allergen == "undisclosed_sauce_base" for w in allergens):
            conflicts.append("Contains undisclosed sauce/dressing; allergens cannot be verified without kitchen staff confirmation")

        return conflicts
