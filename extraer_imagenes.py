import os
import requests
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI

def descargar_imagen(url, carpeta_destino, indice):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Obtener extensión de la URL o del header Content-Type
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower().replace('.', '')
        if not ext or ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            content_type = response.headers.get('Content-Type', '')
            if 'image/' in content_type:
                ext = content_type.split('/')[-1]
            else:
                ext = 'jpg'  # Fallback por defecto

        nombre_archivo = os.path.join(carpeta_destino, f"imagen_{indice}.{ext}")
        with open(nombre_archivo, "wb") as f:
            f.write(response.content)
        return nombre_archivo

    except Exception as e:
        print(f"❌ Error al descargar {url}: {e}")
        return None


def describir_imagen_openai(ruta_imagen):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ No se encontró la variable de entorno OPENAI_API_KEY.")
        return "API key no configurada"

    client = OpenAI(api_key=api_key)

    try:
        with open(ruta_imagen, "rb") as image_file:
            imagen_codificada = base64.b64encode(image_file.read()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe brevemente esta imagen en español."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{imagen_codificada}"}}
                    ]
                }
            ],
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ Error generando descripción para {ruta_imagen}: {e}")
        return "Descripción no disponible"


def extraer_y_describir_imagenes_desde_driver(driver):
    carpeta_img = "imagenes_descargadas"
    os.makedirs(carpeta_img, exist_ok=True)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    imgs = soup.find_all("img")
    urls = []

    url_pagina = driver.current_url

    for img in imgs:
        src = img.get("src")
        if not src:
            continue
        if src.startswith("data:"):
            print("⚠️ Imagen embebida en base64 detectada, se omite.")
            continue
        src = urljoin(url_pagina, src)
        urls.append(src)

    if not urls:
        print("⚠️ No se encontraron imágenes válidas en la página.")
        return []

    descripciones = []

    for i, img_url in enumerate(urls, 1):
        print(f"📥 Descargando imagen {i}/{len(urls)}: {img_url}")
        ruta = descargar_imagen(img_url, carpeta_img, i)
        if ruta:
            print(f"📝 Generando descripción para imagen {i}")
            desc = describir_imagen_openai(ruta)
            descripciones.append((ruta, desc))
        else:
            descripciones.append((img_url, "No se pudo descargar"))

    descripciones_path = os.path.join(carpeta_img, "descripciones.txt")
    with open(descripciones_path, "w", encoding="utf-8") as f:
        for ruta, desc in descripciones:
            f.write(f"Imagen: {ruta}\nDescripción:\n{desc}\n{'-'*40}\n")

    print(f"✅ Descripciones guardadas en: {descripciones_path}")
    return descripciones
