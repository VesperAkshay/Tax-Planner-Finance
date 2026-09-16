"""
LLM-Assisted Batch Categorizer for Bank Transactions.

Uses OpenRouter (free model: inclusionai/ling-3.0-flash-sante:free) to intelligently classify
ambiguous Indian UPI and NEFT transaction descriptions into canonical categories,
and extracts clean merchant names.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.agent.llm_client import get_llm_client_and_model
from app.categorization.feedback_loop import CANONICAL_CATEGORIES, record_user_feedback

logger = logging.getLogger(__name__)


def categorize_batch_with_llm(
    descriptions: List[str],
    user_id: int = 1,
) -> List[Dict[str, Any]]:
    """
    Classifies a list of transaction descriptions using the OpenRouter LLM.
    Returns list of dicts with:
    {
        "category": str,
        "merchant": str,
        "confidence": float,
        "needs_review": bool
    }
    """
    if not descriptions:
        return []

    client, model, provider = get_llm_client_and_model()
    if not client or not model:
        logger.info("No LLM client available for batch categorization. Returning defaults.")
        return [
            {
                "category": "Uncategorized",
                "merchant": desc[:30],
                "confidence": 0.0,
                "needs_review": True,
            }
            for desc in descriptions
        ]

    # Format batch prompt
    items_text = "\n".join(f"[{i}] {d}" for i, d in enumerate(descriptions))
    categories_str = ", ".join(CANONICAL_CATEGORIES)

    system_prompt = (
        "You are an expert Indian banking and UPI transaction classification assistant.\n"
        f"Allowed Canonical Categories strictly:\n{categories_str}\n\n"
        "Instructions:\n"
        "1. For each numbered transaction narration, classify it into the single most accurate category.\n"
        "2. Extract a clean, human-readable merchant or entity name (e.g., 'Swiggy', 'DMart', 'Netflix', 'Electricity Bill', 'Salary', 'P2P Transfer').\n"
        "3. Provide a confidence between 0.80 and 0.99.\n"
        "4. Output MUST be ONLY a valid JSON array of objects with keys: 'index', 'category', 'merchant', 'confidence'. Do not include explanation or thoughts."
    )

    user_prompt = f"Classify these Indian bank statement transactions:\n{items_text}"

    try:
        if provider in ("openrouter", "openai"):
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            raw_text = completion.choices[0].message.content or ""
        elif provider == "anthropic":
            resp = client.messages.create(
                model=model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = resp.content[0].text or ""
        else:
            raw_text = ""

        # Extract JSON array from LLM response
        json_match = re.search(r"\[\s*\{.*\}\s*\]", raw_text, re.DOTALL)
        if json_match:
            parsed_results = json.loads(json_match.group(0))
        else:
            parsed_results = json.loads(raw_text)

        # Map back by index
        results_by_index: Dict[int, Dict[str, Any]] = {}
        for item in parsed_results:
            idx = int(item.get("index", -1))
            cat = str(item.get("category", "Uncategorized")).strip()
            # Normalize category if minor typo
            matched_cat = next((c for c in CANONICAL_CATEGORIES if c.lower() == cat.lower()), "Uncategorized")
            results_by_index[idx] = {
                "category": matched_cat,
                "merchant": str(item.get("merchant", descriptions[idx][:30] if 0 <= idx < len(descriptions) else "Unknown")),
                "confidence": float(item.get("confidence", 0.90)),
                "needs_review": False if matched_cat != "Uncategorized" else True,
            }

        final_list: List[Dict[str, Any]] = []
        for i, desc in enumerate(descriptions):
            if i in results_by_index:
                res = results_by_index[i]
                final_list.append(res)
                # Auto-feed into learning loop
                if res["category"] != "Uncategorized":
                    try:
                        record_user_feedback(
                            user_id=user_id,
                            description=desc,
                            confirmed_category=res["category"],
                            original_predicted_category="Uncategorized",
                            original_confidence=0.5,
                        )
                    except Exception as fe:
                        logger.debug("Feedback record error: %s", fe)
            else:
                final_list.append({
                    "category": "Uncategorized",
                    "merchant": desc[:30],
                    "confidence": 0.0,
                    "needs_review": True,
                })

        return final_list

    except Exception as e:
        logger.warning("LLM batch categorization failed: %s. Falling back to default.", e)
        return [
            {
                "category": "Uncategorized",
                "merchant": desc[:30],
                "confidence": 0.0,
                "needs_review": True,
            }
            for desc in descriptions
        ]
