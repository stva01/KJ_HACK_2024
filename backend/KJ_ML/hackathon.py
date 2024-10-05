from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time
import concurrent.futures

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def scrape_with_requests(base_url, params):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(base_url, headers=headers, params=params)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    hackathons = []
    hackathon_tiles = soup.select('div.hackathon-tile')[:10]  # Adjust this number as needed

    for tile in hackathon_tiles:
        hackathon = {
            'title': tile.select_one('h3').text.strip() if tile.select_one('h3') else 'Title not found',
            'url': tile.select_one('a.tile-anchor')['href'] if tile.select_one('a.tile-anchor') else 'URL not found',
            'status': tile.select_one('div.status-label').text.strip() if tile.select_one('div.status-label') else 'Status not found',
            'location': tile.select_one('div.info-with-icon:nth-of-type(1) .info span').text.strip() if tile.select_one('div.info-with-icon:nth-of-type(1) .info span') else 'Location not found',
            'date': tile.select_one('div.submission-period').text.strip() if tile.select_one('div.submission-period') else 'Date not found',
            'prize': tile.select_one('div.prize').text.strip() if tile.select_one('div.prize') else 'Prize not specified',
            'participants': tile.select_one('div.participants strong').text.strip() if tile.select_one('div.participants strong') else 'Participants not specified',
            'themes': [theme.text.strip() for theme in tile.select('span.theme-label')] or ['No themes found'],
        }
        hackathons.append(hackathon)
    
    return hackathons


def scrape_with_selenium():
    url = "https://devpost.com/hackathons"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1200x600")  # Set window size to a lower resolution

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.hackathon-tile"))
        )
        
        hackathons = []
        hackathon_tiles = driver.find_elements(By.CSS_SELECTOR, "div.hackathon-tile")[:5]  # Reduce to 5
        
        for tile in hackathon_tiles:
            hackathon = {
                'title': tile.find_element(By.CSS_SELECTOR, "h3").text.strip(),
                'url': tile.find_element(By.CSS_SELECTOR, "a.tile-anchor").get_attribute("href"),
                'status': tile.find_element(By.CSS_SELECTOR, "div.status-label").text.strip(),
                'location': tile.find_element(By.CSS_SELECTOR, "div.info-with-icon:nth-of-type(1) .info span").text.strip(),
                'date': tile.find_element(By.CSS_SELECTOR, "div.submission-period").text.strip(),
                'prize': tile.find_element(By.CSS_SELECTOR, "div.prize").text.strip() if tile.find_elements(By.CSS_SELECTOR, "div.prize") else "Prize not specified",
                'participants': tile.find_element(By.CSS_SELECTOR, "div.participants strong").text.strip() if tile.find_elements(By.CSS_SELECTOR, "div.participants strong") else "Participants not specified",
                'themes': [theme.text.strip() for theme in tile.find_elements(By.CSS_SELECTOR, "span.theme-label")] or ["No themes found"],
            }
            hackathons.append(hackathon)
        
        return hackathons
    finally:
        driver.quit()

@app.route('/hackathons', methods=['GET'])
def get_hackathons():
    start_time = time.time()
    
    # Get URL parameters
    challenge_type = request.args.getlist('challenge_type[]')
    length = request.args.getlist('length[]')
    open_to = request.args.getlist('open_to[]')
    status = request.args.getlist('status[]')
    themes = request.args.getlist('themes[]')

    # Construct the URL with the received parameters
    base_url = "https://devpost.com/hackathons"
    params = {
        'challenge_type[]': challenge_type,
        'length[]': length,
        'open_to[]': open_to,
        'status[]': status,
        'themes[]': themes
    }
    
    try:
        hackathons = scrape_with_requests(base_url, params)
        if not hackathons:
            logging.info("Falling back to Selenium for scraping")
            hackathons = scrape_with_selenium()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        hackathons = []
    
    if not hackathons:
        logging.warning("No hackathons were scraped")
    
    end_time = time.time()
    logging.info(f"Scraping completed in {end_time - start_time:.2f} seconds")
    
    return jsonify(hackathons)


if __name__ == '__main__':
    app.run(debug=True)
