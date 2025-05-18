from bs4 import BeautifulSoup

def replace_fragment(html, selector, corrected_html):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.select_one(selector)
        if element:
            new_element = BeautifulSoup(corrected_html, 'html.parser')
            element.replace_with(new_element)
        return str(soup)
    except Exception:
        return html
