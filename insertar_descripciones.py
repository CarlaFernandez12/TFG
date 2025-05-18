from bs4 import BeautifulSoup
import os

html_input = "index_corregido.html"
html_output = "html_con_alt_y_descripcion.html"
descripciones_file = os.path.join("imagenes_descargadas", "descripciones.txt")

# Leer descripciones
descripciones = {}
with open(descripciones_file, "r", encoding="utf-8") as f:
    contenido = f.read().split("----------------------------------------")
    for bloque in contenido:
        if "Imagen:" in bloque and "Descripción:" in bloque:
            try:
                ruta = bloque.split("Imagen:")[1].split("\n")[0].strip().replace("\\", "/")
                desc = bloque.split("Descripción:")[1].strip()
                nombre_archivo = os.path.basename(ruta)
                descripciones[nombre_archivo] = desc
            except Exception as e:
                print(f"❌ Error procesando bloque:\n{bloque}\n{e}")

# Leer HTML original
with open(html_input, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

for img in soup.find_all("img"):
    src = img.get("src")
    if not src:
        continue
    nombre_archivo = os.path.basename(src)
    desc = descripciones.get(nombre_archivo, "FOTO")

    # Actualizar el atributo alt
    img["alt"] = desc

    # Eliminar párrafos <p> que ya contienen esta descripción justo después para evitar duplicados
    siguiente = img.find_next_sibling()
    if siguiente and siguiente.name == "p" and siguiente.string == desc:
        continue  # Ya está insertado, saltar

    # Crear etiqueta <p> con texto de descripción
    texto_desc = soup.new_tag("p")
    texto_desc.string = desc

    # Insertar el párrafo justo después de la imagen
    img.insert_after(texto_desc)

# Guardar HTML modificado
with open(html_output, "w", encoding="utf-8") as f:
    f.write(str(soup.prettify()))

print(f"✅ Archivo generado: {html_output}")
