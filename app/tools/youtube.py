"""
YouTubeTool: reproduce audio/video de YouTube y controla la reproducción activa.

Dependencias del sistema:
  - VLC debe estar instalado: `sudo apt install vlc` (Linux) o https://videolan.org (Windows)

Dependencias Python:
  - yt-dlp
  - python-vlc
"""

import webbrowser
from typing import Any, Optional

try:
    import vlc
    _VLC_AVAILABLE = True
except ImportError:
    _VLC_AVAILABLE = False

import yt_dlp


class YouTubeTool:
    def __init__(self):
        self._vlc_available: bool = _VLC_AVAILABLE
        if not self._vlc_available:
            print("⚠️  VLC no está instalado. La reproducción de audio no estará disponible.")
            print("    Linux: sudo apt install vlc")
            print("    Windows: https://videolan.org")
        self._player: Optional[Any] = None
        self._current_title: str = ""

    def execute(self, action: str, query: str = "") -> str:
        """
        Punto de entrada principal. Despacha según action:
          "play_audio"  → _play_audio(query)
          "play_video"  → _play_video(query)
          "pause"       → _pause()
          "resume"      → _resume()
          "stop"        → _stop()
        Retorna string de confirmación o error; nunca lanza excepción al llamador.
        """
        dispatch = {
            "play_audio": lambda: self._play_audio(query),
            "play_video": lambda: self._play_video(query),
            "pause": self._pause,
            "resume": self._resume,
            "stop": self._stop,
        }

        handler = dispatch.get(action)
        if handler is None:
            return f"Acción desconocida para YouTube: '{action}'."

        try:
            return handler()
        except Exception as exc:
            return f"Error al ejecutar la acción '{action}' en YouTube: {exc}"

    # ------------------------------------------------------------------
    # Métodos privados
    # ------------------------------------------------------------------

    def _play_audio(self, query: str) -> str:
        """
        Busca el primer resultado de 'ytsearch1:{query}' con yt-dlp,
        extrae la URL del stream de audio y lo reproduce con VLC.
        """
        if not self._vlc_available:
            return "VLC no está instalado. No es posible reproducir audio. Instala VLC: sudo apt install vlc (Linux) o https://videolan.org (Windows)."

        if not query.strip():
            return "Por favor, indica qué quieres escuchar."

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)

                # extract_info con ytsearch devuelve un dict con clave 'entries'
                entries = info.get("entries") if info else None
                if not entries:
                    return f"No se encontraron resultados en YouTube para '{query}'."

                entry = entries[0]
                url = entry.get("url")
                title = entry.get("title", query)

                if not url:
                    return f"No se pudo extraer el stream de audio para '{query}'."

        except yt_dlp.utils.DownloadError as exc:
            return f"No se encontraron resultados en YouTube para '{query}': {exc}"
        except Exception as exc:
            return f"Error al buscar '{query}' en YouTube: {exc}"

        # Detener reproducción previa si existe
        if self._player is not None:
            try:
                self._player.stop()
            except Exception:
                pass

        try:
            self._player = vlc.MediaPlayer(url)
            self._player.play()
            self._current_title = title
        except Exception as exc:
            return f"Error al reproducir '{title}' con VLC: {exc}"

        return f"Reproduciendo '{title}' en audio."

    def _play_video(self, query: str) -> str:
        """
        Busca el primer resultado de 'ytsearch1:{query}' con yt-dlp
        y abre la URL de YouTube en el navegador del sistema.
        """
        if not query.strip():
            return "Por favor, indica qué quieres ver."

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "extract_flat": True,  # Sólo necesitamos la URL de la página
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)

                entries = info.get("entries") if info else None
                if not entries:
                    return f"No se encontraron resultados en YouTube para '{query}'."

                entry = entries[0]
                video_id = entry.get("id")
                title = entry.get("title", query)

                if not video_id:
                    return f"No se pudo obtener la URL del video para '{query}'."

                youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        except yt_dlp.utils.DownloadError as exc:
            return f"No se encontraron resultados en YouTube para '{query}': {exc}"
        except Exception as exc:
            return f"Error al buscar '{query}' en YouTube: {exc}"

        try:
            webbrowser.open(youtube_url)
            self._current_title = title
        except Exception as exc:
            return f"Error al abrir el navegador para '{title}': {exc}"

        return f"Abriendo '{title}' en el navegador."

    def _pause(self) -> str:
        """Pausa la reproducción de audio activa."""
        if self._player is None:
            return "No hay reproducción activa para pausar."

        try:
            self._player.pause()
        except Exception as exc:
            return f"Error al pausar la reproducción: {exc}"

        title = self._current_title or "la reproducción"
        return f"Reproducción de '{title}' pausada."

    def _resume(self) -> str:
        """Reanuda la reproducción de audio pausada."""
        if self._player is None:
            return "No hay reproducción activa para reanudar."

        try:
            self._player.play()
        except Exception as exc:
            return f"Error al reanudar la reproducción: {exc}"

        title = self._current_title or "la reproducción"
        return f"Reproducción de '{title}' reanudada."

    def _stop(self) -> str:
        """Detiene y libera la reproducción de audio activa."""
        if self._player is None:
            return "No hay reproducción activa para detener."

        title = self._current_title or "la reproducción"

        try:
            self._player.stop()
            self._player = None
            self._current_title = ""
        except Exception as exc:
            return f"Error al detener la reproducción: {exc}"

        return f"Reproducción de '{title}' detenida."
