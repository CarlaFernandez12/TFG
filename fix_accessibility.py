from bs4 import BeautifulSoup
import uuid

def fix_buttons_without_text(soup):
    buttons = soup.find_all("button")
    for btn in buttons:
        if not btn.get_text(strip=True):
            if not btn.has_attr("aria-label"):
                btn['aria-label'] = "Botón"
    return soup

def fix_inputs_without_label(soup):
    inputs = soup.find_all(['input', 'textarea', 'select'])
    for inp in inputs:
        if inp.name == 'input' and inp.get('type') in ['hidden', 'submit', 'button', 'reset']:
            continue
        label = None
        inp_id = inp.get('id')
        if inp_id:
            label = soup.find("label", attrs={"for": inp_id})
        if not label:
            if not inp.has_attr('aria-label'):
                inp['aria-label'] = "Campo de formulario"
    return soup

def fix_images_without_alt(soup):
    imgs = soup.find_all("img")
    for img in imgs:
        if not img.has_attr('alt') or not img['alt'].strip():
            img['alt'] = "Imagen"
    return soup

def fix_duplicate_ids(soup):
    ids = {}
    for tag in soup.find_all(attrs={"id": True}):
        id_val = tag['id']
        if id_val in ids:
            new_id = f"{id_val}-{uuid.uuid4().hex[:6]}"
            tag['id'] = new_id
        else:
            ids[id_val] = True
    return soup

def fix_links_without_text(soup):
    links = soup.find_all("a")
    for a in links:
        text = a.get_text(strip=True)
        imgs = a.find_all("img")
        if not text and imgs:
            for img in imgs:
                if not img.has_attr('alt') or not img['alt'].strip():
                    img['alt'] = "Imagen enlazada"
    return soup

def fix_nested_imgs(soup):
    """
    Busca imágenes anidadas dentro de otras imágenes y las saca fuera.
    Evita que existan etiquetas <img> anidadas.
    """
    imgs = soup.find_all("img")
    for img in imgs:
        nested_imgs = img.find_all("img")
        for nested_img in nested_imgs:
            # Mover la img anidada fuera, justo después del img padre
            img.insert_after(nested_img.extract())
    return soup

def fix_common_accessibility_issues(html):
    soup = BeautifulSoup(html, "html.parser")
    soup = fix_buttons_without_text(soup)
    soup = fix_inputs_without_label(soup)
    soup = fix_images_without_alt(soup)
    soup = fix_duplicate_ids(soup)
    soup = fix_links_without_text(soup)
    soup = fix_nested_imgs(soup)
    return str(soup)
