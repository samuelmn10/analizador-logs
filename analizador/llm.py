"""
Cliente opcional de Claude (Anthropic).

El paquete `anthropic` NO es obligatorio: el analizador funciona solo con la
librería estándar. Si el paquete no está instalado o no hay credenciales,
la skill explicar_errores usa una explicación basada en reglas.
"""


class ErrorLLM(Exception):
    """No se pudo obtener una respuesta del modelo; el motivo va en el mensaje."""


class ClienteClaude:
    """Envía una sola solicitud a la API de mensajes de Claude."""

    def __init__(self):
        try:
            import anthropic
        except ImportError:
            raise ErrorLLM("el paquete anthropic no está instalado (pip install -r requirements.txt)")
        self._anthropic = anthropic
        # Sin argumentos: toma ANTHROPIC_API_KEY (o un perfil de `ant auth login`).
        self._cliente = anthropic.Anthropic()

    def completar(self, config, mensaje_usuario):
        """Devuelve (texto, modelo_que_respondió) o lanza ErrorLLM."""
        a = self._anthropic
        try:
            respuesta = self._cliente.beta.messages.create(
                model=config.modelo,
                max_tokens=config.max_tokens,
                output_config={"effort": config.esfuerzo},
                # Si el modelo rechaza la solicitud por sus filtros de
                # seguridad, la API reintenta con otro modelo automáticamente.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=config.prompt,
                messages=[{"role": "user", "content": mensaje_usuario}],
            )
        # De lo más específico a lo más general.
        except a.AuthenticationError:
            raise ErrorLLM("las credenciales de Anthropic no son válidas")
        except a.RateLimitError:
            raise ErrorLLM("se superó el límite de solicitudes de la API; intenta más tarde")
        except a.APIStatusError as e:
            raise ErrorLLM(f"la API respondió con un error {e.status_code}")
        except a.APIConnectionError:
            raise ErrorLLM("no hay conexión con la API de Anthropic")
        except a.AnthropicError as e:
            # Incluye el caso de no tener ninguna credencial configurada.
            raise ErrorLLM(f"no se pudo usar la API ({e})")

        if respuesta.stop_reason == "refusal":
            raise ErrorLLM("el modelo no quiso responder esta solicitud")
        texto = "".join(b.text for b in respuesta.content if b.type == "text").strip()
        if not texto:
            raise ErrorLLM("el modelo devolvió una respuesta vacía")
        return texto, respuesta.model
