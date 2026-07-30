"""
BrowserTool: abre el navegador por defecto para buscar en Google o abrir URLs.

Depende únicamente de la librería estándar: webbrowser, urllib.parse.
"""

import webbrowser
import urllib.parse


class BrowserTool:
    GOOGLE_SEARCH_URL = "https://www.google.com/search?q={}"

    def execute(self, action: str, query: str = "", url: str = "") -> str:
        """
        Punto de entrada principal. Despacha según action:
          "search"    → _search(query)
          "open_url"  → _open_url(url)
          cualquier otro → string de error indicando acción desconocida.

        Siempre retorna un string; nunca lanza excepción al llamador.
        """
        if action == "search":
            return self._search(query)
        elif action == "open_url":
            return self._open_url(url)
        else:
            return f"Error: acción desconocida '{action}'. Las acciones disponibles son 'search' y 'open_url'."

    def _search(self, query: str) -> str:
        """
        Construye la URL de búsqueda de Google codificando el término con
        urllib.parse.quote_plus() y la abre en el navegador por defecto.

        Retorna un string de confirmación o de error.
        """
        try:
            encoded_query = urllib.parse.quote_plus(query)
            search_url = self.GOOGLE_SEARCH_URL.format(encoded_query)
            webbrowser.open(search_url)
            return f"Búsqueda en Google abierta: '{query}'"
        except Exception as e:
            return f"Error al abrir la búsqueda en el navegador: {type(e).__name__}: {e}"

    def _open_url(self, url: str) -> str:
        """
        Abre la URL en el navegador por defecto del sistema.
        Si la URL no comienza con 'http://' ni 'https://', añade 'https://'.

        Retorna un string de confirmación o de error.
        """
        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            webbrowser.open(url)
            return f"URL abierta en el navegador: {url}"
        except Exception as e:
            return f"Error al abrir la URL en el navegador: {type(e).__name__}: {e}"
