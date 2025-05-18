import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_wcag_errors(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

def is_valid_html(fragment):
    try:
        soup = BeautifulSoup(fragment, 'html.parser')
        return bool(soup.find())
    except Exception:
        return False

def clean_html(fragment):
    soup = BeautifulSoup(fragment, 'html.parser')
    if soup.body:
        content = ''.join(str(c) for c in soup.body.contents)
    else:
        content = str(soup)
    return content.strip()

def detect_nested_tags(html_fragment):
    soup = BeautifulSoup(html_fragment, "html.parser")

    def has_nested(tag):
        return bool(tag.find(tag.name))

    for tag in soup.find_all():
        if has_nested(tag):
            return True, tag.name
    return False, None

def correct_html(fragment, error_description, extra_prompt=""):
    fragment = fragment[:1500].encode("utf-8", errors="ignore").decode("utf-8")
    prompt = f"""
Corrige el siguiente fragmento HTML para que cumpla la norma WCAG 2.2 nivel A.
Haz SOLO los cambios necesarios, sin duplicar contenido ni anidar etiquetas innecesariamente.
Mantén el mismo formato y estructura.
NO añadas explicaciones ni textos adicionales.
Devuelve únicamente el fragmento HTML corregido, sin etiquetas <html> ni <body>.

Error: {error_description}
{extra_prompt}

Fragmento:
{fragment}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en accesibilidad web y WCAG 2.2 nivel A."},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.2,
            max_tokens=600
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error llamando a OpenAI: {e}")
        return None

    for prefix in ["Fragmento corregido:", "HTML corregido:", "html"]:
        if content.lower().startswith(prefix.lower()):
            content = content[len(prefix):].strip()

    if content.startswith("```") and "```" in content[3:]:
        content = content[3:].split("```")[0].strip()

    if not content.startswith("<") or len(content) < 10 or not is_valid_html(content):
        return None

    cleaned = clean_html(content)

    if not cleaned or not is_valid_html(cleaned):
        return None

    nested, tag = detect_nested_tags(cleaned)
    if nested:
        print(f"Advertencia: etiqueta <{tag}> anidada dentro de sí misma en la corrección, descartando este resultado.")
        return None

    return cleaned

def correct_html_with_all_errors(fragment, errors_filepath):
    wcag_errors = load_wcag_errors(errors_filepath)
    results = {}

    for error_code, data in wcag_errors.items():
        description = data.get("description", "")
        extra_prompt = data.get("prompt", "")
        corrected = correct_html(fragment, description, extra_prompt)
        if corrected:
            results[error_code] = corrected
        else:
            print(f"No se pudo generar una corrección válida para el error {error_code}.")

    return results

