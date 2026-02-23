"""
Take screenshots of the heatmap HTML files using headless Chrome.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Setup headless Chrome
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1400,900')
options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

driver = webdriver.Chrome(options=options)

data_dir = os.path.dirname(os.path.abspath(__file__))
screenshots_dir = os.path.join(data_dir, 'screenshots')
os.makedirs(screenshots_dir, exist_ok=True)

# Screenshot 1: Global heatmap
print("Capturing global heatmap...")
driver.get(f"file://{os.path.join(data_dir, 'restaurant_heatmap.html')}")
time.sleep(3)
driver.save_screenshot(os.path.join(screenshots_dir, 'global_heatmap.png'))
print("  Saved screenshots/global_heatmap.png")

# Screenshot 2: Seattle heatmap
print("Capturing Seattle heatmap...")
driver.get(f"file://{os.path.join(data_dir, 'restaurant_heatmap_seattle.html')}")
time.sleep(3)
driver.save_screenshot(os.path.join(screenshots_dir, 'seattle_heatmap.png'))
print("  Saved screenshots/seattle_heatmap.png")

driver.quit()
print("Done!")
