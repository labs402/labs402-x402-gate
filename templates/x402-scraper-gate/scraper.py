"""
Scraper de Wikipedia usando la API REST oficial.
No hay scraping de HTML: la API devuelve JSON directamente.

Wikipedia permite el uso de su API sin autenticacion.
Requiere el header User-Agent para evitar bloqueos por IP.
"""

import httpx

WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

# Wikipedia exige identificar al cliente en el User-Agent
HEADERS = {"User-Agent": "labs402-x402-scraper/0.1 (https://github.com/labs402)"}


def obtener_resumen(titulo: str) -> dict:
    """
    Devuelve el resumen de un articulo de Wikipedia.

    Args:
        titulo: nombre exacto del articulo (ej: "Solana_(blockchain_platform)")

    Returns:
        dict con titulo, resumen y url del articulo

    Raises:
        httpx.HTTPStatusError: si el articulo no existe (404) o hay error de red
    """
    url = WIKIPEDIA_API.format(title=titulo)
    respuesta = httpx.get(url, headers=HEADERS, timeout=10)
    respuesta.raise_for_status()
    datos = respuesta.json()

    return {
        "titulo": datos.get("title", ""),
        "resumen": datos.get("extract", ""),
        "url": datos.get("content_urls", {}).get("desktop", {}).get("page", ""),
    }
