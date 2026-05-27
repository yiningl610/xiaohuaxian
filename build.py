import json
from read_data import load_data, load_bag
from template import build_html

seed_rates, flower_sources, flower_times, flower_prices, flower_units, outfits, locations = load_data()
bag_flowers, bag_seeds = load_bag()

data_js = f"""
const SEED_RATES = {json.dumps(seed_rates, ensure_ascii=False)};
const FLOWER_SOURCES = {json.dumps(flower_sources, ensure_ascii=False)};
const FLOWER_TIMES = {json.dumps(flower_times, ensure_ascii=False)};
const FLOWER_PRICES = {json.dumps(flower_prices, ensure_ascii=False)};
const FLOWER_UNITS = {json.dumps(flower_units, ensure_ascii=False)};
const OUTFITS = {json.dumps(outfits, ensure_ascii=False, indent=2)};
const LOCATIONS = {json.dumps(locations, ensure_ascii=False, indent=2)};
const DEFAULT_BAG_FLOWERS = {json.dumps(bag_flowers, ensure_ascii=False)};
const DEFAULT_BAG_SEEDS = {json.dumps(bag_seeds, ensure_ascii=False)};
"""

with open("calculator.html", "w", encoding="utf-8") as f:
    f.write(build_html(data_js))

print("✅ 生成成功！打开 calculator.html 即可使用。")