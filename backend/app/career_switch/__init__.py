"""
Career Switch & Offer Letter Decoder Engine Module.
"""

from app.career_switch.switch_engine import (
    compare_two_offers,
    decode_offer_ctc,
    simulate_midyear_switch,
)

__all__ = [
    "decode_offer_ctc",
    "simulate_midyear_switch",
    "compare_two_offers",
]
