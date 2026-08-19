"""
Business Logic Constants for GraphVoyageAI

Domain-specific constants like airport codes, country mappings, etc.
Separate from config.py which handles environment/settings.
"""

# ============================================
# COUNTRY CODE ALIASES
# ============================================
# Maps common country names/aliases to ISO 2-letter codes

COUNTRY_ALIASES = {
    # North America
    "usa": "US",
    "u.s.a": "US",
    "u.s.": "US",
    "america": "US",
    "united states": "US",
    "canada": "CA",
    
    # Europe
    "uk": "GB",
    "u.k.": "GB",
    "britain": "GB",
    "england": "GB",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "turkey": "TR",
    
    # Middle East
    "uae": "AE",
    "dubai": "AE",
    "qatar": "QA",
    "saudi arabia": "SA",
    
    # Asia
    "south korea": "KR",
    "korea": "KR",
    "russia": "RU",
    "vietnam": "VN",
    "bangladesh": "BD",
    "india": "IN",
    "japan": "JP",
    "china": "CN",
    "singapore": "SG",
    "malaysia": "MY",
    "thailand": "TH",
    "indonesia": "ID",
    "nepal": "NP",
    
    # Oceania
    "australia": "AU",
}

# ============================================
# MAIN AIRPORTS BY COUNTRY
# ============================================
# Primary international airport for each country

COUNTRY_MAIN_AIRPORT = {
    # Asia
    "BD": "DAC",  # Bangladesh - Dhaka
    "IN": "DEL",  # India - Delhi
    "JP": "NRT",  # Japan - Tokyo Narita
    "CN": "PEK",  # China - Beijing
    "KR": "ICN",  # South Korea - Seoul Incheon
    "SG": "SIN",  # Singapore
    "MY": "KUL",  # Malaysia - Kuala Lumpur
    "TH": "BKK",  # Thailand - Bangkok
    "ID": "CGK",  # Indonesia - Jakarta
    "NP": "KTM",  # Nepal - Kathmandu
    "VN": "SGN",  # Vietnam - Ho Chi Minh (add if needed)
    
    # Middle East
    "AE": "DXB",  # UAE - Dubai
    "QA": "DOH",  # Qatar - Doha
    "SA": "JED",  # Saudi Arabia - Jeddah
    "TR": "IST",  # Turkey - Istanbul
    
    # North America
    "US": "JFK",  # USA - New York JFK
    "CA": "YYZ",  # Canada - Toronto
    
    # Europe
    "GB": "LHR",  # UK - London Heathrow
    "DE": "FRA",  # Germany - Frankfurt
    "FR": "CDG",  # France - Paris Charles de Gaulle
    "IT": "FCO",  # Italy - Rome Fiumicino
    "ES": "MAD",  # Spain - Madrid
    
    # Oceania
    "AU": "SYD",  # Australia - Sydney
}

# ============================================
# MAIN AIRPORTS BY CITY
# ============================================
# Primary airport for major cities

CITY_MAIN_AIRPORT = {
    # Bangladesh
    "dhaka": "DAC",
    
    # India
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "kolkata": "CCU",
    "chennai": "MAA",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "hyderabad": "HYD",
    "pune": "PNQ",
    
    # Japan
    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",  # Kyoto uses Osaka airport
    
    # USA
    "new york": "JFK",
    "los angeles": "LAX",
    "chicago": "ORD",
    "san francisco": "SFO",
    "miami": "MIA",
    "boston": "BOS",
    
    # UK
    "london": "LHR",
    
    # UAE
    "dubai": "DXB",
    "abu dhabi": "AUH",
    
    # Singapore
    "singapore": "SIN",
    
    # Malaysia
    "kuala lumpur": "KUL",
    
    # Thailand
    "bangkok": "BKK",
    
    # Qatar
    "doha": "DOH",
    
    # Turkey
    "istanbul": "IST",
    
    # Canada
    "toronto": "YYZ",
    "vancouver": "YVR",
    
    # Australia
    "sydney": "SYD",
    "melbourne": "MEL",
    
    # Europe
    "paris": "CDG",
    "rome": "FCO",
    "madrid": "MAD",
    "frankfurt": "FRA",
    "amsterdam": "AMS",
    "berlin": "BER",
}

# ============================================
# AGENT NAMES
# ============================================
# Known agent names in the system

KNOWN_AGENTS = {
    "supervisor_agent",
    "flight_agent",
    "hotel_agent",
    "weather_agent",
    "budget_agent",
    "itinerary_agent",
}

AGENT_EXECUTION_ORDER = [
    "flight_agent",
    "hotel_agent",
    "weather_agent",
    "budget_agent",
    "itinerary_agent",
]
