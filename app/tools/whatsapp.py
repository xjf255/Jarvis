"""
WhatsAppTool — Herramienta para gestionar mensajes de WhatsApp.

Requisitos: 7.2.1, 7.2.2, 7.2.3, 7.2.4, 7.2.5
"""

import webbrowser

try:
    import pywhatkit
    _PYWHATKIT_AVAILABLE = True
except ImportError:
    _PYWHATKIT_AVAILABLE = False


class WhatsAppTool:
    """
    Herramienta para leer mensajes no leídos y enviar mensajes de WhatsApp.

    Métodos públicos:
        execute(action, contact, message) → str
    """

    def execute(self, action: str, contact: str = "", message: str = "") -> str:
        """
        Despacha la acción solicitada.

        Acciones válidas:
          - "read_unread"   → _read_unread()
          - "send_message"  → _send_message(contact, message)

        Retorna siempre un string (nunca lanza excepción al llamador).
        """
        try:
            if action == "read_unread":
                return self._read_unread()
            elif action == "send_message":
                return self._send_message(contact, message)
            else:
                return (
                    f"Acción desconocida para WhatsApp: '{action}'. "
                    "Las acciones disponibles son: read_unread, send_message."
                )
        except Exception as e:
            return f"Error inesperado en WhatsAppTool.execute: {type(e).__name__}: {e}"

    # ------------------------------------------------------------------
    # Acciones internas
    # ------------------------------------------------------------------

    def _read_unread(self) -> str:
        """
        Abre WhatsApp Web en el navegador por defecto del sistema.

        La lectura automatizada de mensajes requiere una sesión activa de
        WhatsApp Web. Esta implementación básica abre el navegador para que
        el usuario pueda revisar sus mensajes manualmente.

        Retorna un mensaje informativo en español.
        """
        try:
            webbrowser.open("https://web.whatsapp.com")
            return (
                "He abierto WhatsApp Web en tu navegador. "
                "Por favor revisa tus mensajes no leídos directamente en la página. "
                "La lectura automática requiere una sesión activa en el navegador."
            )
        except Exception as e:
            return (
                f"No fue posible abrir WhatsApp Web: {type(e).__name__}: {e}"
            )

    def _send_message(self, contact: str, message: str) -> str:
        """
        Envía un mensaje de WhatsApp al contacto especificado usando pywhatkit.

        Args:
            contact: Número de teléfono con código de país (p.ej. "+521234567890")
                     o nombre del contacto según el soporte de pywhatkit.
            message: Texto del mensaje a enviar.

        Retorna un string de confirmación o de error.
        """
        if not contact or not contact.strip():
            return (
                "No se puede enviar el mensaje: el contacto no fue especificado. "
                "Por favor indica el número de teléfono o nombre del contacto."
            )

        if not message or not message.strip():
            return (
                "No se puede enviar el mensaje: el texto del mensaje está vacío. "
                "Por favor indica el contenido del mensaje."
            )

        if not _PYWHATKIT_AVAILABLE:
            return (
                "No fue posible enviar el mensaje: la librería pywhatkit no está instalada. "
                "Instálala con: pip install pywhatkit"
            )

        try:
            pywhatkit.sendwhatmsg_instantly(
                contact,
                message,
                wait_time=10,
                tab_close=True,
            )
            return (
                f"Mensaje enviado correctamente a {contact}: \"{message}\"."
            )
        except Exception as e:
            return (
                f"No fue posible enviar el mensaje a '{contact}': "
                f"{type(e).__name__}: {e}"
            )
