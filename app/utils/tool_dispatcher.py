"""
ToolDispatcher — despacha tool_calls del LLMClient a las herramientas correspondientes.

Requisitos: 7.4, 7.5, 7.6, 7.7
"""

from app.tools.youtube import YouTubeTool
from app.tools.whatsapp import WhatsAppTool
from app.tools.browser import BrowserTool


class ToolDispatcher:
    """
    Recibe el nombre de la herramienta y sus argumentos desde el LLMClient
    y delega la ejecución al módulo de herramienta correspondiente.

    Garantiza que dispatch() SIEMPRE retorna un string y nunca lanza excepción.
    """

    def __init__(self):
        youtube_tool = YouTubeTool()
        whatsapp_tool = WhatsAppTool()
        browser_tool = BrowserTool()

        self._registry: dict = {
            "youtube": youtube_tool.execute,
            "whatsapp": whatsapp_tool.execute,
            "browser": browser_tool.execute,
        }

    def dispatch(self, tool_name: str, tool_args: dict) -> str:
        """
        Busca la herramienta en el registro interno y la ejecuta con tool_args.

        Args:
            tool_name: Nombre de la herramienta (p. ej. "youtube", "whatsapp", "browser").
            tool_args: Diccionario de argumentos para pasar a la herramienta como kwargs.

        Returns:
            String con el resultado de la herramienta, un mensaje de herramienta
            no disponible, o una descripción del error ocurrido.
            Nunca lanza excepción al llamador.
        """
        executor = self._registry.get(tool_name)

        if executor is None:
            return (
                f"Herramienta '{tool_name}' no está disponible. "
                f"Las herramientas disponibles son: {', '.join(self._registry.keys())}."
            )

        try:
            return str(executor(**tool_args))
        except Exception as e:
            return (
                f"Error al ejecutar herramienta '{tool_name}': "
                f"{type(e).__name__}: {e}"
            )
