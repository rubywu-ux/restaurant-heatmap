import csv
import re
from collections import defaultdict

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

        # Skip refunds / credits / negative amounts
        if amount <= 0:
            continue

        # Include if category is "Eat out"
        is_eatout = category == 'Eat out'

        # Also include known restaurant names that may be under "Other"
        known_restaurant_keywords = [
            'jollibee', 'chick-fil-a', 'red robin', 'whataburger', 'wendy',
            'mcdonald', 'taco bell', 'dairy queen', 'domino', 'subway',
            'panda express', 'five guys', 'raising cane', 'chipotle',
            'shake shack', 'in-n-out', 'jack in the b', 'sonic',
            'auntie anne', 'starbucks', 'tim horton', 'chick fil',
            'karakoram', 'jagerhof', 'celines fish', 'red pepper',
            'taco palenque', 'taco pal', 'texas roadhou', 'rudy',
            'dave\'s hot ch', 'sip matcha', 'siempre natur', 'reserva',
            'rossina', 'taqueria', 'la reyna', 'the caffeine',
            'rodriguez mex', 'sweet pa', 'pho houston', 'la taquiza',
            'palenque', 'shipley', 'buc-ee', 'quan binh',
            'gelatiamo', 'kau kau', 'lam seafood', 'cheesecake',
            'happy lamb', 'shinya shokud', 'xiao chi', 'mercurys',
            'ummadak', 'korean tofu', 'lighthouse ro', 'lees kitchen',
            'xi\'an no', 'jb-us tukwila', 'fob sushi', 'meet fresh',
            'district-h', 'cocoichibanya', 'yoshinoya', 'youmenyagoe',
            'kuuya', 'lukes omotesa', 'ol by oslo', 'cafe mugiwara',
            'robot kimbab', 'gourmet termi', 'local by oam',
            'costco wholesale', 'einstein bros', 'einsteinbros',
            'la cabana', 'hokkaido rame', 'wild cumin', 'mee sum',
            'los chil', 'fort st', 'the mark', 'honey court',
            'pho bac', 'la carta', 'slurp station', 'panda noodle',
            'boon boona', 'spicy style', 'carnitas mich', 'seattle buddh',
            'than brother', 'happy lemon', 'diamond b', 'uep*diamond',
            'el camio', 'maharaja', 'naan stop', 'eat and go',
            'nextlevelburg', 'mr. lu seafoo', 'cafe on', 'lin handmade',
            'poke dondon', 'taste of', 'dong tian', 'the bob',
            'la argentina', 'dont yel', 'mei mei cafe', 'myung dong',
            'basil viet', 'gyro sababa', 'itadakimasu',
            'shawarma stop', 'ncma cafe', 'pike&pine',
            'la farm bakery', 'portage', 'kedai ma',
            'fainting goat', 'ezells famous', 'mcozy ca',
            'grean', 'cha yan', 'letao', 'heytea',
            'sweetgreen', 'paseo sodo', 'paseo', 'fob poke',
            'pho bac dt', 'pho bac sup',
            'hellenika', 'sausalito swe', 'sabroso doggy',
            'hotdogs', 'delightful', 'el porte', 'blue bottle',
            'sf chickenbox', 'dishdash', 'kuali', 'affis marin',
            'nature\'s orga', 'lil woodys', '99 ranch mark',
            'aplus hong ko', 'a plus hong', 'shawarma king',
            'dick\'s drive', 'hey! i am yog', 'yomies rice',
            'plaza latina', 'burritos cali',
            'tres lecheria', 'tres sandwich', 'ejae pak',
            'kais thai', 'u-district', 'teriyaki isla',
            'hong kong bis', 'cedars i', 'the coffee be',
            'sushi neko', 'tacos el gord', 'in-n-out',
            'style pasifik', 'ramen bo',
            'zhangliang', 'rinconcito pe', 'molly tea',
            'uep*shanghai', 'toyokan', 'cedar cafe',
            'nirvana resta', 'continental sausage',
            'van aqua-courtyard', 'fusion feast',
            'bubble tea fr', 'tiger sugar',
            'kfc', 'la cocina', 'alibertos',
            'fuji bakery', 'yumbit', 'oh bear cafe',
            'don\'t yel', 'impeckable',
            'taqueria la p', 'taqueria la h', 'tacos kissi',
            'grab bangkok', 'the edge sky',
            'so tasty', 'jin huang', 'castella rich',
            'george coffee', 'popina foods', 'sunlight farm',
            'kaisereck', 'mui garden', 'big way hot',
            'macu tea', 'tutto belle', 'albasha',
            'seafood city', 'us 3036 tukwi', 'oomomo aberde',
            'taqueria jali', 'van aqua-upst', 'van aqua-cour',
            'pizza pzazz', 'la bise bakery',
            'yabes food', 'la mexican ga', 'chalma',
            'forks outfitt', 'happy lamb ho',
            'ludi\'s restau', 'sat 3894', 'sat 3893',
            'par*qargo', 'siempre', 'tst* reserva',
            'tst* rossina', 'tst* taco pal', 'tst* siempre',
            'sprouts farme', 'siren store',
            'uw seattle be', 'aladdin falaf',
            'uw food servi', 'little thai',
            'panda yogurt', 'ikea seatle rest', 'ikea mcallen',
        ]

        is_known = any(kw in name.lower() for kw in known_restaurant_keywords)

        if not is_eatout and not is_known:
            continue

        restaurants.append({
            'date': row['date'],
            'name': name,
            'amount': amount,
            'category': category,
        })

print(f"Total dining transactions found: {len(restaurants)}")

###############################################################################
# Step 2: Parse restaurant name and city from transaction name
###############################################################################

def parse_merchant(raw_name):
    """Extract clean restaurant name and city hint from transaction name."""
    name = raw_name

    # Remove common prefixes
    prefixes = ['Aplpay ', 'Aplpay Tst* ', 'Tst* ', 'Aplpay Uep*', 'Uep*',
                'Aplpay Par*', 'Aplpay Se40679 ']
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break

    # Known city suffixes that get concatenated to names
    city_patterns = [
        (r'seattle$', 'Seattle, WA'),
        (r'seattl$', 'Seattle, WA'),
        (r'bellevue$', 'Bellevue, WA'),
        (r'lynnwood$', 'Lynnwood, WA'),
        (r'shoreline$', 'Shoreline, WA'),
        (r'tukwila$', 'Tukwila, WA'),
        (r'edmonds$', 'Edmonds, WA'),
        (r'renton$', 'Renton, WA'),
        (r'forks$', 'Forks, WA'),
        (r'lakewood co$', 'Lakewood, CO'),
        (r'las vegas$', 'Las Vegas, NV'),
        (r'los angeles$', 'Los Angeles, CA'),
        (r'romeoville$', 'Romeoville, IL'),
        (r'san francisco$', 'San Francisco, CA'),
        (r'cupertino$', 'Cupertino, CA'),
        (r'sunnyvale$', 'Sunnyvale, CA'),
        (r'sausalito$', 'Sausalito, CA'),
        (r'santa rosa$', 'Santa Rosa, CA'),
        (r'oakland$', 'Oakland, CA'),
        (r'san antonio$', 'San Antonio, TX'),
        (r'san juan$', 'San Juan, TX'),
        (r'edinburg$', 'Edinburg, TX'),
        (r'pharr$', 'Pharr, TX'),
        (r'mcallen$', 'McAllen, TX'),
        (r'windcrest$', 'Windcrest, TX'),
        (r'wharton$', 'Wharton, TX'),
        (r'pearland$', 'Pearland, TX'),
        (r'brownsville$', 'Brownsville, TX'),
        (r'mercedes$', 'Mercedes, TX'),
        (r'atlanta$', 'Atlanta, GA'),
        (r'vancouver$', 'Vancouver, BC'),
        (r'richmond$', 'Richmond, BC'),
        (r'surrey$', 'Surrey, BC'),
        (r'arlington$', 'Arlington, WA'),
        (r'morrisville$', 'Morrisville, NC'),
        (r'tokyo jp$', 'Tokyo, Japan'),
        (r'tokyo$', 'Tokyo, Japan'),
        (r'bangkok th$', 'Bangkok, Thailand'),
        (r'bangkok$', 'Bangkok, Thailand'),
        (r'incheon$', 'Incheon, South Korea'),
        (r'honolulu$', 'Honolulu, HI'),
        (r'bellingham$', 'Bellingham, WA'),
    ]

    city = 'Unknown'
    for pattern, city_name in city_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            city = city_name
            name = name[:match.start()].strip()
            break

    # Clean up trailing whitespace, dashes, commas
    name = re.sub(r'[\s\-,]+$', '', name)

    return name, city


# Build unique restaurant list
unique_restaurants = {}  # key: (clean_name_lower, city) -> info

for r in restaurants:
    clean_name, city = parse_merchant(r['name'])

    # Manual city overrides for known places
    lower = clean_name.lower()
    if 'uw food servi' in r['name'].lower() or 'uw hfs' in r['name'].lower():
        city = 'Seattle, WA (UW Campus)'
        clean_name = re.sub(r'(Uw Food Servi|Uw Hfs).*', '', clean_name).strip() or 'UW Food Services'
    elif 'uw seattle be' in r['name'].lower():
        city = 'Seattle, WA (UW Campus)'
        clean_name = 'UW Seattle Bean'

    key = (clean_name.lower().strip(), city)
    if key not in unique_restaurants:
        unique_restaurants[key] = {
            'name': clean_name,
            'city': city,
            'count': 0,
            'total_spent': 0,
            'first_date': r['date'],
            'last_date': r['date'],
        }
    unique_restaurants[key]['count'] += 1
    unique_restaurants[key]['total_spent'] += r['amount']
    unique_restaurants[key]['last_date'] = r['date']

###############################################################################
# Step 3: Add Uber Eats restaurants
###############################################################################
uber_eats = [
    ('Panda Yogurt UW', 'Seattle, WA (U-District)', '4502 University Way NE, Seattle, WA 98105'),
    ('Panda Yogurt Chinatown', 'Seattle, WA (Chinatown)', '665 S King St, Seattle, WA 98104'),
    ('CHAYAN (茶颜悦色)', 'Seattle, WA (U-District)', 'University District, Seattle, WA'),
    ('Taco Palenque', 'Edinburg, TX', '3000 S McColl Rd, Edinburg, TX 78539'),
    ('Shawarma King', 'Seattle, WA (U-District)', '4515 University Way NE, Seattle, WA 98105'),
    ('The Curry Club', 'Seattle, WA', 'Seattle, WA'),
    ('Hey! I am Yogost', 'Seattle, WA (U-District)', '4507 University Way NE, Seattle, WA 98105'),
    ('Meetfresh Chinatown', 'Seattle, WA (Chinatown)', '659 S King St, Seattle, WA 98104'),
    ('Meetfresh Bellevue', 'Bellevue, WA', '15555 NE 24th St, Bellevue, WA 98007'),
]

for name, city, addr in uber_eats:
    key = (name.lower(), city)
    if key not in unique_restaurants:
        unique_restaurants[key] = {
            'name': name,
            'city': city,
            'count': 0,
            'total_spent': 0,
            'first_date': 'Uber Eats',
            'last_date': 'Uber Eats',
            'address_hint': addr,
        }

###############################################################################
# Step 4: Output sorted by city, then by visit count
###############################################################################
sorted_restaurants = sorted(unique_restaurants.values(),
                            key=lambda x: (x['city'], -x['count']))

print(f"\n{'='*90}")
print(f"UNIQUE RESTAURANTS: {len(sorted_restaurants)}")
print(f"{'='*90}\n")

current_city = None
idx = 0
for r in sorted_restaurants:
    if r['city'] != current_city:
        current_city = r['city']
        print(f"\n--- {current_city} ---")
    idx += 1
    addr = r.get('address_hint', '')
    addr_str = f"  [{addr}]" if addr else ''
    print(f"  {idx:3d}. {r['name']:<40s} | visits: {r['count']:3d} | ${r['total_spent']:8.2f} | {r['first_date']} - {r['last_date']}{addr_str}")

# Also write to CSV for easy review
with open('unique_restaurants.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['#', 'restaurant_name', 'city', 'visits', 'total_spent', 'first_date', 'last_date', 'address_hint'])
    for i, r in enumerate(sorted_restaurants, 1):
        writer.writerow([i, r['name'], r['city'], r['count'],
                         f"{r['total_spent']:.2f}", r['first_date'], r['last_date'],
                         r.get('address_hint', '')])

print(f"\n\nSaved to unique_restaurants.csv for review.")
print("Please review and add/correct addresses, then we'll geocode and build the heatmap.")
