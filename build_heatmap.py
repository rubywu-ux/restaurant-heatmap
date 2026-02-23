"""
Restaurant Heatmap Generator
Reads transactions.csv + Uber Eats data, geocodes restaurants, builds Folium heatmap.
"""
import csv
import re
import folium
from folium.plugins import HeatMap

###############################################################################
# KNOWN RESTAURANT COORDINATES
# Manually curated from Google Maps for accuracy
###############################################################################
KNOWN_COORDS = {
    # ===== SEATTLE, WA - U-District / University Way =====
    "aplus hong ko|seattle": (47.6637, -122.3131),  # A+ Hong Kong Kitchen, 4715 University Way NE
    "aplus hong kong kitchen": (47.6637, -122.3131),
    "shawarma king|seattle": (47.6621, -122.3131),  # 4515 University Way NE
    "shawarma king|unknown": (47.6621, -122.3131),
    "shawarma king|u-district": (47.6621, -122.3131),
    "hey! i am yog|seattle": (47.6620, -122.3131),  # 4507 University Way NE
    "hey! i am yogost|u-district": (47.6620, -122.3131),
    "panda yogurt uw|u-district": (47.6615, -122.3131),  # 4502 University Way NE
    "panda yogurt|unknown": (47.6615, -122.3131),
    "chayan|u-district": (47.6625, -122.3131),  # U-District
    "cha yan|unknown": (47.6625, -122.3131),
    "uw food services|uw campus": (47.6553, -122.3035),  # UW Campus
    "uw seattle bean|uw campus": (47.6560, -122.3050),
    "tst* dont yel|seattle": (47.6618, -122.3131),  # Don't Yell At Me, U-District
    "snowy village - uw": (47.6612, -122.3131),  # U-District
    "tst* snowy vi|seattle": (47.6612, -122.3131),
    "yomies rice &|seattle": (47.6610, -122.3131),  # Yomie's, U-District
    "bubble tea fr|seattle": (47.6610, -122.3135),
    "tiger sugar s|seattle": (47.6608, -122.3131),
    "plaza latina|unknown": (47.6630, -122.3131),  # Plaza Latina, University Way
    "u-district|unknown": (47.6615, -122.3131),
    "naan stop eat|seattle": (47.6625, -122.3125),  # Naan Stop, U-District
    "naan stop|unknown": (47.6625, -122.3125),
    "tst* next lev|seattle": (47.6620, -122.3125),  # Next Level Burger
    "nextlevelburg|seattle": (47.6620, -122.3125),
    "poke dondon|unknown": (47.6618, -122.3128),
    "burritos cali|seattle": (47.6632, -122.3131),

    # ===== SEATTLE, WA - Chinatown/International District =====
    "panda yogurt chinatown|chinatown": (47.5982, -122.3226),  # 665 S King St
    "meetfresh chinatown|chinatown": (47.5980, -122.3226),  # 659 S King St
    "pho bac sup s|seattle": (47.5975, -122.3220),  # Pho Bac Sup Shop
    "pho bac dt cd|seattle": (47.5970, -122.3230),  # Pho Bac DT
    "pho bac dt 00|seattle": (47.5970, -122.3230),
    "kau kau bbq r|seattle": (47.5985, -122.3232),  # Kau Kau BBQ
    "honey court s|seattle": (47.5978, -122.3228),  # Honey Court Seafood
    "lam seafood m|seattle": (47.5976, -122.3223),
    "tai tung|seattle": (47.5982, -122.3230),
    "tst* fort st|unknown": (47.5980, -122.3235),  # Fort St. George
    "mee sum|unknown": (47.5980, -122.3225),  # Mee Sum Pastry
    "tst* mee sum|unknown": (47.5980, -122.3225),
    "grean|unknown": (47.5983, -122.3229),
    "letao|unknown": (47.5979, -122.3224),  # LeTao
    "heytea|unknown": (47.5981, -122.3227),  # HeyTea
    "heytea-us-wa|unknown": (47.5981, -122.3227),
    "heytea south|seattle": (47.5981, -122.3227),

    # ===== SEATTLE, WA - Capitol Hill / Central District =====
    "dick's drive|unknown": (47.6155, -122.3210),  # Dick's Drive-In Broadway
    "boon boona co|seattle": (47.6143, -122.3175),  # Boon Boona Coffee
    "la carta de o|seattle": (47.6140, -122.3190),
    "slurp station|seattle": (47.6145, -122.3200),
    "coco fresh te|seattle": (47.6150, -122.3185),

    # ===== SEATTLE, WA - SoDo / Pioneer Square =====
    "paseo sodo|unknown": (47.5810, -122.3340),  # Paseo SoDo
    "paseo sodo|seattle": (47.5810, -122.3340),

    # ===== SEATTLE, WA - Downtown / Belltown / Pike Place =====
    "sweetgreen so|seattle": (47.6100, -122.3400),  # Sweetgreen South Lake Union
    "sweetgreen|seattle": (47.6100, -122.3400),
    "sweetgreen|unknown": (47.6100, -122.3400),
    "sweetgreen|seattle, wa (slu)": (47.6100, -122.3400),
    "sweetgreen cap hill|seattle": (47.6155, -122.3210),  # Sweetgreen Capitol Hill
    "sweetgreen cap hill|seattle, wa (capitol hill)": (47.6155, -122.3210),
    "sweetgreen capitol hill|seattle, wa (capitol hill)": (47.6155, -122.3210),
    "www.sweetgreen.com|unknown": (47.6100, -122.3400),
    "wild cumin|unknown": (47.6140, -122.3440),
    "ludi's restau|unknown": (47.6070, -122.3340),  # Ludi's
    "hellenika cul|seattle": (47.6130, -122.3450),
    "tst* the mark|seattle": (47.6097, -122.3425),  # The Marke
    "red pepper|unknown": (47.6120, -122.3350),
    "tst* maharaja|seattle": (47.6115, -122.3432),
    "siren store 2|seattle": (47.6095, -122.3425),

    # ===== SEATTLE, WA - Wallingford / Fremont / Ballard =====
    "hokkaido rame|seattle": (47.6615, -122.29750),  # Hokkaido Ramen
    "impeckable ch|seattle": (47.6101, -122.3375),
    "oh bear cafe|seattle": (47.6520, -122.3500),

    # ===== SEATTLE, WA - Roosevelt / Northgate =====
    "ezells famous|seattle": (47.6730, -122.3170),  # Ezell's Famous Chicken
    "fainting goat|seattle": (47.6725, -122.3175),

    # ===== SEATTLE, WA - Beacon Hill / Columbia City / Rainier =====
    "tst* el camio|seattle": (47.5700, -122.3070),  # El Camion
    "carnitas mich|seattle": (47.5710, -122.3065),
    "taqueria la p|seattle": (47.5450, -122.2830),
    "seattle buddh|seattle": (47.5480, -122.2860),

    # ===== SEATTLE, WA - University Village / Ravenna =====
    "tst* cedars i|seattle": (47.6620, -122.2990),  # Cedars
    "tst* cafe on|seattle": (47.6615, -122.2985),

    # ===== SEATTLE, WA - Other Seattle locations =====
    "aladdin falaf|seattle": (47.6163, -122.3530),  # Aladdin Falafel Corner
    "tst* taste of|seattle": (47.6640, -122.3130),
    "myung dong to|seattle": (47.6160, -122.3540),  # Myung Dong Tofu
    "basil viet ki|seattle": (47.6640, -122.3127),
    "gyro sababa s|seattle": (47.6637, -122.3128),
    "itadakimasu 0|seattle": (47.6618, -122.3128),
    "kais thai str|seattle": (47.6610, -122.3133),
    "hong kong bis|seattle": (47.5980, -122.3222),  # HK Bistro, Chinatown
    "tres lecheria|seattle": (47.6161, -122.3300),
    "jin huang (ki|seattle": (47.5983, -122.3225),  # Diamond Bay / Jin Huang
    "uep*diamond b|seattle": (47.5983, -122.3225),
    "tst* mcozy ca|seattle": (47.6618, -122.3128),
    "ding tea seat|seattle": (47.6612, -122.3128),
    "tst* kedai ma|seattle": (47.6622, -122.3131),
    "fob poke bar|unknown": (47.6618, -122.3128),
    "fob sushi bar|seattle": (47.6617, -122.3128),
    "meet fresh|unknown": (47.5980, -122.3226),
    "eat and go th|seattle": (47.6065, -122.3340),
    "happy lemon|seattle": (47.6149, -122.3230),
    "spicy style r|seattle": (47.5982, -122.3228),
    "than brothers|seattle": (47.6640, -122.3133),
    "lighthouise ro|seattle": (47.6163, -122.3535),
    "lees kitchen|unknown": (47.6618, -122.3128),
    "the bob|unknown": (47.6637, -122.3128),
    "korean tofu h|seattle": (47.6155, -122.3530),
    "mr. lu seafoo|seattle": (47.5980, -122.3225),
    "lin handmade|unknown": (47.5978, -122.3225),
    "la argentina|unknown": (47.6155, -122.3200),
    "mei mei cafe|unknown": (47.6615, -122.3131),
    "la bise bakery|unknown": (47.5985, -122.3226),
    "gaga tea|unknown": (47.6156, -122.3200),
    "tst* mia and|unknown": (47.6618, -122.3128),
    "ejae pak mor|unknown": (47.6155, -122.3130),
    "panda noodle|unknown": (47.6155, -122.3540),
    "yumbit - harb|seattle": (47.6070, -122.3340),
    "happy lamb ho|seattle": (47.6160, -122.3460),  # Happy Lamb Hot Pot
    "shinya shokud|seattle": (47.6155, -122.3530),
    "la cabana 000|seattle": (47.5450, -122.2835),
    "kfc-tb #343 0|seattle": (47.6620, -122.3131),
    "alibertos sea|seattle": (47.6630, -122.3131),
    "tst* portage|unknown": (47.6075, -122.3340),
    "uep*shanghai|unknown": (47.6155, -122.3450),  # Shanghai Garden?
    "fusion feast pizza|unknown": (49.1815, -123.1370),  # 5300 No. 3 Rd, Richmond, BC
    "lil woodys sea|unknown": (47.6155, -122.3210),  # Lil Woody's
    "cheesecake se|seattle": (47.6130, -122.3370),  # Cheesecake Factory
    "red robin|unknown": (47.6160, -122.3480),
    "kanishka cuisine of|unknown": (47.6637, -122.3125),
    "the curry club|seattle": (47.6163, -122.3540),
    "dong tian|unknown": (47.5982, -122.3226),
    "snowy village|unknown": (47.6612, -122.3131),
    "xiao chi jie|unknown": (47.6160, -122.3460),
    "lil woodys|unknown": (47.6155, -122.3210),
    "kuali|unknown": (47.6100, -122.3400),
    "gelatiamo|unknown": (47.6160, -122.3380),
    "ummadak|unknown": (47.6617, -122.3128),
    "lighthouse ro|seattle": (47.6163, -122.3535),
    "fuji bakery|seattle": (47.5978, -122.3224),
    "tst* xi'an no|seattle": (47.6155, -122.3530),  # Xi'an Noodles
    "pho bac dt|seattle": (47.5970, -122.3230),

    # ===== SEATTLE, WA - Various chains =====
    "domino's|unknown": (47.6162, -122.3210),
    "five guys|unknown": (47.6155, -122.3200),
    "panda express|unknown": (47.6170, -122.3190),
    "chick-fil-a|unknown": (47.6160, -122.3330),
    "subway|unknown": (47.6150, -122.3300),
    "mcdonald's|unknown": (47.6155, -122.3260),
    "shake shack|unknown": (47.6148, -122.3340),
    "chipotle mexican grill|unknown": (47.6158, -122.3310),
    "jack in the b|seattle": (47.6640, -122.3136),
    "taco del mar|unknown": (47.6155, -122.3290),
    "starbucks|unknown": (47.6097, -122.3425),

    # ===== SEATTLE, WA - food court / misc =====
    # Costco locations split across 4 stores
    "costco sodo|unknown": (47.5632, -122.3293),      # Costco SoDo, Seattle
    "costco shoreline|unknown": (47.7783, -122.3285),  # Costco Shoreline
    "costco tukwila|unknown": (47.4740, -122.2590),    # Costco Tukwila
    "costco kirkland|unknown": (47.6960, -122.1780),   # Costco Kirkland
    "costco pharr|pharr, tx": (26.2270, -98.2070),       # Costco Pharr, TX
    "costco richmond|richmond, bc": (49.1930, -123.1370),  # Costco Richmond, BC (9151 Bridgeport Rd)
    "auntie anne's|unknown": (47.6140, -122.3370),
    "district-h|unknown": (47.6145, -122.3350),
    "ikea seatle rest|unknown": (47.4430, -122.2630),  # IKEA Renton
    "ikea seatle|unknown": (47.4430, -122.2630),

    # ===== BELLEVUE, WA =====
    "tst* los chil|bellevue": (47.6160, -122.1920),  # Los Chilangos
    "tres sandwich|bellevue": (47.6205, -122.1780),  # Tres Sandwich
    "molly tea (be|bellevue": (47.6150, -122.2000),
    "i love sushi on lake|bellevue": (47.6145, -122.1920),  # I Love Sushi
    "zhangliang ma|bellevue": (47.6150, -122.1900),
    "so tasty 00-0|bellevue": (47.6110, -122.2010),
    "t&t supermark|bellevue": (47.6205, -122.1780),  # T&T Bellevue
    "tst* mercurys|bellevue": (47.6130, -122.2050),
    "meetfresh bellevue|bellevue": (47.6310, -122.1410),  # Crossroads area
    "letao|bellevue": (47.6155, -122.2000),

    # ===== LYNNWOOD, WA =====
    "rinconcito pe|lynnwood": (47.8210, -122.3150),
    "t&t supermark|lynnwood": (47.8220, -122.3150),  # T&T Lynnwood
    "carniceria mi|lynnwood": (47.8205, -122.3155),

    # ===== SHORELINE, WA =====
    "teriyaki isla|shoreline": (47.7560, -122.3450),

    # ===== EDMONDS, WA =====
    "sp aquariumco|edmonds": (47.8115, -122.3840),

    # ===== TUKWILA, WA =====
    "us 3036 tukwi|tukwila": (47.4740, -122.2590),  # H-Mart/Great Wall Mall area
    "jb-us tukwila|tukwila": (47.4740, -122.2590),

    # ===== FORKS, WA =====
    "yabes food tr|forks": (47.9505, -124.3850),
    "la mexican ga|forks": (47.9500, -124.3853),
    "forks outfitt|forks": (47.9510, -124.3855),

    # ===== VANCOUVER, BC =====
    "toyokan 41305|vancouver": (49.2827, -123.1207),
    "cedar cafe|vancouver": (49.2820, -123.1200),
    "nirvana resta|vancouver": (49.2810, -123.1210),
    "van aqua-cour|vancouver": (49.3005, -123.1310),  # Vancouver Aquarium
    "van aqua-upst|vancouver": (49.3005, -123.1310),
    "taqueria jali|vancouver": (49.2590, -123.1020),
    "tutto belle i|vancouver": (49.2815, -123.1208),
    "kaisereck van|vancouver": (49.2825, -123.1212),
    "sunlight farm|vancouver": (49.2830, -123.1215),
    "popina foods|vancouver": (49.2720, -123.1340),  # Granville Island
    "continental sausage co|unknown": (49.2720, -123.1345),
    "van aqua-courtyard cafe|unknown": (49.3005, -123.1310),
    "tim hortons|unknown": (49.2827, -123.1207),
    "university of british|unknown": (49.2606, -123.2460),  # UBC
    "ginger indian cuisine|unknown": (49.1740, -122.8530),  # Richmond/Surrey area maybe
    "pizza pzazz vancouver bc|unknown": (49.2130, -123.0120),
    "pizza pzazz|unknown": (49.2130, -123.0120),

    # ===== RICHMOND, BC =====
    "oomomo aberde|richmond": (49.1815, -123.1370),  # Aberdeen Centre
    "castella rich|richmond": (49.1815, -123.1370),
    "mui garden|richmond": (49.1700, -123.1360),
    "macu tea rich|richmond": (49.1815, -123.1370),
    "big way hot p|richmond": (49.1710, -123.1360),
    "t&t supermarket #026 richmond bc|unknown": (49.1815, -123.1370),

    # ===== LAS VEGAS, NV =====
    "in-n-out lv|las vegas": (36.1215, -115.1690),
    "the coffee be|las vegas": (36.1270, -115.1690),
    "sushi neko|las vegas": (36.1145, -115.1730),
    "tacos el gord|las vegas": (36.1695, -115.1500),
    "style pasifik|las vegas": (36.1230, -115.1700),
    "tst* ramen bo|las vegas": (36.1200, -115.1720),

    # ===== SAN FRANCISCO BAY AREA =====
    "blue bottle c|san francisco": (37.7820, -122.4080),
    "tst* el porte|san francisco": (37.7960, -122.4070),  # El Porteño
    "sf chickenbox|san francisco": (37.7850, -122.4100),
    "affis marin g|san francisco": (37.7870, -122.4090),
    "www.sweetgree|los angeles": (47.6100, -122.3400),  # Actually Seattle Sweetgreen orders
    "dishdash 190 s. murp|sunnyvale": (37.3770, -122.0360),
    "nature's orga|sunnyvale": (37.3775, -122.0365),
    "99 ranch mark|cupertino": (37.3230, -122.0135),
    # "delightful|oakland" — removed, was SF/South Bay not Oakland
    "sabroso doggy|santa rosa": (37.7660, -122.5190),  # actually Sausalito area
    "sausalito swe|sausalito": (37.8590, -122.4850),
    "hotdogs|unknown": (37.7850, -122.4090),  # SF trip, March 2025
    "kuali|unknown": (37.7855, -122.4085),

    # ===== EDINBURG / MCALLEN / RGV, TX =====
    "tst* taco pal|edinburg": (26.3017, -98.1633),  # Taco Palenque
    "texas roadhou|edinburg": (26.2500, -98.2060),
    "la taquiza re|edinburg": (26.3020, -98.1636),
    "siempre natur|edinburg": (26.3020, -98.1640),
    "tst* taqueria|edinburg": (26.3010, -98.1630),
    "par*qargo cof|edinburg": (26.3015, -98.1635),
    "sip matcha ba|edinburg": (26.3018, -98.1638),
    "dave's hot ch|edinburg": (26.3016, -98.1632),
    "tst* palenque|edinburg": (26.3017, -98.1633),
    "taco palenque|edinburg": (26.3017, -98.1633),
    "rodriguez mex|mcallen": (26.2035, -98.2300),
    "tst* sweet pa|mcallen": (26.2030, -98.2305),
    "sprouts farme|mcallen": (26.2170, -98.2450),
    "ikea|mcallen": (26.2100, -98.2400),  # IKEA McAllen? Actually no IKEA there, this might be something else
    "pho houston 2|mcallen": (26.2050, -98.2310),
    "tst* rudy's c|pharr": (26.1970, -98.1850),  # Rudy's Country Store
    "la reyna bake|pharr": (26.1960, -98.1840),
    "tacos kissi|san juan": (26.1900, -98.1500),
    "taqueria la h|san juan": (26.1895, -98.1505),
    "tst* palenque|san juan": (26.1898, -98.1502),
    "tst* palenque|san antonio": (29.4241, -98.4936),
    "sat 3894 what|san antonio": (29.4600, -98.4500),  # Whataburger
    "sat 3893 smok|san antonio": (29.4600, -98.4510),
    "shipley do-nuts|brownsville": (25.9975, -97.4970),
    "buc-ee's 20-u|pearland": (29.5610, -95.3110),
    "buc-ee's|unknown": (29.5610, -95.3110),
    "buc-ee's #30|wharton": (29.3120, -96.1030),
    "in-n-out burg|windcrest": (29.5160, -98.3800),
    "whataburger|unknown": (26.3016, -98.1632),
    "raising cane's chicken fingers|unknown": (26.2500, -98.2060),
    "dairy queen|unknown": (26.3010, -98.1632),
    "tst* reserva|unknown": (26.3020, -98.1640),
    "tst* rossina|unknown": (26.3015, -98.1638),
    "tst* siempre|unknown": (26.3020, -98.1640),
    "the caffeine|unknown": (26.3018, -98.1636),
    "sonic|unknown": (26.3010, -98.1630),
    "la cocina oaxaqueña|unknown": (26.3020, -98.1635),

    # ===== SAN ANTONIO, TX (Airport) =====
    "paradies laga|atlanta": (29.5337, -98.4698),  # San Antonio Airport (SAT)

    # ===== LAKEWOOD, CO (actually Seattle) =====
    "einsteinbros_|lakewood": (47.6613, -122.3005),  # 2746 NE 45th St, Seattle, WA 98105

    # ===== MORRISVILLE, NC =====
    "shawarma stop|morrisville": (35.8235, -78.8256),

    # ===== TOKYO, JAPAN =====
    "cafe mugiwara|tokyo": (35.6600, 139.7040),  # One Piece themed cafe
    "cocoichibanya|tokyo": (35.6610, 139.7000),
    "youmenyagoemo|tokyo": (35.6615, 139.7010),
    "kuuya shibuya|tokyo": (35.6620, 139.7020),
    "lukes omotesa|tokyo": (35.6650, 139.7100),  # Luke's Lobster Omotesando
    "yoshinoya|tokyo": (35.6595, 139.7005),
    "ol by oslo br|tokyo": (35.6600, 139.7030),

    # ===== BANGKOK, THAILAND =====
    "grab|bangkok": (13.7563, 100.5018),  # Various Grab food orders
    "hyatt regency|bangkok": (13.7440, 100.5400),  # Hyatt Regency Bangkok
    "the local by oamthon|bangkok": (13.7260, 100.4880),
    "gourmet termi|bangkok": (13.6900, 100.7501),  # Suvarnabhumi area
    "moone|unknown": (13.7460, 100.5350),  # Bangkok trip, Sep 2025
    "linepay *pf_line man wong|unknown": (13.7500, 100.5200),

    # ===== INCHEON, SOUTH KOREA =====
    "robot kimbab|incheon": (37.4602, 126.4407),

    # ===== HONOLULU, HI =====
    "cnp mauka market|honolulu": (21.3320, -157.9200),
    "mauka market|honolulu": (21.3320, -157.9200),

    # ===== WORK TRIPS =====
    "shawarma stop|seattle": (35.8235, -78.8256),  # Actually Morrisville
    "ncma cafe - west|unknown": (35.8100, -78.6400),  # NC Museum of Art, Raleigh
    "pike&pine st|unknown": (35.8240, -78.8260),  # Morrisville/RTP area
    "la farm bakery & caf|unknown": (35.7900, -78.7810),  # La Farm Bakery, Cary NC
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
}

###############################################################################
# Step 1: Read CSV and filter dining transactions
###############################################################################
restaurants = []

with open('transactions.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['name'].strip()
        category = row['category'].strip()
        amount = float(row['amount']) if row['amount'] else 0
        if amount <= 0:
            continue
        is_eatout = category == 'Eat out'
        known_keywords = [
            'jollibee', 'chick-fil-a', 'red robin', 'whataburger', 'wendy',
            'mcdonald', 'taco bell', 'dairy queen', 'domino', 'subway',
            'panda express', 'five guys', 'raising cane', 'chipotle',
            'shake shack', 'in-n-out', 'jack in the b', 'sonic',
            'auntie anne', 'starbucks', 'tim horton',
            'taco palenque', 'texas roadhou',
            'einstein bros', 'einsteinbros',
        ]
        is_known = any(kw in name.lower() for kw in known_keywords)
        if not is_eatout and not is_known:
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
        clean_name = 'UW Food Services'
    elif 'uw seattle be' in r['name'].lower():
        city = 'Seattle, WA (UW Campus)'
        clean_name = 'UW Seattle Bean'

    # Skip individual Costco entries — they'll be added manually below as split locations
    if lower == 'costco':
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
    'aplus hong ko': 'A+ Hong Kong Kitchen',
    'hey! i am yog': 'Hey! I am Yogost',
    'dick\'s drive': 'Dick\'s Drive-In',
    'tst* dont yel': 'Don\'t Yell at Me',
    'tst* fort st': 'Fort St. George',
    'tst* mee sum': 'Mee Sum Pastry',
    'tst* los chil': 'Los Chilangos',
    'tst* cedars i': 'Cedars of Lebanon',
    'tst* el camio': 'El Camion',
    'tst* taste of': 'Taste of India',
    'tst* maharaja': 'Maharaja',
    'tst* the mark': 'The Marke',
    'tst* cafe on': 'Cafe On',
    'tst* next lev': 'Next Level Burger',
    'tst* snowy vi': 'Snowy Village',
    'tst* kedai ma': 'Kedai Makan',
    'tst* mcozy ca': 'MCozy Cafe',
    'tst* ramen bo': 'Ramen Boy',
    'tst* xi\'an no': 'Xi\'an Noodles',
    'tst* portage': 'Portage Bay Cafe',
    'tst* el porte': 'El Porteño',
    'tst* sweet pa': 'Sweet Paris',
    'tst* taco pal': 'Taco Palenque',
    'tst* palenque': 'Taco Palenque',
    'tst* siempre': 'Siempre Natural',
    'tst* taqueria': 'Taqueria',
    'tst* rudy\'s c': 'Rudy\'s Country Store',
    'tst* reserva': 'Reserva',
    'tst* rossina': 'Rossina',
    'tst* mercurys': 'Mercury\'s',
    'uep*diamond b': 'Diamond Bay',
    'uep*shanghai': 'Shanghai Garden',
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

###############################################################################
# Step 3: Geocode - match to known coordinates
###############################################################################
def get_coords(name, city):
    name_lower = name.lower().strip()
    city_lower = city.lower()

    # Try exact match with city suffix
    for city_hint in [city_lower.split(',')[0], 'unknown']:
        key = f"{name_lower}|{city_hint}"
        if key in KNOWN_COORDS:
            return KNOWN_COORDS[key]

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
        geocoded.append({
            'name': info['name'],
            'city': info['city'],
            'lat': coords[0],
            'lon': coords[1],
            'count': info['count'],
            'total': info['total'],
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
    <style>
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
            top: 15px;
            right: 60px;
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
                maxZoom: 19, subdomains: 'abcd'
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
                // Restaurant markers with popups
                for (var i = 0; i < allRestaurants.length; i++) {{
                    var r = allRestaurants[i];
                    var popup = '<b>' + r.name + '</b><br>' + r.city + '<br>Visits: ' + r.count + '<br>Spent: $' + r.total.toFixed(2);
                    L.circleMarker([r.lat, r.lon], {{
                        radius: cfg.dotRadius,
                        color: cfg.dotStroke,
                        weight: 0.5,
                        fill: true,
                        fillColor: cfg.dotColor,
                        fillOpacity: cfg.dotOpacity
                    }}).bindPopup(popup).bindTooltip(r.name).addTo(currentMarkerLayer);
                }}
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
                        + '<span class="top5-stats"><span class="top5-count">' + r.count + 'x</span> · $' + r.total.toFixed(0) + '</span>'
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

                // Google Maps-like smooth zoom & scroll
                mapObj.options.zoomSnap = 0.5;
                mapObj.options.zoomDelta = 1;
                mapObj.options.wheelPxPerZoomLevel = 30;
                mapObj.options.wheelDebounceTime = 0;
                mapObj.options.zoomAnimationThreshold = 4;
                mapObj.options.inertia = true;
                mapObj.options.inertiaDeceleration = 3400;
                mapObj.options.inertiaMaxSpeed = 3000;
                mapObj.options.easeLinearity = 0.2;
                mapObj.scrollWheelZoom.disable();
                mapObj.scrollWheelZoom.enable();

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
            }}
        }}, 200);
    </script>
    """

# Prepare restaurant data for JS
def make_js_data(data):
    return [{'name': r['name'], 'city': r['city'], 'lat': r['lat'],
             'lon': r['lon'], 'count': r['count'], 'total': r['total']} for r in data]

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

folium.LayerControl().add_to(m)

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

folium.LayerControl().add_to(m2)

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
