"""
LLM client module for the Jarvis voice assistant.

Communicates with OpenRouter using the OpenAI-compatible API.
"""

import os
import json
from dataclasses import dataclass
from typing import Literal, Any

import openai


SYSTEM_PROMPT = (
    "Eres Jarvis, un asistente personal inteligente. "
    "Responde siempre en español, de forma concisa y clara. "
    "Tus respuestas serán convertidas a voz, por lo que debes evitar markdown, "
    "listas numeradas, viñetas, asteriscos y cualquier carácter especial. "
    "Usa oraciones completas y naturales. Máximo 2-3 oraciones. "
    "Cuando el usuario solicite reproducir música, video, enviar mensajes de "
    "WhatsApp o buscar en internet, usa la herramienta correspondiente."
)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "youtube",
            "description": "Reproduce música o video de YouTube, o controla la reproducción activa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play_audio", "play_video", "pause", "resume", "stop"],
                        "description": "Acción a realizar",
                    },
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda en YouTube (requerido para play_audio y play_video)",
                    },
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "whatsapp",
            "description": "Lee mensajes no leídos de WhatsApp o envía un mensaje a un contacto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read_unread", "send_message"],
                        "description": "Acción a realizar",
                    },
                    "contact": {
                        "type": "string",
                        "description": "Nombre o número del contacto (requerido para send_message)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Texto del mensaje (requerido para send_message)",
                    },
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser",
            "description": "Abre el navegador para buscar en Google o abrir una URL específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "open_url"],
                        "description": "Acción a realizar",
                    },
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda (requerido para search)",
                    },
                    "url": {
                        "type": "string",
                        "description": "URL a abrir (requerido para open_url)",
                    },
                },
                "required": ["action"],
            },
        },
    },
]


@dataclass
class LLMResponse:
    type: Literal["text", "tool_call"]
    text: str | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None


class LLMClient:
    """Encapsulates communication with OpenRouter via the OpenAI-compatible API."""

    def __init__(self) -> None:
        """
        Read OPENROUTER_API_KEY and LLM_MODEL from environment variables.
        Configure the openai client pointing to OpenRouter's base URL.

        Raises:
            ValueError: If OPENROUTER_API_KEY is not defined in the environment.
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY no está definida en las variables de entorno. "
                "Por favor, configúrala en el archivo .env antes de ejecutar el sistema."
            )

        self.model: str = os.getenv(
            "LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free"
        )

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def generate(self, user_text: str) -> LLMResponse:
        """
        Send user_text to OpenRouter and return an LLMResponse.

        Includes tool definitions so the model can decide to call a tool instead
        of responding with text. Interprets the response based on finish_reason.

        Args:
            user_text: The user's query transcribed from speech.

        Returns:
            LLMResponse with type="text" if the model replied in text, or
            LLMResponse with type="tool_call" if the model requested a tool.

        Raises:
            Any exception raised by the OpenRouter API is propagated to the caller.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=300,
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            return LLMResponse(
                type="tool_call",
                tool_name=tool_call.function.name,
                tool_args=json.loads(tool_call.function.arguments),
            )

        return LLMResponse(
            type="text",
            text=choice.message.content,
        )
