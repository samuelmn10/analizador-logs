"""
Estructuras de datos que comparten las skills y los agentes.

Antes, cada línea se representaba con un diccionario armado dentro de
analizar_linea(). Ahora hay clases explícitas: cada skill sabe qué campos
puede leer y cuáles debe llenar, y se pueden combinar en cualquier orden.
"""

from dataclasses import dataclass, field


@dataclass
class Problema:
    """Un problema detectado en una línea.

    codigo  -> identificador estable (ej. "fecha_invalida"); sirve para agrupar
               problemas y buscar sugerencias en config/sugerencias.json.
    mensaje -> texto que ve el usuario (ej. "fecha inválida: 2025-13-45").
    """
    codigo: str
    mensaje: str


@dataclass
class LineaContexto:
    """Estado de una línea mientras las skills la procesan.

    parsear_linea llena los campos de extracción (nivel_texto, resto, etc.);
    las skills validar_* solo leen esos campos y agregan problemas.
    """
    numero: int
    texto: str
    vacia: bool = False
    tiene_corchetes: bool = False
    nivel_texto: str | None = None     # lo escrito entre corchetes, tal cual
    nivel: str | None = None           # nivel reconocido (INFO/WARNING/ERROR) o None
    fecha_texto: str | None = None     # primer token si parece fecha
    fecha: str = "ausente"             # "valida", "invalida" o "ausente"
    mensaje: str = ""
    problemas: list[Problema] = field(default_factory=list)

    def agregar(self, codigo: str, mensaje: str) -> None:
        self.problemas.append(Problema(codigo, mensaje))


@dataclass
class Reporte:
    """Resultado de analizar un archivo completo con un agente."""
    archivo: str
    agente: str
    lineas: list[LineaContexto] = field(default_factory=list)
    total_eventos: int = 0
    por_tipo: dict[str, int] = field(default_factory=dict)
    mal_formateadas: int = 0
    explicacion: str | None = None         # la llena explicar_errores
    explicacion_fuente: str | None = None  # "IA (modelo)" o "reglas (motivo)"

    @property
    def con_problemas(self) -> list[LineaContexto]:
        return [l for l in self.lineas if l.problemas]
