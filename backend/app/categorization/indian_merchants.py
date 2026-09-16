"""
Deterministic Indian Merchant & Payment Rails Pattern Matcher.

Provides instant (< 0.1ms) zero-latency categorization for >100 leading Indian merchants,
UPI VPA strings, and payment rails across all 12 canonical financial categories.
"""

import re
from typing import Dict, List, Optional, Tuple

# Merchant patterns: (regex_pattern, category, clean_merchant_name)
MERCHANT_PATTERNS: List[Tuple[str, str, str]] = [
    # --- Dining & Food Delivery ---
    (r"\b(swiggy|bundl technologies)\b", "Dining", "Swiggy"),
    (r"\b(zomato)\b", "Dining", "Zomato"),
    (r"\b(mcdonalds?|mcd)\b", "Dining", "McDonald's"),
    (r"\b(starbucks|tata starbucks)\b", "Dining", "Starbucks"),
    (r"\b(dominos?|jubilant foodworks)\b", "Dining", "Domino's"),
    (r"\b(burger king)\b", "Dining", "Burger King"),
    (r"\b(kfc)\b", "Dining", "KFC"),
    (r"\b(subway)\b", "Dining", "Subway"),
    (r"\b(pizza hut)\b", "Dining", "Pizza Hut"),
    (r"\b(chai point|mountain trail)\b", "Dining", "Chai Point"),
    (r"\b(chaayos)\b", "Dining", "Chaayos"),
    (r"\b(cafe coffee day|ccd)\b", "Dining", "Cafe Coffee Day"),
    (r"\b(haldirams?)\b", "Dining", "Haldiram's"),
    (r"\b(barbeque nation)\b", "Dining", "Barbeque Nation"),
    (r"\b(behrouz|faasos|rebel foods)\b", "Dining", "Rebel Foods (Behrouz/Faasos)"),
    (r"\b(biryani by kilo)\b", "Dining", "Biryani By Kilo"),
    (r"\b(baskin robbins)\b", "Dining", "Baskin Robbins"),

    # --- Groceries & Quick Commerce ---
    (r"\b(blinkit|grofers)\b", "Groceries", "Blinkit"),
    (r"\b(zepto|kirana cart)\b", "Groceries", "Zepto"),
    (r"\b(instamart)\b", "Groceries", "Swiggy Instamart"),
    (r"\b(bigbasket|innovative retail)\b", "Groceries", "BigBasket"),
    (r"\b(dmart|avenue supermarts)\b", "Groceries", "DMart"),
    (r"\b(dunzo)\b", "Groceries", "Dunzo"),
    (r"\b(milkbasket)\b", "Groceries", "Milkbasket"),
    (r"\b(country delight)\b", "Groceries", "Country Delight"),
    (r"\b(licious|delightful gourmet)\b", "Groceries", "Licious"),
    (r"\b(freshtohome)\b", "Groceries", "FreshToHome"),
    (r"\b(natures basket)\b", "Groceries", "Nature's Basket"),
    (r"\b(more retail|more supermarket)\b", "Groceries", "More Retail"),
    (r"\b(spencers?)\b", "Groceries", "Spencer's"),
    (r"\b(supermarket|hypermarket|kirana|provision store)\b", "Groceries", "Local Grocery / Kirana"),

    # --- Shopping & E-Commerce ---
    (r"\b(amazon|amzn|amazon pay)\b", "Shopping", "Amazon"),
    (r"\b(flipkart)\b", "Shopping", "Flipkart"),
    (r"\b(myntra)\b", "Shopping", "Myntra"),
    (r"\b(ajio|reliance retail)\b", "Shopping", "Ajio / Reliance Retail"),
    (r"\b(meesho)\b", "Shopping", "Meesho"),
    (r"\b(nykaa|fsn e-commerce)\b", "Shopping", "Nykaa"),
    (r"\b(tata cliq)\b", "Shopping", "Tata CLiQ"),
    (r"\b(zara|inditex)\b", "Shopping", "Zara"),
    (r"\b(h&m|hennes)\b", "Shopping", "H&M"),
    (r"\b(uniqlo)\b", "Shopping", "Uniqlo"),
    (r"\b(decathlon)\b", "Shopping", "Decathlon"),
    (r"\b(croma|infiniti retail)\b", "Shopping", "Croma"),
    (r"\b(reliance digital)\b", "Shopping", "Reliance Digital"),
    (r"\b(vijay sales)\b", "Shopping", "Vijay Sales"),
    (r"\b(shoppers stop)\b", "Shopping", "Shoppers Stop"),
    (r"\b(westside|trent)\b", "Shopping", "Westside"),
    (r"\b(pantaloons|aditya birla fashion)\b", "Shopping", "Pantaloons"),

    # --- Transport, Travel & Fuel ---
    (r"\b(uber)\b", "Transport", "Uber"),
    (r"\b(ola|ani technologies)\b", "Transport", "Ola"),
    (r"\b(rapido|roppen)\b", "Transport", "Rapido"),
    (r"\b(namma metro|bmrc|dmrc|delhi metro|mumbai metro|metro rail)\b", "Transport", "Metro Transit"),
    (r"\b(irctc|indian railway)\b", "Transport", "IRCTC / Railways"),
    (r"\b(makemytrip|mmt)\b", "Transport", "MakeMyTrip"),
    (r"\b(yatra)\b", "Transport", "Yatra"),
    (r"\b(goibibo)\b", "Transport", "Goibibo"),
    (r"\b(easemytrip)\b", "Transport", "EaseMyTrip"),
    (r"\b(indigo|interglobe)\b", "Transport", "IndiGo"),
    (r"\b(air india|tata sia|vistara)\b", "Transport", "Air India / Vistara"),
    (r"\b(fastag|nhai|toll)\b", "Transport", "FASTag Toll"),
    (r"\b(hpcl|hindustan petroleum)\b", "Transport", "HPCL Fuel"),
    (r"\b(bpcl|bharat petroleum)\b", "Transport", "BPCL Fuel"),
    (r"\b(iocl|indian oil)\b", "Transport", "IOCL Fuel"),
    (r"\b(shell|petrol pump|fuel station)\b", "Transport", "Fuel / Petrol Pump"),

    # --- Entertainment & Subscriptions ---
    (r"\b(netflix)\b", "Subscriptions", "Netflix"),
    (r"\b(spotify)\b", "Subscriptions", "Spotify"),
    (r"\b(prime video|prime member)\b", "Subscriptions", "Amazon Prime"),
    (r"\b(hotstar|disney\+?|disney plus)\b", "Subscriptions", "Disney+ Hotstar"),
    (r"\b(youtube|google play|google \*)\b", "Subscriptions", "YouTube / Google"),
    (r"\b(apple\.com|itunes|icloud)\b", "Subscriptions", "Apple Services"),
    (r"\b(sonyliv)\b", "Subscriptions", "SonyLIV"),
    (r"\b(zee5)\b", "Subscriptions", "Zee5"),
    (r"\b(bookmyshow|bigtree)\b", "Entertainment", "BookMyShow"),
    (r"\b(pvr|inox)\b", "Entertainment", "PVR INOX Cinemas"),
    (r"\b(cult\.fit|curefit)\b", "Subscriptions", "Cult.fit"),

    # --- Utilities & Bills ---
    (r"\b(bescom|tata power|adani electricity|torrent power|mseb|discom)\b", "Utilities", "Electricity Bill"),
    (r"\b(mahanagar gas|igl|indraprastha gas|gujarat gas|adani gas)\b", "Utilities", "Piped Gas Bill"),
    (r"\b(airtel|bharti airtel)\b", "Utilities", "Airtel Telecomm"),
    (r"\b(jio|reliance jio)\b", "Utilities", "Reliance Jio"),
    (r"\b(vodafone|vi post|vodafone idea)\b", "Utilities", "Vi Telecom"),
    (r"\b(act fibernet|act broadband)\b", "Utilities", "ACT Fibernet"),
    (r"\b(hathway|tata play fiber|airtel broadband)\b", "Utilities", "Broadband Internet"),
    (r"\b(cred|credclub)\b", "Utilities", "CRED Bill Payment"),
    (r"\b(billdesk|bbps|bharat bill)\b", "Utilities", "Utility Bill Payment"),
    (r"\b(water board|bwssb|jal board)\b", "Utilities", "Municipal Water Bill"),

    # --- Medical & Healthcare ---
    (r"\b(apollo pharmacy|apollo hospitals?)\b", "Medical", "Apollo Healthcare"),
    (r"\b(pharmeasy)\b", "Medical", "PharmEasy"),
    (r"\b(1mg|tata 1mg)\b", "Medical", "Tata 1mg"),
    (r"\b(netmeds)\b", "Medical", "Netmeds"),
    (r"\b(medplus)\b", "Medical", "MedPlus Pharmacy"),
    (r"\b(practo)\b", "Medical", "Practo"),
    (r"\b(dr lal pathlabs?)\b", "Medical", "Dr Lal PathLabs"),
    (r"\b(srl diagnostics?|agilus)\b", "Medical", "Agilus Diagnostics"),
    (r"\b(max healthcare|fortis|manipal hospital|hospital|clinic|chemist)\b", "Medical", "Hospital / Clinic"),

    # --- Rent & Housing ---
    (r"\b(rent|house rent|flat rent|landlord|room rent)\b", "Rent", "House Rent"),
    (r"\b(nobroker)\b", "Rent", "NoBroker Rent"),
    (r"\b(mygate|society maintenance)\b", "Rent", "Society Maintenance"),

    # --- Investments & Tax-Saving ---
    (r"\b(zerodha)\b", "Miscellaneous", "Zerodha Investments"),
    (r"\b(groww|nextbillion)\b", "Miscellaneous", "Groww Investments"),
    (r"\b(angel one|angel broking)\b", "Miscellaneous", "Angel One"),
    (r"\b(upstox|rksv)\b", "Miscellaneous", "Upstox"),
    (r"\b(kuvera)\b", "Miscellaneous", "Kuvera"),
    (r"\b(cams|karvy|kfintech)\b", "Miscellaneous", "Mutual Fund Registrar"),
    (r"\b(nps|national pension)\b", "Miscellaneous", "NPS Tier I Contribution"),
    (r"\b(ppf|public provident fund)\b", "Miscellaneous", "PPF Deposit"),
    (r"\b(lic of india|life insurance corporation)\b", "Miscellaneous", "LIC Premium"),
    (r"\b(hdfc life|sbi life|icici prudential life|max life)\b", "Miscellaneous", "Life Insurance Premium"),
    (r"\b(star health|care health|niva bupa)\b", "Medical", "Health Insurance Premium"),
    (r"\b(mutual fund|sip\b|uti mf|hdfc mf|sbi mf|nippon india)\b", "Miscellaneous", "Mutual Fund SIP"),

    # --- Salary Credit ---
    (r"\b(salary|payroll|wage|stipend)\b", "Salary Credit", "Salary Credit"),
    (r"\b(wipro|infosys|tcs|tata consultancy|hcl tech|accenture|cognizant)\b", "Salary Credit", "Corporate Salary"),
    (r"\b(google india|microsoft india|amazon dev center)\b", "Salary Credit", "Tech Employer Salary"),

    # --- Self-Transfer & Internal ---
    (r"\b(self-transfer|self transfer|own account|funds transfer to own)\b", "Self-Transfer", "Self Transfer"),
    (r"\b(credit card payment|cc payment|auto-debit cc)\b", "Self-Transfer", "Credit Card Payment"),
]


def match_merchant_pattern(description: str) -> Optional[Tuple[str, str, float]]:
    """
    Checks if a transaction narration matches known Indian merchants or payment rails.
    Returns: (category, clean_merchant_name, confidence) or None if no match.
    """
    if not description:
        return None

    desc_clean = description.lower().replace("/", " ").replace("-", " ").replace("@", " ")
    # Replace multiple whitespaces
    desc_clean = re.sub(r"\s+", " ", desc_clean)

    for pattern, category, merchant in MERCHANT_PATTERNS:
        if re.search(pattern, desc_clean):
            return category, merchant, 0.98

    return None
