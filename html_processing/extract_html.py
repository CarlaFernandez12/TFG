from bs4 import BeautifulSoup
import requests

def extract_fragment(html_content, css_selector):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one(css_selector)
        return str(element) if element else None
    except Exception as e:
        return None

def get_html_from_url(url):
    try:
        response = requests.get(url)
        return response.text if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None
