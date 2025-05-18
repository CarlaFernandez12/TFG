import openai
import os

# Configura tu clave API de OpenAI aquí o en variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

def correct_css(css_fragment, error_description, extra_prompt=""):
    """
    Corrige un fragmento CSS para que cumpla WCAG 2.2 nivel A usando OpenAI GPT.

    Args:
        css_fragment (str): Código CSS que contiene el error.
        error_description (str): Descripción del error de accesibilidad.
        extra_prompt (str): Texto extra que quieras añadir al prompt.

    Returns:
        str|None: CSS corregido o None si no se pudo corregir.
    """
    # Limitar tamaño para evitar cortes
    fragment = css_fragment[:1500].encode("utf-8", errors="ignore").decode("utf-8")

    prompt = f"""
Corrige el siguiente fragmento CSS para que cumpla la norma WCAG 2.2 nivel A.
Haz SOLO los cambios necesarios, sin duplicar contenido. Mantén el mismo formato.
NO añadas explicaciones, NO repitas el fragmento original.

Error: {error_description}
{extra_prompt}

Fragmento CSS:
{fragment}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en accesibilidad web y WCAG 2.2 nivel A."},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.2,
            max_tokens=600,
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[correct_css] Error OpenAI API: {e}")
        return None

    # Limpieza del contenido para extraer sólo el código
    for prefix in ["Fragmento corregido:", "CSS corregido:", "css"]:
        if content.lower().startswith(prefix.lower()):
            content = content[len(prefix):].strip()

    if content.startswith("```") and "```" in content[3:]:
        content = content[3:].split("```")[0].strip()

    if not content or len(content) < 5:
        return None

    return content
