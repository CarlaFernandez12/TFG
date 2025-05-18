import os
import shutil
import re

# Rutas
html_path = "html_resultado/index_corregido.html"
imagenes_src = "imagenes_descargadas"
imagenes_dest = os.path.join("html_resultado", "imagenes_descargadas")

# Paso 1: Copiar imágenes si no existen ya
if not os.path.exists(imagenes_dest):
    shutil.copytree(imagenes_src, imagenes_dest)
    print(f"📁 Carpeta de imágenes copiada a: {imagenes_dest}")
else:
    print("✅ Carpeta de imágenes ya existe en html_resultado/")

# Paso 2: Reemplazar rutas en HTML
with open(html_path, "r", encoding="utf-8") as f:
    contenido = f.read()

# Expresión regular para encontrar imágenes externas
pattern = r'<img\s+[^>]*src="https?://[^"]+/(.+?\.(?:png|jpg|jpeg|gif|webp))"'
reemplazos = re.findall(pattern, contenido)

if reemplazos:
    for nombre_archivo in reemplazos:
        nueva_ruta = f'imagenes_descargadas/{nombre_archivo}'
        contenido = re.sub(
            rf'src="https?://[^"]*{nombre_archivo}"',
            f'src="{nueva_ruta}"',
            contenido
        )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(contenido)
    print("🛠️  Rutas de imágenes corregidas en el HTML.")
else:
    print("⚠️  No se encontraron rutas de imágenes externas para corregir.")
