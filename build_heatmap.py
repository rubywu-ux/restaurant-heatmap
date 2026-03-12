"""
Restaurant Heatmap Generator
Reads transactions.csv + Uber Eats data, geocodes restaurants, builds Folium heatmap.
"""
import csv
import re
import math
from datetime import datetime
import folium
from folium.plugins import HeatMap

# Home base: IRO Apartments, 5233 15th Ave NE, Seattle, WA 98105
HOME_LAT = 47.6680
HOME_LON = -122.3115

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

###############################################################################
# KNOWN RESTAURANT COORDINATES
# Manually curated from Google Maps for accuracy
###############################################################################
KNOWN_COORDS = {
    # ===== SEATTLE, WA - U-District / University Way =====
    "center table|seattle": (47.6599, -122.3045),  # Center Table, 4294 Little Canoe Channel NE (UW Campus)
    "aplus hong ko|seattle": (47.5983, -122.3243),  # A+ HK Restaurant, 667 S King St (Chinatown)
    "aplus hong kong kitchen": (47.5983, -122.3243),  # A+ HK Restaurant, 667 S King St
    "a+ hong kong restaurant|seattle": (47.5983, -122.3243),  # display-name alias
    "shawarma king|seattle": (47.6679, -122.3131),  # 5241 University Way NE
    # "shawarma king|seattle" duplicate removed (already exists above)
    "hey! i am yog|seattle": (47.6569, -122.3142),  # 4106 Brooklyn Ave NE Suite 103A
    "panda yogurt|seattle": (47.6592, -122.3131),
    "cha yan|seattle": (47.6575, -122.3152),
    "chayan|seattle": (47.6575, -122.3152),  # Uber Eats display-name alias
    "snowy village - uw": (47.6682, -122.3128),  # Snowy Village, 5264 University Way NE
    "yomies rice &|seattle": (47.6610, -122.3131),  # Yomie's, U-District
    "plaza latina|shoreline": (47.7535, -122.3453),  # Plaza Latina, 17034 Aurora Ave N, Shoreline
    "u-district|seattle": (47.6615, -122.3131),
    "naan stop eat|seattle": (47.6626, -122.3135),  # Naan Stop, 4549 University Way NE
    "naan stop|seattle": (47.6626, -122.3135),
    "nextlevelburg|seattle": (47.6751, -122.3146),
    "poke dondon|seattle": (47.6636, -122.3162),  # 4712 11th Ave NE
    "burritos cali|seattle": (47.6632, -122.3131),
    "persepolis gr|seattle": (47.6691, -122.3133),  # Persepolis Grill, 5517 University Way NE
    "isarn thai kitchen|seattle": (47.6759, -122.3019),
    "little thai|seattle": (47.6580, -122.3150),  # Little Thai, 4142 Brooklyn Ave NE
    "george coffee & pastries|seattle": (47.6629, -122.3136),
    "muddy waters|seattle": (47.6633, -122.3156),  # Muddy Waters Coffee, 1116 NE 47th St
    "portage|seattle": (47.6576, -122.3177),

    # Post-override name matches (prefix-stripped names that don't match original keys)
    "dont yel|seattle": (47.6618, -122.3131),  # prefix-stripped "Tst* Dont Yel"
    "don't yell at me|seattle": (47.6618, -122.3131),  # display-name alias
    "cedars i|seattle": (47.6647, -122.3145),  # Cedars in U-District, 4759 Brooklyn Ave NE
    "cedars of lebanon|seattle": (47.6647, -122.3145),  # display-name alias
    "next lev|seattle": (47.6751, -122.3146),  # prefix-stripped "Tst* Next Lev"
    "einstein bros. bagels|seattle": (47.6613, -122.3005),

    # ===== SEATTLE, WA - Chinatown/International District =====
    "pho bac sup s|seattle": (47.5996, -122.3154),  # Pho Bac Sup Shop, 1240 S Jackson St
    "pho bac dt cd|seattle": (47.5970, -122.3230),  # Pho Bac DT
    "honey court s|seattle": (47.5978, -122.3228),  # Honey Court Seafood
    "fort st|seattle": (47.5982, -122.3262),
    "mee sum|seattle": (47.6610, -122.3134),  # Mee Sum, 4343 University Way NE (U-District)
    "grean|seattle": (47.6617, -122.3128),  # Grean Matcha, 4524 University Way NE (U-District)
    "letao|bellevue": (47.6161, -122.1933),  # LeTao, 700 110th Ave NE #195, Bellevue (The Bravern)
    "heytea|seattle": (47.6198, -122.3396),  # HeyTea (South Lake Union), 910 John St

    # ===== SEATTLE, WA - Capitol Hill / Central District =====
    "dick's drive|seattle": (47.6155, -122.3210),  # Dick's Drive-In Broadway
    "boon boona co|seattle": (47.6076, -122.3166),  # Boon Boona Coffee, 1223 E Cherry St
    "la carta de o|seattle": (47.6681, -122.3859),  # La Carta de Oaxaca, 5431 Ballard Ave NW
    "slurp station|seattle": (47.6633, -122.3146),  # Slurp Station, 4701 Brooklyn Ave NE (U-District)
    "coco fresh te|seattle": (47.6632, -122.3138),  # CoCo Bubble Tea, 4700 Brooklyn Ave NE (U-District)

    # ===== SEATTLE, WA - SoDo / Pioneer Square =====
    "paseo sodo|seattle": (47.5864, -122.3338),  # Paseo, 1760 1st Ave S (SoDo)

    # ===== SEATTLE, WA - Downtown / Belltown / Pike Place =====
    "sweetgreen so|seattle": (47.6166, -122.3376),  # Sweetgreen South Lake Union, 801 Lenora St
    "www.sweetgreen.com|seattle": (47.6166, -122.3376),
    "sweetgreen capitol hill|seattle": (47.6195, -122.3210),  # Sweetgreen Capitol Hill
    "wild cumin|kent": (47.4388, -122.2206),  # Wild Cumin, 18230 E Valley Hwy #126, Kent (Great Wall Mall)
    "ludi's restau|seattle": (47.6109, -122.3407),  # Ludi's, 120 Stewart St
    "hellenika cul|seattle": (47.6102, -122.3428),  # Hellenika, 1920a Pike Pl
    "red pepper|seattle": (47.6625, -122.3131),  # Red Pepper, 4545 University Way NE
    "maharaja|seattle": (47.6610, -122.2881),  # Maharaja Cuisine of India, 3701 NE 45th St

    # ===== SEATTLE, WA - Wallingford / Fremont / Ballard =====
    "hokkaido rame|seattle": (47.6615, -122.29750),  # Hokkaido Ramen
    "impeckable ch|seattle": (47.7323, -122.2930),  # Impeckable Chicken, 14307 Lake City Way NE
    "oh bear cafe|seattle": (47.6636, -122.3162),
    "ray's boathou|seattle": (47.6734, -122.4077),  # 6049 Seaview Ave NW, Shilshole

    # ===== SEATTLE, WA - Roosevelt / Northgate =====
    "ezells famous|seattle": (47.6063, -122.3031),  # Ezell's Famous Chicken, 501 23rd Ave
    "fainting goat|seattle": (47.6615, -122.3320),  # Fainting Goat Gelato, 2210 N 45th St (Wallingford)

    # ===== SEATTLE, WA - Beacon Hill / Columbia City / Rainier =====
    "carnitas mich|seattle": (47.5807, -122.3133),  # Carnitas Michoacan, 2500 Beacon Ave S (Beacon Hill)
    "taqueria la p|seattle": (47.7081, -122.3326),  # Taqueria La Pasadita, 2143 N Northgate Way
    "seattle buddh|seattle": (47.5997, -122.3132),  # Seattle Buddhist Temple, 1427 S Main St

    # ===== SEATTLE, WA - University Village / Ravenna =====

    # ===== SEATTLE, WA - Other Seattle locations =====
    "aladdin falaf|seattle": (47.6624, -122.3133),  # Aladdin Falafel Corner, 4541 University Way NE
    "myung dong to|seattle": (47.6582, -122.3141),  # Myung Dong Tofu, 4142 Brooklyn Ave NE
    "basil viet ki|seattle": (47.6554, -122.3132),  # Basil Viet Kitchen, 4002 University Way NE
    "gyro sababa s|seattle": (47.6634, -122.3177),  # Gyro Sababa, 4701 Roosevelt Way NE
    "itadakimasu 0|seattle": (47.6643, -122.3144),  # Itadakimasu, 4743 Brooklyn Ave NE
    "kais thai str|seattle": (47.6610, -122.3133),
    "hong kong bis|seattle": (47.5979, -122.3252),  # HK Bistro, 507 Maynard Ave S (Chinatown)
    "tres lecheria|seattle": (47.6612, -122.3306),  # Tres Lecheria, 2315 N 45th St (Wallingford)
    "jin huang (ki|seattle": (47.5985, -122.3215),  # Diamond Bay, 409 8th Ave S
    "diamond b|seattle": (47.5985, -122.3215),  # Diamond Bay alias
    "mcozy ca|seattle": (47.6633, -122.3012),
    "meetfresh chinatown|seattle": (47.5982, -122.3258),  # Meet Fresh, 659 S King St (Chinatown-ID)
    "uw seattle bean|seattle": (47.6558, -122.3081),  # Seattle Bean, UW campus
    "cafe on|seattle": (47.6586, -122.3131),  # Cafe On the Ave, U-District
    "kedai ma|seattle": (47.6648, -122.3131),  # Kedai Makan, U-District
    "taste of|seattle": (47.6691, -122.3176),  # Taste of India, 5517 Roosevelt Way NE
    "el camio|seattle": (47.6831, -122.3724),  # El Camion, Ballard
    "the curry club|seattle": (47.6615, -122.3131),  # The Curry Club (Uber Eats)
    "fusion feast pizza and cu|seattle": (47.6615, -122.3131),  # Fusion Feast
    "ding tea seat|seattle": (47.6638, -122.3133),  # Ding Tea, 4725 University Way NE
    "fob poke bar|seattle": (47.6140, -122.3421),  # FOB Poke Bar, 2101 4th Ave (Belltown)
    "eat and go th|seattle": (47.7206, -122.3446),  # Eat & Go Thai, 12534 Aurora Ave N
    "happy lemon|seattle": (47.6624, -122.2989),  # Happy Lemon U Village, 2630 NE Village Ln
    "spicy style r|seattle": (47.7247, -122.3438),  # Spicy Style of Sichuan, 13200 Aurora Ave N
    "than brothers|seattle": (47.6586, -122.3134),  # Than Brothers, 4207 University Way NE
    "mr. lu seafoo|seattle": (47.6646, -122.3129),  # Mr Lu's Burgers & Seafood, 4752 University Way NE
    "lin handmade|seattle": (47.6640, -122.3150),  # Lin Handmade, 4757 12th Ave NE (U-District)
    "mei mei cafe|seattle": (47.6650, -122.3177),  # Mei Mei Cafe, 1004 NE 50th St
    "la bise bakery|vancouver": (49.2727, -123.1352),  # La Bise Bakery, 1689 Johnston St, Vancouver BC
    "gaga tea|seattle": (47.5977, -122.3252),  # Gaga Tea, 523 Maynard Ave S (Chinatown)
    "mia and|kent": (47.4388, -122.2206),
    "ejae pak mor|seattle": (47.5978, -122.3280),  # E-Jae Pak Mor, 504 5th Ave S (Chinatown/ID)
    "panda noodle|seattle": (47.6618, -122.3131),  # Panda Noodle Bar, 4508 University Way NE
    "yumbit - harb|seattle": (47.6213, -122.3363),  # Yumbit, 333 Boren Ave N
    "shanghai|seattle": (47.5977, -122.3262),  # Shanghai Garden (post-prefix-strip name)
    "lil woodys sea|seattle": (47.6149, -122.3282),  # Lil Woody's Capitol Hill, 1211 Pine St
    "kanishka cuisine of|seattle": (47.5891, -122.3338),  # Kanishka, 1534 1st Ave S (SoDo)
    "albasha|seattle": (47.6136, -122.3466),  # Al Basha Mediterranean, 2302 1st Ave (Belltown)
    "seafood city|tukwila": (47.4598, -122.2561),  # Seafood City, 1368 Southcenter Mall, Tukwila
    "the edge skyomish|seattle": (47.7096, -121.3589),  # The Edge, 210 E Railroad Ave, Skykomish, WA
    "kuali|seattle": (47.6100, -122.3400),

    # ===== SEATTLE, WA - Various chains =====
    # (These are primary-location coords; chains with multiple locations are split below)
    "chick-fil-a|seattle": (47.7226, -122.3453),  # 12801 Aurora Ave N
    "subway|seattle": (47.6140, -122.3420),  # 305 Lenora St
    "taco del mar|seattle": (47.6158, -122.3344),  # 908 Stewart St
    "mcdonald's|seattle": (47.6155, -122.3260),
    "chipotle mexican grill|seattle": (47.6158, -122.3310),
    "jack in the b|seattle": (47.6648, -122.3134),  # Jack in the Box, 4749 University Way NE (permanently closed)
    # Split chains (Panda Express, Five Guys, Domino's, Dick's) handled below
    "panda express lake city|seattle": (47.7196, -122.2953),  # 12513 Lake City Way NE
    "panda express interbay|seattle": (47.6340, -122.3770),  # 1827 15th Ave W Suite A23
    "five guys northgate|seattle": (47.7030, -122.3230),  # 311 NE 103rd St
    "five guys shoreline|shoreline": (47.7423, -122.3483),  # 15515 Westminster Way N
    "domino's u-district|seattle": (47.6640, -122.3150),  # 4715 Brooklyn Ave NE
    "domino's west seattle|seattle": (47.5750, -122.3870),  # 3220 California Ave SW
    "dick's drive-in u-district|seattle": (47.6611, -122.3278),  # 111 NE 45th St
    "dick's drive-in capitol hill|seattle": (47.6193, -122.3212),  # 115 Broadway E

    # ===== SEATTLE, WA - food court / misc =====
    # Costco locations split across 4 stores
    "costco sodo|seattle": (47.5653, -122.3304),      # Costco SoDo, 4401 4th Ave S
    "costco shoreline|shoreline": (47.7751, -122.3452),  # Costco Shoreline, 1175 N 205th St
    "costco tukwila|tukwila": (47.4456, -122.2488),    # Costco Tukwila, 400 Costco Dr
    "costco kirkland|kirkland": (47.6807, -122.1817),   # Costco Kirkland, 8629 120th Ave NE
    "costco pharr|pharr, tx": (26.2270, -98.2070),       # Costco Pharr, TX
    "costco richmond|richmond, bc": (49.1931, -123.1218),  # Costco Richmond, BC (9151 Bridgeport Rd)
    "auntie anne's|bellevue": (47.6170, -122.2030),  # 575 Bellevue Square
    "ikea seatle rest|renton": (47.4424, -122.2286),  # IKEA Renton, 601 SW 41st St
    "ikea seatle|renton": (47.4424, -122.2286),

    # ===== BELLEVUE, WA =====
    "tres sandwich|bellevue": (47.6205, -122.1780),  # Tres Sandwich
    "molly tea (be|bellevue": (47.6114, -122.2019),  # Molly Tea, 103 Bellevue Way NE
    "i love sushi on lake|bellevue": (47.6145, -122.1920),  # I Love Sushi
    "zhangliang ma|bellevue": (47.6299, -122.1547),  # Zhangliang Malatang, 2221 140th Ave NE
    "so tasty 00-0|bellevue": (47.6173, -122.1279),  # So Tasty, 15920 NE 8th St #7 (Crossroads)
    "t&t supermark|bellevue": (47.6205, -122.1780),  # T&T Bellevue
    "t&t supermarket bellevue|bellevue": (47.6205, -122.1780),

    # ===== LYNNWOOD, WA =====
    "rinconcito pe|lynnwood": (47.8272, -122.3112),  # 18904 Hwy 99
    "t&t supermarket lynnwood|lynnwood": (47.8202, -122.3186),

    # ===== SHORELINE, WA =====
    "teriyaki isla|shoreline": (47.7560, -122.3450),

    # ===== EDMONDS, WA =====

    # ===== TUKWILA, WA =====
    "us 3036 tukwi|tukwila": (47.4740, -122.2590),  # H-Mart/Great Wall Mall area

    # ===== FORKS, WA =====
    "yabes food tr|forks": (47.9505, -124.3850),

    # ===== VANCOUVER, BC =====
    "toyokan 41305|vancouver": (49.2827, -123.1207),
    "cedar cafe|vancouver": (49.2820, -123.1200),
    "nirvana resta|vancouver": (49.2810, -123.1210),
    "van aqua-cour|vancouver": (49.3005, -123.1310),  # Vancouver Aquarium
    "van aqua-upst|vancouver": (49.3005, -123.1310),
    "taqueria jali|vancouver": (49.2590, -123.1020),
    "continental sausage co|vancouver": (49.2720, -123.1345),
    "van aqua-courtyard cafe|vancouver": (49.3005, -123.1310),
    "yvrwc pms|vancouver": (49.1947, -123.1817),  # The Westin Wall Centre, Vancouver Airport
    "tim hortons|vancouver": (49.2827, -123.1207),
    "university of british|vancouver": (49.2606, -123.2460),  # UBC
    "ginger indian cuisine|surrey": (49.1740, -122.8530),  # Richmond/Surrey area maybe
    "pizza pzazz vancouver bc|vancouver": (49.2130, -123.0120),
    "pizza pzazz|vancouver": (49.2130, -123.0120),

    # ===== RICHMOND, BC =====
    "oomomo aberde|richmond": (49.1815, -123.1370),  # Aberdeen Centre
    "castella rich|richmond": (49.1815, -123.1370),
    "t&t supermarket #026 richmond bc|richmond": (49.1815, -123.1370),

    # ===== LAS VEGAS, NV =====
    "in-n-out lv|las vegas": (36.1215, -115.1690),
    "the coffee be|las vegas": (36.1270, -115.1690),
    "sushi neko|las vegas": (36.1145, -115.1730),
    "tacos el gord|las vegas": (36.1695, -115.1500),
    "style pasifik|las vegas": (36.1230, -115.1700),

    # ===== SAN FRANCISCO BAY AREA =====
    "blue bottle c|san francisco": (37.7820, -122.4080),
    "sf chickenbox|san francisco": (37.7850, -122.4100),
    "affis marin g|san francisco": (37.7870, -122.4090),
    "www.sweetgree|los angeles": (47.6166, -122.3376),  # Actually Seattle Sweetgreen orders
    "dishdash 190 s. murp|sunnyvale": (37.3770, -122.0360),
    "nature's orga|sunnyvale": (37.3775, -122.0365),
    # "delightful|oakland" — removed, was SF/South Bay not Oakland
    "sabroso doggy|santa rosa": (37.7660, -122.5190),  # actually Sausalito area
    "sausalito swe|sausalito": (37.8590, -122.4850),
    "hotdogs|san francisco": (37.7850, -122.4090),  # SF trip, March 2025
    "kuali|san francisco": (37.7855, -122.4085),

    # ===== EDINBURG / MCALLEN / RGV, TX =====
    "texas roadhou|edinburg": (26.2500, -98.2060),
    "sip matcha ba|edinburg": (26.3018, -98.1638),
    "rodriguez mex|mcallen": (26.2035, -98.2300),
    "ikea|mcallen": (26.2100, -98.2400),  # IKEA McAllen? Actually no IKEA there, this might be something else
    "la reyna bake|pharr": (26.1960, -98.1840),
    "tacos kissi|san juan": (26.1900, -98.1500),
    "in-n-out burg|windcrest": (29.5160, -98.3800),
    "raising cane's chicken fingers|edinburg": (26.2500, -98.2060),
    "the caffeine|edinburg": (26.3018, -98.1636),
    "sonic|edinburg": (26.3010, -98.1630),
    "siempre natural|edinburg": (26.3030, -98.1745),  # Siempre Natural, Edinburg, TX

    # ===== SAN ANTONIO, TX (Airport) =====
    "paradies laga|atlanta": (29.5337, -98.4698),  # San Antonio Airport (SAT)

    # ===== LAKEWOOD, CO (actually Seattle) =====

    # ===== MORRISVILLE, NC =====

    # ===== TOKYO, JAPAN =====

    # ===== BANGKOK, THAILAND =====
    "grab|bangkok": (13.7563, 100.5018),  # Various Grab food orders
    "hyatt regency|bangkok": (13.7440, 100.5400),  # Hyatt Regency Bangkok
    "the local by oamthon|bangkok": (13.7260, 100.4880),
    "moone|bangkok": (13.7460, 100.5350),  # Bangkok trip, Sep 2025
    "linepay *pf_line man wong|bangkok": (13.7500, 100.5200),

    # ===== INCHEON, SOUTH KOREA =====
    "robot kimbab|incheon": (37.4602, 126.4407),

    # ===== HONOLULU, HI =====

    # ===== WORK TRIPS =====
}

# City center fallback coordinates
CITY_CENTERS = {
    "seattle": (47.6062, -122.3321),
    "bellevue": (47.6101, -122.2015),
    "vancouver": (49.2827, -123.1207),
    "richmond": (49.1666, -123.1336),
    "tokyo": (35.6762, 139.6503),
    "bangkok": (13.7563, 100.5018),
    "edinburg": (26.3017, -98.1633),
    "mcallen": (26.2034, -98.2300),
    "las vegas": (36.1699, -115.1398),
    "san francisco": (37.7749, -122.4194),
    "san antonio": (29.4241, -98.4936),
    "unknown": (47.6062, -122.3321),  # Default to Seattle
}

###############################################################################
# FALSE POSITIVES TO EXCLUDE
###############################################################################
FALSE_POSITIVES = {
    'venmo', 'non-chase atm withdraw', 'withdrawal', 'uber cash',
    'alaska airlines', 'atm withdrawal', 'indigo park-reservatio',
    'zelle payment to juan', 'aplpay', 'palenque group',
    'costco wholesale',  # mixed grocery/food court - skip
    'delightful',  # unknown SF/South Bay restaurant, merchant registered as Oakland
    'uber eats',  # delivery service fees, not a restaurant
    "love's",  # gas station
    'exxonmobil',  # gas station
}

###############################################################################
# Step 1: Read CSV and filter dining transactions
###############################################################################
DATE_START = datetime(2025, 1, 1)
DATE_END = datetime(2026, 3, 4)
restaurants = []

with open('transactions.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Date filter
        try:
            txn_date = datetime.strptime(row['date'].strip(), '%Y-%m-%d')
        except (ValueError, KeyError):
            continue
        if txn_date < DATE_START or txn_date > DATE_END:
            continue
        name = row['name'].strip()
        category = row['category'].strip()
        amount = float(row['amount']) if row['amount'] else 0
        if amount <= 0:
            continue
        is_eatout = category == 'Eat out'
        if not is_eatout:
            continue
        restaurants.append({
            'date': row['date'],
            'name': name,
            'amount': amount,
            'category': category,
        })

###############################################################################
# Step 2: Parse merchant name and city
###############################################################################
def parse_merchant(raw_name):
    name = raw_name
    prefixes = ['Aplpay Tst* ', 'Aplpay Uep*', 'Aplpay Par*', 'Aplpay Se40679 ', 'Aplpay ']
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break
    city_patterns = [
        (r'seattle$', 'Seattle, WA'), (r'seattl$', 'Seattle, WA'),
        (r'bellevue$', 'Bellevue, WA'), (r'lynnwood$', 'Lynnwood, WA'),
        (r'shoreline$', 'Shoreline, WA'), (r'tukwila$', 'Tukwila, WA'),
        (r'edmonds$', 'Edmonds, WA'), (r'renton$', 'Renton, WA'),
        (r'forks$', 'Forks, WA'), (r'lakewood co$', 'Lakewood, CO'),
        (r'las vegas$', 'Las Vegas, NV'), (r'los angeles$', 'Los Angeles, CA'),
        (r'romeoville$', 'Romeoville, IL'), (r'san francisco$', 'San Francisco, CA'),
        (r'cupertino$', 'Cupertino, CA'), (r'sunnyvale$', 'Sunnyvale, CA'),
        (r'santa rosa$', 'Santa Rosa, CA'), (r'sausalito$', 'Sausalito, CA'),
        (r'oakland$', 'Oakland, CA'), (r'san antonio$', 'San Antonio, TX'),
        (r'san juan$', 'San Juan, TX'), (r'edinburg$', 'Edinburg, TX'),
        (r'pharr$', 'Pharr, TX'), (r'mcallen$', 'McAllen, TX'),
        (r'windcrest$', 'Windcrest, TX'), (r'wharton$', 'Wharton, TX'),
        (r'pearland$', 'Pearland, TX'), (r'brownsville$', 'Brownsville, TX'),
        (r'mercedes$', 'Mercedes, TX'), (r'atlanta$', 'Atlanta, GA'),
        (r'vancouver$', 'Vancouver, BC'), (r'richmond$', 'Richmond, BC'),
        (r'surrey$', 'Surrey, BC'), (r'arlington$', 'Arlington, WA'),
        (r'morrisville$', 'Morrisville, NC'),
        (r'tokyo jp$', 'Tokyo, Japan'), (r'tokyo$', 'Tokyo, Japan'),
        (r'bangkok th$', 'Bangkok, Thailand'), (r'bangkok$', 'Bangkok, Thailand'),
        (r'incheon$', 'Incheon, South Korea'), (r'honolulu$', 'Honolulu, HI'),
        (r'bellingham$', 'Bellingham, WA'),
    ]
    city = 'Unknown'
    for pattern, city_name in city_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            city = city_name
            name = name[:match.start()].strip()
            break
    name = re.sub(r'[\s\-,]+$', '', name)
    return name, city


# Deduplicate
unique = {}
for r in restaurants:
    clean_name, city = parse_merchant(r['name'])
    lower = clean_name.lower().strip()

    # Skip false positives
    if lower in FALSE_POSITIVES:
        continue

    # UW food services grouping
    if 'uw food servi' in r['name'].lower() or 'uw hfs' in r['name'].lower():
        city = 'Seattle, WA (UW Campus)'
        clean_name = 'Center Table'
    elif 'uw seattle be' in r['name'].lower():
        city = 'Seattle, WA (UW Campus)'
        clean_name = 'UW Seattle Bean'

    # Fix city for merchants whose bank data lacks a city suffix
    if city == 'Unknown':
        city_overrides = {
            # Seattle, WA
            'shawarma king': 'Seattle, WA',
            'panda yogurt': 'Seattle, WA',
            'cha yan': 'Seattle, WA',
            'u-district': 'Seattle, WA',
            'naan stop': 'Seattle, WA',
            'poke dondon': 'Seattle, WA',
            'isarn thai kitchen': 'Seattle, WA',
            'little thai': 'Seattle, WA',
            'george coffee & pastries': 'Seattle, WA',
            'muddy waters': 'Seattle, WA',
            'muddy waters coffee comp': 'Seattle, WA',
            'portage': 'Seattle, WA',
            'einstein bros. bagels': 'Seattle, WA',
            'fort st': 'Seattle, WA',
            'mee sum': 'Seattle, WA',
            'grean': 'Seattle, WA',
            'heytea': 'Seattle, WA',
            'heytea south': 'Seattle, WA',
            "dick's drive": 'Seattle, WA',
            'paseo sodo': 'Seattle, WA',
            'www.sweetgreen.com': 'Seattle, WA',
            "ludi's restau": 'Seattle, WA',
            'red pepper': 'Seattle, WA',
            'oh bear cafe': 'Seattle, WA',
            "ray's boathou": 'Seattle, WA',
            'fob poke bar': 'Seattle, WA',
            'lin handmade': 'Seattle, WA',
            'mei mei cafe': 'Seattle, WA',
            'gaga tea': 'Seattle, WA',
            'ejae pak mor': 'Seattle, WA',
            'panda noodle': 'Seattle, WA',
            'shanghai': 'Seattle, WA',
            'lil woodys sea': 'Seattle, WA',
            'kanishka cuisine of': 'Seattle, WA',
            'albasha': 'Seattle, WA',
            'the edge skyomish': 'Seattle, WA',
            'kuali': 'Seattle, WA',
            'chick-fil-a': 'Seattle, WA',
            'subway': 'Seattle, WA',
            'taco del mar': 'Seattle, WA',
            "mcdonald's": 'Seattle, WA',
            'chipotle mexican grill': 'Seattle, WA',
            'cafe on': 'Seattle, WA',
            'snowy village - uw': 'Seattle, WA',
            # Bellevue / Renton / Kent / Tukwila, WA
            'letao': 'Bellevue, WA',
            "auntie anne's": 'Bellevue, WA',
            'ikea seatle rest': 'Renton, WA',
            'ikea seatle': 'Renton, WA',
            'wild cumin': 'Kent, WA',
            'mia and': 'Kent, WA',
            'seafood city': 'Tukwila, WA',
            # Shoreline, WA
            'plaza latina': 'Shoreline, WA',
            # Vancouver, BC
            'continental sausage co': 'Vancouver, BC',
            'van aqua-courtyard cafe': 'Vancouver, BC',
            'yvrwc pms': 'Vancouver, BC',
            'tim hortons': 'Vancouver, BC',
            'university of british': 'Vancouver, BC',
            'pizza pzazz': 'Vancouver, BC',
            'pizza pzazz vancouver bc': 'Vancouver, BC',
            'la bise bakery': 'Vancouver, BC',
            # Surrey, BC
            'ginger indian cuisine': 'Surrey, BC',
            # Richmond, BC
            't&t supermarket #026 richmond bc': 'Richmond, BC',
            # San Francisco, CA
            'hotdogs': 'San Francisco, CA',
            # Edinburg, TX
            "raising cane's chicken fingers": 'Edinburg, TX',
            'the caffeine': 'Edinburg, TX',
            'sonic': 'Edinburg, TX',
            'siempre': 'Edinburg, TX',
            'siempre natural': 'Edinburg, TX',
            # Bangkok, Thailand
            'moone': 'Bangkok, Thailand',
            'linepay *pf_line man wong': 'Bangkok, Thailand',
            # Unknown location
            'fusion feast pizza and cu': 'Seattle, WA',
        }
        if lower in city_overrides:
            city = city_overrides[lower]

    # Skip individual Costco entries — they'll be added manually below as split locations
    if lower == 'costco':
        continue

    # Skip chains that will be split into multiple locations below
    if lower in ('panda express', 'five guys', "dick's drive-in", "dick's drive", "domino's"):
        continue

    key = (clean_name.lower().strip(), city)
    if key not in unique:
        unique[key] = {'name': clean_name, 'city': city, 'count': 0, 'total': 0}
    unique[key]['count'] += 1
    unique[key]['total'] += r['amount']

# Clean up display names
NAME_OVERRIDES = {
    'www.sweetgree': 'Sweetgreen',
    'www.sweetgreen.com': 'Sweetgreen',
    'sweetgreen so': 'Sweetgreen',
    'aplus hong ko': 'A+ Hong Kong Restaurant',
    'hey! i am yog': 'Hey! I am Yogost',
    'dick\'s drive': 'Dick\'s Drive-In',
    'dont yel': "Don't Yell at Me",
    'fort st': 'Fort St. George',
    'tst* mee sum': 'Mee Sum Pastry',
    'mee sum': 'Mee Sum Pastry',
    "ray's boathou": "Ray's Boathouse",
    'los chil': 'Los Chilangos',
    'cedars i': 'Cedars of Lebanon',
    'el camio': 'El Camion',
    'taste of': 'Taste of India',
    'maharaja': 'Maharaja',
    'the mark': 'The Marke',
    'cafe on': 'Cafe On',
    'next lev': 'Next Level Burger',
    'snowy vi': 'Snowy Village',
    'kedai ma': 'Kedai Makan',
    'mcozy ca': 'MCozy Cafe',
    'ramen bo': 'Ramen Boy',
    "xi'an no": "Xi'an Noodles",
    'portage': 'Portage Bay Cafe',
    'el porte': 'El Porteño',
    'sweet pa': 'Sweet Paris',
    'taco pal': 'Taco Palenque',
    'palenque': 'Taco Palenque',
    'siempre': 'Siempre Natural',
    'taqueria': 'Taqueria',
    "rudy's c": "Rudy's Country Store",
    'reserva': 'Reserva',
    'rossina': 'Rossina',
    'mercurys': "Mercury's",
    'diamond b': 'Diamond Bay',
    'shanghai': 'Shanghai Garden',
    'einsteinbros_': 'Einstein Bros. Bagels',
    'hokkaido rame': 'Hokkaido Ramen Santouka',
}
for key in unique:
    lower = unique[key]['name'].lower()
    for pattern, override in NAME_OVERRIDES.items():
        if lower == pattern or lower.startswith(pattern):
            unique[key]['name'] = override
            break

# Add Uber Eats restaurants
uber_eats = [
    ('Panda Yogurt UW', 'Seattle, WA (U-District)', 3),
    ('Panda Yogurt Chinatown', 'Seattle, WA (Chinatown)', 20),
    ('CHAYAN', 'Seattle, WA (U-District)', 1),
    ('Taco Palenque (Uber)', 'Edinburg, TX', 2),
    ('Shawarma King (Uber)', 'Seattle, WA (U-District)', 4),
    ('The Curry Club', 'Seattle, WA', 1),
    ('Hey! I am Yogost (Uber)', 'Seattle, WA (U-District)', 3),
    ('Meetfresh Chinatown', 'Seattle, WA (Chinatown)', 4),
    ('Meetfresh Bellevue', 'Bellevue, WA', 1),
]
for name, city, count in uber_eats:
    key = (name.lower(), city)
    if key not in unique:
        unique[key] = {'name': name, 'city': city, 'count': count, 'total': 0}
    else:
        unique[key]['count'] += count

# Add Costco locations split across 6 stores (26 total visits, $170.13 total)
costco_locations = [
    ('Costco SoDo', 'Seattle, WA (SoDo)', 8, 52.34),
    ('Costco Shoreline', 'Shoreline, WA', 6, 39.26),
    ('Costco Tukwila', 'Tukwila, WA', 4, 26.18),
    ('Costco Kirkland', 'Kirkland, WA', 4, 26.18),
    ('Costco Pharr', 'Pharr, TX', 2, 13.09),
    ('Costco Richmond', 'Richmond, BC', 2, 13.08),
]
for name, city, count, total in costco_locations:
    key = (name.lower(), city)
    unique[key] = {'name': name, 'city': city, 'count': count, 'total': total}

# Consolidate all Sweetgreen visits into Seattle, then split 2 to Capitol Hill
sg_total_count = 0
sg_total_spent = 0
sg_keys_to_remove = []
for key, info in unique.items():
    if info['name'].lower().startswith('sweetgreen') or info['name'].lower().startswith('www.sweetgre'):
        sg_total_count += info['count']
        sg_total_spent += info['total']
        sg_keys_to_remove.append(key)
for k in sg_keys_to_remove:
    del unique[k]
# 2 visits at Capitol Hill, rest at SLU
sg_cap_hill_count = 2
sg_cap_hill_total = round(sg_total_spent * (2 / max(sg_total_count, 1)), 2)
sg_slu_count = sg_total_count - sg_cap_hill_count
sg_slu_total = round(sg_total_spent - sg_cap_hill_total, 2)
unique[('sweetgreen', 'Seattle, WA (SLU)')] = {'name': 'Sweetgreen', 'city': 'Seattle, WA (SLU)', 'count': sg_slu_count, 'total': sg_slu_total}
unique[('sweetgreen cap hill', 'Seattle, WA (Capitol Hill)')] = {'name': 'Sweetgreen Capitol Hill', 'city': 'Seattle, WA (Capitol Hill)', 'count': sg_cap_hill_count, 'total': sg_cap_hill_total}

# Split Panda Express by date: after 06/2025 → Lake City, before → Interbay
pe_lake_city = {'name': 'Panda Express (Lake City)', 'city': 'Seattle, WA (Lake City)', 'count': 0, 'total': 0}
pe_interbay = {'name': 'Panda Express (Interbay)', 'city': 'Seattle, WA (Interbay)', 'count': 0, 'total': 0}
for r in restaurants:
    clean, city = parse_merchant(r['name'])
    if clean.lower() == 'panda express':
        txn_date = datetime.strptime(r['date'], '%Y-%m-%d')
        if txn_date >= datetime(2025, 7, 1):
            pe_lake_city['count'] += 1
            pe_lake_city['total'] += r['amount']
        else:
            pe_interbay['count'] += 1
            pe_interbay['total'] += r['amount']
if pe_lake_city['count'] > 0:
    unique[('panda express lake city', 'Seattle, WA (Lake City)')] = pe_lake_city
if pe_interbay['count'] > 0:
    unique[('panda express interbay', 'Seattle, WA (Interbay)')] = pe_interbay

# Split Five Guys: 1 at Shoreline, rest at Northgate (311 NE 103rd St)
fg_total_count = 0
fg_total_spent = 0
for r in restaurants:
    clean, city = parse_merchant(r['name'])
    if clean.lower() == 'five guys':
        fg_total_count += 1
        fg_total_spent += r['amount']
fg_shoreline_count = 1
fg_shoreline_total = round(fg_total_spent / max(fg_total_count, 1), 2)
fg_northgate_count = fg_total_count - fg_shoreline_count
fg_northgate_total = round(fg_total_spent - fg_shoreline_total, 2)
unique[('five guys northgate', 'Seattle, WA (Northgate)')] = {'name': 'Five Guys (Northgate)', 'city': 'Seattle, WA (Northgate)', 'count': fg_northgate_count, 'total': fg_northgate_total}
unique[('five guys shoreline', 'Shoreline, WA')] = {'name': 'Five Guys (Shoreline)', 'city': 'Shoreline, WA', 'count': fg_shoreline_count, 'total': fg_shoreline_total}

# Split Dick's Drive-In: last 3 at U-District (111 NE 45th), rest at Capitol Hill (115 Broadway E)
dk_total_count = 0
dk_total_spent = 0
for r in restaurants:
    clean, city = parse_merchant(r['name'])
    if clean.lower().startswith("dick's drive"):
        dk_total_count += 1
        dk_total_spent += r['amount']
dk_udist_count = 3
dk_udist_total = round(dk_total_spent * (3 / max(dk_total_count, 1)), 2)
dk_caphill_count = dk_total_count - dk_udist_count
dk_caphill_total = round(dk_total_spent - dk_udist_total, 2)
unique[("dick's drive-in u-district", 'Seattle, WA (U-District)')] = {'name': "Dick's Drive-In (U-District)", 'city': 'Seattle, WA (U-District)', 'count': dk_udist_count, 'total': dk_udist_total}
unique[("dick's drive-in capitol hill", 'Seattle, WA (Capitol Hill)')] = {'name': "Dick's Drive-In (Capitol Hill)", 'city': 'Seattle, WA (Capitol Hill)', 'count': dk_caphill_count, 'total': dk_caphill_total}

# Split Domino's: first 2 at U-District (4715 Brooklyn Ave NE), last 1 at West Seattle (3220 California Ave SW)
dm_total_count = 0
dm_total_spent = 0
for r in restaurants:
    clean, city = parse_merchant(r['name'])
    if clean.lower() == "domino's":
        dm_total_count += 1
        dm_total_spent += r['amount']
dm_west_seattle_count = 1
dm_west_seattle_total = round(dm_total_spent / max(dm_total_count, 1), 2)
dm_udist_count = dm_total_count - dm_west_seattle_count
dm_udist_total = round(dm_total_spent - dm_west_seattle_total, 2)
unique[("domino's u-district", 'Seattle, WA (U-District)')] = {'name': "Domino's (U-District)", 'city': 'Seattle, WA (U-District)', 'count': dm_udist_count, 'total': dm_udist_total}
unique[("domino's west seattle", 'Seattle, WA (West Seattle)')] = {'name': "Domino's (West Seattle)", 'city': 'Seattle, WA (West Seattle)', 'count': dm_west_seattle_count, 'total': dm_west_seattle_total}

# Split T&T Supermarket: last 1 in Lynnwood, rest in Bellevue
tnt_keys = [k for k in unique if 't&t supermarket' in k[0] and k[1] == 'Unknown']
if tnt_keys:
    tnt_key = tnt_keys[0]
    tnt_info = unique[tnt_key]
    tnt_total_count = tnt_info['count']
    tnt_total_spent = tnt_info['total']
    del unique[tnt_key]
    tnt_lyn_count = 1
    tnt_lyn_total = round(tnt_total_spent / max(tnt_total_count, 1), 2)
    tnt_bel_count = tnt_total_count - tnt_lyn_count
    tnt_bel_total = round(tnt_total_spent - tnt_lyn_total, 2)
    unique[('t&t supermarket bellevue', 'Bellevue, WA')] = {'name': 'T&T Supermarket (Bellevue)', 'city': 'Bellevue, WA', 'count': tnt_bel_count, 'total': tnt_bel_total}
    unique[('t&t supermarket lynnwood', 'Lynnwood, WA')] = {'name': 'T&T Supermarket (Lynnwood)', 'city': 'Lynnwood, WA', 'count': tnt_lyn_count, 'total': tnt_lyn_total}

###############################################################################
# Step 3: Geocode - match to known coordinates
###############################################################################
def get_coords(name, city):
    name_lower = name.lower().strip()
    city_lower = city.lower()
    city_prefix = city_lower.split(',')[0]

    # Try exact match with city suffix
    key = f"{name_lower}|{city_prefix}"
    if key in KNOWN_COORDS:
        return KNOWN_COORDS[key]

    # Try with parenthesized suffixes removed and joined
    # e.g. "Panda Express (Lake City)" → "panda express lake city"
    paren_match = re.search(r'\(([^)]*)\)', name_lower)
    if paren_match:
        stripped = re.sub(r'\s*\([^)]*\)', '', name_lower).strip()
        joined = f"{stripped} {paren_match.group(1)}"
        key2 = f"{joined}|{city_prefix}"
        if key2 in KNOWN_COORDS:
            return KNOWN_COORDS[key2]

    # Try partial match
    for known_key, coords in KNOWN_COORDS.items():
        known_name = known_key.split('|')[0] if '|' in known_key else known_key
        if name_lower.startswith(known_name) or known_name.startswith(name_lower):
            return coords

    # Fallback to city center
    for city_key, coords in CITY_CENTERS.items():
        if city_key in city_lower:
            return coords

    return CITY_CENTERS.get('unknown', (47.6062, -122.3321))


geocoded = []
unmatched = []
for key, info in unique.items():
    coords = get_coords(info['name'], info['city'])
    if coords:
        dist = haversine_miles(HOME_LAT, HOME_LON, coords[0], coords[1])
        geocoded.append({
            'name': info['name'],
            'city': info['city'],
            'lat': coords[0],
            'lon': coords[1],
            'count': info['count'],
            'total': info['total'],
            'distance': round(dist, 1),
        })
    else:
        unmatched.append(info)

print(f"Geocoded: {len(geocoded)} restaurants")
if unmatched:
    print(f"Unmatched: {len(unmatched)}")
    for u in unmatched:
        print(f"  - {u['name']} ({u['city']})")

###############################################################################
# Step 4: Build Folium Heatmap
###############################################################################

import json

# JavaScript for the top-5 panel that updates on pan/zoom
def get_top5_js(restaurant_data):
    """Generate JS that shows top 5 restaurants in current map view."""
    js_data = json.dumps(restaurant_data)
    # Build per-visit dot data for "Dot Density" view
    dot_data = []
    for r in restaurant_data:
        for _ in range(r['count']):
            dot_data.append([r['lat'], r['lon']])
    js_dot_data = json.dumps(dot_data)
    return f"""
    <!-- Home overlay toggle -->
    <div id="home-toggle" style="position:fixed;top:15px;right:15px;z-index:9999;display:flex;align-items:center;gap:6px;background:rgba(255,255,255,0.92);border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.15);padding:6px 12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:12px;cursor:pointer;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);">
        <input type="checkbox" id="home-checkbox" style="cursor:pointer;accent-color:#6b5233;" />
        <label for="home-checkbox" style="cursor:pointer;color:#555;font-weight:500;">🏠 Home Base</label>
    </div>
    <style>
        /* Prevent tile blanking during zoom */
        .leaflet-tile-container {{
            will-change: transform;
        }}
        .leaflet-tile {{
            opacity: 1 !important;
            transition: opacity 0.15s ease-in;
        }}
        .leaflet-tile-loaded {{
            opacity: 1 !important;
        }}
        .leaflet-zoom-anim .leaflet-tile {{
            transition: none;
        }}
        .leaflet-fade-anim .leaflet-tile-container {{
            transition: opacity 0.2s;
        }}

        #top5-panel {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 9999;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 14px 18px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.2);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            max-width: 320px;
            line-height: 1.4;
        }}
        #top5-panel h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #333;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 6px;
        }}
        .top5-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 6px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            border-radius: 6px;
            transition: background 0.15s, transform 0.15s;
        }}
        .top5-item:hover {{
            background: #fef2f2;
            transform: translateX(2px);
        }}
        .top5-item:last-child {{ border-bottom: none; }}
        .top5-rank {{
            font-weight: 700;
            color: #e74c3c;
            width: 22px;
        }}
        .top5-name {{
            flex: 1;
            margin: 0 8px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .top5-stats {{
            text-align: right;
            color: #666;
            font-size: 12px;
            white-space: nowrap;
        }}
        .top5-count {{
            font-weight: 600;
            color: #333;
        }}
        #search-panel {{
            position: fixed;
            top: 60px;
            right: 15px;
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        #search-input {{
            width: 250px;
            padding: 10px 14px 10px 36px;
            border: none;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.2);
            font-size: 14px;
            outline: none;
            background: rgba(255,255,255,0.95) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E") no-repeat 12px center;
        }}
        #search-input::placeholder {{ color: #aaa; }}
        #search-results {{
            margin-top: 4px;
            background: rgba(255,255,255,0.97);
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            max-height: 300px;
            overflow-y: auto;
            display: none;
        }}
        .search-result-item {{
            padding: 10px 14px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
            font-size: 13px;
        }}
        .search-result-item:last-child {{ border-bottom: none; }}
        .search-result-item:hover {{ background: #f5f5f5; }}
        .search-result-name {{ font-weight: 600; color: #333; }}
        .search-result-info {{ color: #888; font-size: 12px; margin-top: 2px; }}

        /* View Switcher */
        #view-switcher {{
            position: fixed;
            top: 15px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            display: flex;
            gap: 0;
            background: rgba(255,255,255,0.92);
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 12px;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }}
        .view-btn {{
            padding: 8px 16px;
            cursor: pointer;
            border: none;
            background: transparent;
            color: #555;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
            border-right: 1px solid rgba(0,0,0,0.08);
            white-space: nowrap;
        }}
        .view-btn:last-child {{ border-right: none; }}
        .view-btn:hover {{ background: rgba(0,0,0,0.05); }}
        .view-btn.active {{
            background: #333;
            color: #fff;
            font-weight: 600;
        }}
        /* Dark mode overrides for panels */
        body.dark-view #top5-panel {{
            background: rgba(30, 30, 30, 0.92);
            color: #ddd;
            box-shadow: 0 2px 12px rgba(0,0,0,0.5);
        }}
        body.dark-view #top5-panel h3 {{ color: #eee; }}
        body.dark-view .top5-rank {{ color: #aaa; }}
        body.dark-view .top5-stats {{ color: #999; }}
        body.dark-view .top5-count {{ color: #ddd; }}
        body.dark-view .top5-item:hover {{ background: rgba(255,255,255,0.06); }}
        body.dark-view .top5-item {{ border-bottom-color: rgba(255,255,255,0.08); }}
        body.dark-view #search-input {{
            background-color: rgba(30,30,30,0.92);
            color: #eee;
            box-shadow: 0 2px 12px rgba(0,0,0,0.5);
        }}
        body.dark-view #search-results {{
            background: rgba(30,30,30,0.95);
        }}
        body.dark-view .search-result-item {{ border-bottom-color: rgba(255,255,255,0.08); }}
        body.dark-view .search-result-item:hover {{ background: rgba(255,255,255,0.06); }}
        body.dark-view .search-result-name {{ color: #eee; }}
        body.dark-view .search-result-info {{ color: #888; }}
        body.dark-view #view-switcher {{
            background: rgba(30,30,30,0.92);
        }}
        body.dark-view .view-btn {{ color: #aaa; border-right-color: rgba(255,255,255,0.08); }}
        body.dark-view .view-btn:hover {{ background: rgba(255,255,255,0.08); }}
        body.dark-view .view-btn.active {{ background: #e74c3c; color: #fff; }}
        body.dark-view #home-toggle {{
            background: rgba(30,30,30,0.92);
            box-shadow: 0 2px 12px rgba(0,0,0,0.5);
        }}
        body.dark-view #home-toggle label {{ color: #aaa; }}

        /* Default (fine dining) mode */
        body.default-view #top5-panel {{
            background: rgba(250,246,239,0.95);
            border: 1px solid #d4c5a9;
            box-shadow: 0 2px 12px rgba(107,82,51,0.15);
        }}
        body.default-view #top5-panel h3 {{
            color: #5a4632;
            font-style: italic;
            letter-spacing: 0.5px;
        }}
        body.default-view .top5-rank {{ color: #8b6f47; }}
        body.default-view .top5-name {{ color: #4a3728; }}
        body.default-view .top5-count {{ color: #5a4632; }}
        body.default-view .top5-stats {{ color: #8b7355; }}
        body.default-view .top5-item:hover {{ background: rgba(168,185,140,0.15); }}
        body.default-view .top5-item {{ border-bottom-color: #e8dfd0; }}
        body.default-view #search-input {{
            background-color: rgba(250,246,239,0.95);
            color: #4a3728;
            border: 1px solid #d4c5a9;
            box-shadow: 0 2px 12px rgba(107,82,51,0.15);
        }}
        body.default-view #search-results {{
            background: rgba(250,246,239,0.97);
            border: 1px solid #d4c5a9;
        }}
        body.default-view .search-result-item {{ border-bottom-color: #e8dfd0; }}
        body.default-view .search-result-item:hover {{ background: rgba(168,185,140,0.12); }}
        body.default-view .search-result-name {{ color: #4a3728; }}
        body.default-view .search-result-info {{ color: #8b7355; }}
        body.default-view #view-switcher {{
            background: rgba(250,246,239,0.95);
            border: 1px solid #d4c5a9;
        }}
        body.default-view .view-btn {{ color: #6b5233; border-right-color: #d4c5a9; }}
        body.default-view .view-btn:hover {{ background: rgba(168,185,140,0.15); }}
        body.default-view .view-btn.active {{ background: #6b5233; color: #faf6ef; }}
        body.default-view #home-toggle {{
            background: rgba(250,246,239,0.95);
            border: 1px solid #d4c5a9;
            box-shadow: 0 2px 12px rgba(107,82,51,0.15);
        }}
        body.default-view #home-toggle label {{ color: #6b5233; }}
    </style>
    <div id="search-panel">
        <input type="text" id="search-input" placeholder="Search restaurants..." autocomplete="off" />
        <div id="search-results"></div>
    </div>
    <div id="view-switcher">
        <button class="view-btn active" data-view="default">Default</button>
        <button class="view-btn" data-view="dark">Dark Neon</button>
    </div>
    <div id="top5-panel">
        <h3>🍽 Top 5 in View</h3>
        <div id="top5-list">Loading...</div>
    </div>
    <script>
        var allRestaurants = {js_data};
        var dotData = {js_dot_data};
        var homeLat = {HOME_LAT};
        var homeLon = {HOME_LON};
        var homeLayerGroup = null;

        // ---- View configurations ----
        var viewConfigs = {{
            dark: {{
                tiles: 'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
                attribution: '&copy; OpenStreetMap &copy; CARTO',
                heatGradient: {{0.15: '#001f3f', 0.3: '#0ff', 0.5: '#f0f', 0.75: '#ff0', 1.0: '#fff'}},
                heatRadius: 18, heatBlur: 14,
                dotColor: '#0ff', dotStroke: '#0aa', dotOpacity: 0.7, dotRadius: 3,
                dark: true, showHeat: true, showDots: false
            }},
            'default': {{
                tiles: 'https://{{s}}.basemaps.cartocdn.com/light_nolabels/{{z}}/{{x}}/{{y}}{{r}}.png',
                attribution: '&copy; OpenStreetMap &copy; CARTO',
                heatGradient: {{0.2: '#f5f0e8', 0.4: '#d4c5a9', 0.6: '#a8b98c', 0.8: '#7a9e5a', 1.0: '#4a6741'}},
                heatRadius: 18, heatBlur: 14,
                dotColor: '#3d6b4f', dotStroke: '#2d4f3a', dotOpacity: 0.7, dotRadius: 3,
                dark: false, showHeat: true, showDots: false,
                bodyBg: '#faf6ef'
            }}
        }};

        var currentTileLayer = null;
        var currentHeatLayer = null;
        var currentMarkerLayer = null;
        var currentView = localStorage.getItem('heatmapView') || 'default';
        var theMap = null;

        function toggleHomeOverlay(show) {{
            if (!theMap) return;
            if (show) {{
                if (homeLayerGroup) theMap.removeLayer(homeLayerGroup);
                homeLayerGroup = L.layerGroup().addTo(theMap);
                var cfg = viewConfigs[currentView];
                var ringColor = cfg.dark ? 'rgba(0,255,255,0.25)' : 'rgba(107,82,51,0.18)';
                var ringBorder = cfg.dark ? 'rgba(0,255,255,0.4)' : 'rgba(107,82,51,0.35)';
                var labelColor = cfg.dark ? '#0ff' : '#6b5233';
                var rings = [0.5, 1, 3, 5, 10];
                for (var i = 0; i < rings.length; i++) {{
                    var radiusMeters = rings[i] * 1609.34;
                    L.circle([homeLat, homeLon], {{
                        radius: radiusMeters,
                        color: ringBorder,
                        weight: 1,
                        fill: i === 0,
                        fillColor: ringColor,
                        fillOpacity: 0.08,
                        dashArray: '4 6'
                    }}).addTo(homeLayerGroup);
                    var labelLat = homeLat + (radiusMeters / 111320);
                    L.marker([labelLat, homeLon], {{
                        icon: L.divIcon({{
                            className: 'distance-label',
                            html: '<span style="font-size:10px;font-weight:600;color:' + labelColor + ';background:rgba(255,255,255,0.85);padding:1px 5px;border-radius:4px;white-space:nowrap;">' + rings[i] + ' mi</span>',
                            iconSize: [40, 14],
                            iconAnchor: [20, 7]
                        }})
                    }}).addTo(homeLayerGroup);
                }}
                L.marker([homeLat, homeLon], {{
                    icon: L.divIcon({{
                        className: 'home-icon',
                        html: '<div style="font-size:22px;text-shadow:0 1px 4px rgba(0,0,0,0.3);line-height:1;">&#127968;</div>',
                        iconSize: [28, 28],
                        iconAnchor: [14, 14]
                    }})
                }}).bindPopup('<b>Home Base</b><br>IRO Apartments<br>5233 15th Ave NE<br>Seattle, WA 98105').addTo(homeLayerGroup);
            }} else {{
                if (homeLayerGroup) {{
                    theMap.removeLayer(homeLayerGroup);
                    homeLayerGroup = null;
                }}
            }}
        }}

        document.getElementById('home-checkbox').addEventListener('change', function() {{
            toggleHomeOverlay(this.checked);
        }});

        function applyView(viewName, mapObj) {{
            var cfg = viewConfigs[viewName];
            if (!cfg || !mapObj) return;
            currentView = viewName;
            localStorage.setItem('heatmapView', viewName);

            // Update accent colors for current view
            var cfg = viewConfigs[currentView];
            var h3 = document.querySelector('#top5-panel h3');
            if (h3) h3.style.borderBottomColor = cfg.dotColor;
            document.querySelectorAll('.top5-rank').forEach(function(el) {{ el.style.color = cfg.dotColor; }});

            // Update button states
            document.querySelectorAll('.view-btn').forEach(function(b) {{
                b.classList.toggle('active', b.dataset.view === viewName);
            }});

            // Dark mode body class
            document.body.classList.remove('dark-view', 'default-view');
            if (cfg.dark) {{
                document.body.classList.add('dark-view');
            }} else if (viewName === 'default') {{
                document.body.classList.add('default-view');
            }}

            // Swap tiles
            if (currentTileLayer) mapObj.removeLayer(currentTileLayer);
            currentTileLayer = L.tileLayer(cfg.tiles, {{
                attribution: cfg.attribution,
                maxZoom: 19, subdomains: 'abcd',
                keepBuffer: 8,
                updateWhenZooming: false,
                updateWhenIdle: true
            }}).addTo(mapObj);

            // Remove old heat layer
            if (currentHeatLayer) mapObj.removeLayer(currentHeatLayer);
            currentHeatLayer = null;

            // Remove old markers
            if (currentMarkerLayer) mapObj.removeLayer(currentMarkerLayer);
            currentMarkerLayer = L.layerGroup().addTo(mapObj);

            // Add heatmap
            if (cfg.showHeat && cfg.heatGradient) {{
                var heatPoints = [];
                for (var i = 0; i < allRestaurants.length; i++) {{
                    var r = allRestaurants[i];
                    for (var j = 0; j < r.count; j++) {{
                        heatPoints.push([r.lat, r.lon]);
                    }}
                }}
                currentHeatLayer = L.heatLayer(heatPoints, {{
                    radius: cfg.heatRadius,
                    blur: cfg.heatBlur,
                    maxZoom: 13,
                    gradient: cfg.heatGradient
                }}).addTo(mapObj);
            }}

            // Add markers
            if (cfg.showDots) {{
                // Dot density: one dot per visit
                for (var i = 0; i < dotData.length; i++) {{
                    L.circleMarker(dotData[i], {{
                        radius: cfg.dotRadius,
                        color: cfg.dotStroke,
                        weight: 0.5,
                        fill: true,
                        fillColor: cfg.dotColor,
                        fillOpacity: cfg.dotOpacity
                    }}).addTo(currentMarkerLayer);
                }}
            }} else {{
                // Find max visit count for scaling
                var maxCount = 1;
                for (var i = 0; i < allRestaurants.length; i++) {{
                    if (allRestaurants[i].count > maxCount) maxCount = allRestaurants[i].count;
                }}

                // Restaurant markers scaled by visit density
                for (var i = 0; i < allRestaurants.length; i++) {{
                    var r = allRestaurants[i];
                    var ratio = r.count / maxCount;

                    // Scale radius: 3px (1 visit) → 12px (max visits)
                    var scaledRadius = 3 + ratio * 9;

                    // Scale opacity: 0.35 (1 visit) → 0.85 (max visits)
                    var scaledOpacity = 0.35 + ratio * 0.5;

                    var distText = r.distance > 0 ? '<br>Distance: ' + r.distance.toFixed(1) + ' mi from home' : '';
                    var popup = '<b>' + r.name + '</b><br>' + r.city + '<br>Visits: ' + r.count + '<br>Spent: $' + r.total.toFixed(2) + distText;
                    L.circleMarker([r.lat, r.lon], {{
                        radius: scaledRadius,
                        color: cfg.dotStroke,
                        weight: 0.5,
                        fill: true,
                        fillColor: cfg.dotColor,
                        fillOpacity: scaledOpacity
                    }}).bindPopup(popup).bindTooltip(r.name).addTo(currentMarkerLayer);
                }}
            }}

            // Re-render home overlay if active (so ring colors match new theme)
            var cb = document.getElementById('home-checkbox');
            if (cb && cb.checked) {{
                setTimeout(function() {{ toggleHomeOverlay(true); }}, 50);
            }}
        }}

        function updateTop5(mapObj) {{
            var bounds = mapObj.getBounds();
            var visible = allRestaurants.filter(function(r) {{
                return bounds.contains([r.lat, r.lon]);
            }});
            visible.sort(function(a, b) {{ return b.count - a.count; }});
            var top5 = visible.slice(0, 5);
            var html = '';
            if (top5.length === 0) {{
                html = '<div style="color:#999;padding:4px 0;">No restaurants in view</div>';
            }} else {{
                for (var i = 0; i < top5.length; i++) {{
                    var r = top5[i];
                    html += '<div class="top5-item" data-lat="' + r.lat + '" data-lon="' + r.lon + '" data-name="' + r.name + '" data-city="' + r.city + '" data-count="' + r.count + '" data-total="' + r.total.toFixed(0) + '">'
                        + '<span class="top5-rank">' + (i+1) + '.</span>'
                        + '<span class="top5-name" title="' + r.name + ' — ' + r.city + '">' + r.name + '</span>'
                        + '<span class="top5-stats"><span class="top5-count">' + r.count + 'x</span> · $' + r.total.toFixed(0) + (r.distance > 0 && r.distance < 100 ? ' · ' + r.distance.toFixed(1) + 'mi' : '') + '</span>'
                        + '</div>';
                }}
            }}
            var total = visible.reduce(function(s, r) {{ return s + r.count; }}, 0);
            html += '<div style="margin-top:8px;font-size:11px;color:#999;">'
                + visible.length + ' restaurants · ' + total + ' visits in view</div>';
            document.getElementById('top5-list').innerHTML = html;
        }}

        // Search functionality
        var searchInput = document.getElementById('search-input');
        var searchResults = document.getElementById('search-results');
        var searchMarker = null;

        searchInput.addEventListener('input', function() {{
            var query = this.value.toLowerCase().trim();
            if (query.length < 2) {{
                searchResults.style.display = 'none';
                return;
            }}
            var matches = allRestaurants.filter(function(r) {{
                return r.name.toLowerCase().indexOf(query) !== -1 || r.city.toLowerCase().indexOf(query) !== -1;
            }});
            matches.sort(function(a, b) {{ return b.count - a.count; }});
            matches = matches.slice(0, 8);
            if (matches.length === 0) {{
                searchResults.innerHTML = '<div class="search-result-item"><span style="color:#999">No results</span></div>';
            }} else {{
                var html = '';
                for (var i = 0; i < matches.length; i++) {{
                    var r = matches[i];
                    html += '<div class="search-result-item" data-lat="' + r.lat + '" data-lon="' + r.lon + '" data-name="' + r.name + '">'
                        + '<div class="search-result-name">' + r.name + '</div>'
                        + '<div class="search-result-info">' + r.city + ' · ' + r.count + ' visits · $' + r.total.toFixed(0) + '</div>'
                        + '</div>';
                }}
                searchResults.innerHTML = html;
            }}
            searchResults.style.display = 'block';
        }});

        searchResults.addEventListener('click', function(e) {{
            var item = e.target.closest('.search-result-item');
            if (!item) return;
            var lat = parseFloat(item.dataset.lat);
            var lon = parseFloat(item.dataset.lon);
            var name = item.dataset.name;

            // Find the map object
            var mapObj = null;
            for (var key in window) {{
                if (key.startsWith('map_') && window[key] && typeof window[key].getBounds === 'function') {{
                    mapObj = window[key]; break;
                }}
            }}
            if (!mapObj) return;

            // Pan to location, only zoom in if currently too far out
            var curZoom = mapObj.getZoom();
            var targetZoom = Math.max(curZoom, 14);
            mapObj.setView([lat, lon], targetZoom, {{ animate: true, duration: 0.5 }});

            // Subtle highlight
            if (searchMarker) mapObj.removeLayer(searchMarker);
            var cfg = viewConfigs[currentView];
            searchMarker = L.circleMarker([lat, lon], {{
                radius: 6, color: cfg.dotStroke, weight: 1, fillColor: cfg.dotColor, fillOpacity: 0.25
            }}).addTo(mapObj);
            searchMarker.bindPopup('<b>' + name + '</b>').openPopup();

            searchResults.style.display = 'none';
            searchInput.value = name;
        }});

        // Top 5 click-to-navigate

        document.getElementById('top5-list').addEventListener('click', function(e) {{
            var item = e.target.closest('.top5-item');
            if (!item) return;
            var lat = parseFloat(item.dataset.lat);
            var lon = parseFloat(item.dataset.lon);
            var name = item.dataset.name;
            if (isNaN(lat) || isNaN(lon)) return;

            var mapObj = null;
            for (var key in window) {{
                if (key.startsWith('map_') && window[key] && typeof window[key].getBounds === 'function') {{
                    mapObj = window[key]; break;
                }}
            }}
            if (!mapObj) return;

            // Pan to location, only zoom in if currently too far out
            var curZoom = mapObj.getZoom();
            var targetZoom = Math.max(curZoom, 14);
            mapObj.setView([lat, lon], targetZoom, {{ animate: true, duration: 0.5 }});

            if (searchMarker) mapObj.removeLayer(searchMarker);
            var cfg = viewConfigs[currentView];
            searchMarker = L.circleMarker([lat, lon], {{
                radius: 6, color: cfg.dotStroke, weight: 1, fillColor: cfg.dotColor, fillOpacity: 0.25
            }}).addTo(mapObj);
            searchMarker.bindPopup('<b>' + name + '</b> · ' + item.dataset.count + 'x · $' + item.dataset.total).openPopup();
        }});

        // View switcher click
        document.getElementById('view-switcher').addEventListener('click', function(e) {{
            var btn = e.target.closest('.view-btn');
            if (!btn) return;
            var viewName = btn.dataset.view;
            var mapObj = null;
            for (var key in window) {{
                if (key.startsWith('map_') && window[key] && typeof window[key].getBounds === 'function') {{
                    mapObj = window[key]; break;
                }}
            }}
            if (mapObj) applyView(viewName, mapObj);
        }});

        // Close search results on outside click
        document.addEventListener('click', function(e) {{
            if (!e.target.closest('#search-panel')) {{
                searchResults.style.display = 'none';
            }}
        }});

        // Find the Folium map object (it's named map_xxxxx)
        var checkMap = setInterval(function() {{
            var mapObj = null;
            for (var key in window) {{
                if (key.startsWith('map_') && window[key] && typeof window[key].getBounds === 'function') {{
                    mapObj = window[key];
                    break;
                }}
            }}
            if (mapObj) {{
                clearInterval(checkMap);

                // Use Leaflet's native scroll zoom with tuned speed
                // Native handles zoom-toward-cursor correctly without shifting
                mapObj.options.zoomSnap = 1;
                mapObj.options.wheelPxPerZoomLevel = 45;
                mapObj.options.wheelDebounceTime = 30;
                mapObj.options.zoomAnimation = true;
                mapObj.options.zoomAnimationThreshold = 4;

                // Smooth panning
                mapObj.options.inertia = true;
                mapObj.options.inertiaDeceleration = 3400;
                mapObj.options.inertiaMaxSpeed = 3000;
                mapObj.options.easeLinearity = 0.2;

                // Remove Folium's default tile layer, heatmap, and markers
                mapObj.eachLayer(function(layer) {{
                    if (layer._url || layer._heat || layer.options.radius !== undefined) {{
                        mapObj.removeLayer(layer);
                    }}
                }});

                // Apply saved or default view
                applyView(currentView, mapObj);

                mapObj.on('moveend', function() {{ updateTop5(mapObj); }});
                mapObj.on('zoomend', function() {{ updateTop5(mapObj); }});
                updateTop5(mapObj);

                theMap = mapObj;
            }}
        }}, 200);
    </script>
    """

# Prepare restaurant data for JS
def make_js_data(data):
    return [{'name': r['name'], 'city': r['city'], 'lat': r['lat'],
             'lon': r['lon'], 'count': r['count'], 'total': r['total'],
             'distance': r.get('distance', 0)} for r in data]

# ---- MAP 1: Global overview with markers ----
center_lat = sum(r['lat'] for r in geocoded) / len(geocoded)
center_lon = sum(r['lon'] for r in geocoded) / len(geocoded)

m = folium.Map(location=[center_lat, center_lon], zoom_start=4, tiles='CartoDB positron')

# Heatmap layer (weighted by visit count)
heat_data = []
for r in geocoded:
    for _ in range(r['count']):
        heat_data.append([r['lat'], r['lon']])

HeatMap(heat_data, radius=15, blur=10, max_zoom=13, name='Heatmap').add_to(m)

# Small dot markers — fixed pixel size, clean and minimal like Zillow
for r in geocoded:
    popup_text = f"<b>{r['name']}</b><br>{r['city']}<br>Visits: {r['count']}<br>Spent: ${r['total']:.2f}"
    folium.CircleMarker(
        location=[r['lat'], r['lon']],
        radius=3,
        color='#c0392b',
        weight=0.5,
        fill=True,
        fill_color='#e74c3c',
        fill_opacity=0.6,
        popup=folium.Popup(popup_text, max_width=250),
        tooltip=r['name'],
    ).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
# Hide base layer radio buttons, show only overlay checkboxes
m.get_root().html.add_child(folium.Element(
    '<style>'
    '.leaflet-control-layers-base { display: none !important; }'
    '.leaflet-control-layers { border: none !important; border-radius: 8px !important; padding: 8px 14px !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; font-size: 13px !important; }'
    'body.dark-view .leaflet-control-layers { background: rgba(30,30,30,0.92) !important; color: #ddd !important; box-shadow: 0 2px 12px rgba(0,0,0,0.5) !important; }'
    'body.default-view .leaflet-control-layers { background: rgba(250,246,239,0.95) !important; color: #4a3728 !important; box-shadow: 0 2px 12px rgba(107,82,51,0.15) !important; }'
    '</style>'
))

# Add top-5 panel
top5_html = get_top5_js(make_js_data(geocoded))
m.get_root().html.add_child(folium.Element(top5_html))

m.save('restaurant_heatmap.html')
print(f"\nSaved global heatmap: restaurant_heatmap.html")

# ---- MAP 2: Seattle area detail ----
m2 = folium.Map(location=[47.6200, -122.3210], zoom_start=13, tiles='CartoDB positron')

seattle_data = [r for r in geocoded if 46.5 < r['lat'] < 48.5 and -123.5 < r['lon'] < -121.5]
heat_seattle = []
for r in seattle_data:
    for _ in range(r['count']):
        heat_seattle.append([r['lat'], r['lon']])

HeatMap(heat_seattle, radius=18, blur=12, max_zoom=16, name='Heatmap').add_to(m2)

for r in seattle_data:
    popup_text = f"<b>{r['name']}</b><br>{r['city']}<br>Visits: {r['count']}<br>Spent: ${r['total']:.2f}"
    folium.CircleMarker(
        location=[r['lat'], r['lon']],
        radius=4,
        color='#c0392b',
        weight=0.5,
        fill=True,
        fill_color='#e74c3c',
        fill_opacity=0.6,
        popup=folium.Popup(popup_text, max_width=250),
        tooltip=r['name'],
    ).add_to(m2)

folium.LayerControl(collapsed=False).add_to(m2)
# Hide base layer radio buttons, show only overlay checkboxes
m2.get_root().html.add_child(folium.Element(
    '<style>'
    '.leaflet-control-layers-base { display: none !important; }'
    '.leaflet-control-layers { border: none !important; border-radius: 8px !important; padding: 8px 14px !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; font-size: 13px !important; }'
    'body.dark-view .leaflet-control-layers { background: rgba(30,30,30,0.92) !important; color: #ddd !important; box-shadow: 0 2px 12px rgba(0,0,0,0.5) !important; }'
    'body.default-view .leaflet-control-layers { background: rgba(250,246,239,0.95) !important; color: #4a3728 !important; box-shadow: 0 2px 12px rgba(107,82,51,0.15) !important; }'
    '</style>'
))

# Add top-5 panel
top5_html2 = get_top5_js(make_js_data(geocoded))
m2.get_root().html.add_child(folium.Element(top5_html2))

m2.save('restaurant_heatmap_seattle.html')
print(f"Saved Seattle heatmap: restaurant_heatmap_seattle.html")

# ---- Summary stats ----
total_visits = sum(r['count'] for r in geocoded)
total_spent = sum(r['total'] for r in geocoded)
cities = set(r['city'] for r in geocoded)
print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Total unique restaurants: {len(geocoded)}")
print(f"Total dining visits: {total_visits}")
print(f"Total spent on dining: ${total_spent:,.2f}")
print(f"Cities/regions: {len(cities)}")
print(f"\nTop 15 most visited:")
for r in sorted(geocoded, key=lambda x: -x['count'])[:15]:
    print(f"  {r['count']:3d}x  {r['name']:<35s} ({r['city']})")
print(f"\nTop 10 highest spend:")
for r in sorted(geocoded, key=lambda x: -x['total'])[:10]:
    print(f"  ${r['total']:8.2f}  {r['name']:<35s} ({r['city']})")
