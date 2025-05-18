from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import os
import webbrowser
import http.server
import socketserver
import re

from axe_analysis.run_axe import run_axe_analysis
from ia_correction.correct_html import correct_html, load_wcag_errors
from ia_correction.correct_css import correct_css
from fix_accessibility import fix_common_accessibility_issues
from extraer_imagenes import extraer_y_describir_imagenes_desde_driver


def find_best_match_and_replace(html, old_fragment, new_fragment, min_match_size=100):
    from difflib import SequenceMatcher
    matcher = SequenceMatcher(None, html, old_fragment)
    match = matcher.find_longest_match(0, len(html), 0, len(old_fragment))
    if match.size >= min_match_size:
        start, end = match.a, match.a + match.size
        return html[:start] + new_fragment + html[end:]
    return html


def replace_all_occurrences(text, old, new):
    return text.replace(old, new)


def open_browser_and_wait_for_url():
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    service = Service(executable_path='C:/Users/carla/PythonProject/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("about:blank")
    return driver


def wait_for_page_to_load(driver, timeout=120):
    print("Introduce la URL en el navegador que se ha abierto.")
    input("Cuando hayas introducido la URL, pulsa Enter aquí para empezar a esperar a que cargue...")

    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Página cargada completamente. Pulsa Enter para continuar con el análisis.")
    except Exception as e:
        print("⚠ Tiempo de espera agotado. La página puede no haberse cargado completamente.")

    input()


def is_css_fragment(fragment):
    # Detectar si un fragmento parece CSS: contiene propiedades CSS típicas con ':' y no contiene etiquetas HTML (<...>)
    if "<" in fragment and ">" in fragment:
        return False
    return bool(re.search(r"[a-zA-Z\-]+\s*:\s*[^;]+;", fragment))


def insertar_descripciones_en_html(html_str, descripciones):
    """
    Inserta justo debajo de cada <img> la descripción correspondiente en texto plano,
    y actualiza el atributo alt de la imagen.
    """
    soup = BeautifulSoup(html_str, "html.parser")

    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        nombre_archivo = os.path.basename(src)
        desc = descripciones.get(nombre_archivo, "FOTO")

        # Actualizar atributo alt
        img["alt"] = desc

        # Evitar duplicar la descripción si ya existe justo después
        siguiente = img.find_next_sibling()
        if siguiente and siguiente.name == "p" and siguiente.string == desc:
            continue

        # Crear y añadir párrafo con la descripción
        texto_desc = soup.new_tag("p")
        texto_desc.string = desc
        img.insert_after(texto_desc)

    return str(soup)


def main():
    errors_filepath = "wcag_errors.json"
    wcag_errors = load_wcag_errors(errors_filepath)

    driver = open_browser_and_wait_for_url()
    wait_for_page_to_load(driver)

    # Extraer y describir imágenes automáticamente desde el driver
    descripciones = extraer_y_describir_imagenes_desde_driver(driver)
    for ruta, desc in descripciones:
        print(f"{ruta} -> {desc[:100]}...")

    original_html = driver.page_source
    original_html = fix_common_accessibility_issues(original_html)

    violations = run_axe_analysis(driver)
    soup = BeautifulSoup(original_html, "html.parser")

    if not soup.head:
        head_tag = soup.new_tag("head")
        soup.html.insert(0, head_tag)
    if not soup.head.find("meta", charset=True):
        meta_tag = soup.new_tag("meta", charset="UTF-8")
        soup.head.insert(0, meta_tag)

    original_html = str(soup)
    not_corrected = []

    for violation in violations:
        error_id = violation.get('id') or violation.get('ruleId')

        if error_id in wcag_errors:
            error_entry = wcag_errors[error_id]
            description = error_entry.get("description", violation.get("description", ""))
            extra_prompt = error_entry.get("prompt", "")
        else:
            description = violation.get("description", "")
            extra_prompt = ""

        for node in violation.get('nodes', []):
            fragment = node.get('html', '')
            if not fragment or len(fragment.strip()) == 0:
                print("⚠ Fragmento inválido, se omite.")
                continue

            print(f"Corrigiendo fragmento con problema: {error_id} - {description}")

            if is_css_fragment(fragment):
                corrected_fragment = correct_css(fragment, description, extra_prompt)
                tipo = "CSS"
            else:
                corrected_fragment = correct_html(fragment, description, extra_prompt)
                tipo = "HTML"

            if corrected_fragment:
                if corrected_fragment == fragment:
                    print(f"ℹ Fragmento de tipo {tipo} ya cumplía con la norma, no se modifica.")
                    continue

                print(f"✅ Fragmento {tipo} corregido: {corrected_fragment[:200]}...")

                if fragment in original_html:
                    count = original_html.count(fragment)
                    original_html = replace_all_occurrences(original_html, fragment, corrected_fragment)
                    print(f"✅ Reemplazo exacto realizado {count} veces.")
                else:
                    updated_html = find_best_match_and_replace(original_html, fragment, corrected_fragment)
                    if updated_html != original_html:
                        print("✅ Reemplazo aproximado realizado con éxito.")
                        original_html = updated_html
                    else:
                        print(f"⚠ Fragmento {tipo} no encontrado ni siquiera de forma aproximada, se omite la corrección.")
                        not_corrected.append((description, fragment))
            else:
                print(f"⚠ No se recibió fragmento corregido del modelo para {tipo}.")
                not_corrected.append((description, fragment))

    # Crear carpeta para guardar resultado
    os.makedirs("html_resultado", exist_ok=True)

    original_path = os.path.join("html_resultado", "index_original.html")
    with open(original_path, "w", encoding="utf-8-sig") as f:
        f.write(driver.page_source)

    # Convertir lista de tuplas (ruta, desc) a diccionario {nombre_archivo: desc}
    descripciones_dict = {os.path.basename(ruta): desc for ruta, desc in descripciones}

    # Insertar descripciones debajo de las imágenes en el HTML corregido
    original_html = insertar_descripciones_en_html(original_html, descripciones_dict)

    corrected_path = os.path.join("html_resultado", "index_corregido.html")
    with open(corrected_path, "w", encoding="utf-8") as f:
        f.write(original_html)

    if not_corrected:
        with open("html_resultado/no_corregidos.txt", "w", encoding="utf-8") as log:
            for desc, frag in not_corrected:
                log.write(f"Descripción: {desc}\nFragmento:\n{frag}\n{'-'*40}\n")

    print(f"✅ HTML original guardado en {original_path}")
    print(f"✅ HTML corregido guardado en {corrected_path}")
    driver.quit()

    PORT = 8000
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory="html_resultado", **kwargs)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Servidor iniciado en http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}/index_corregido.html")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
