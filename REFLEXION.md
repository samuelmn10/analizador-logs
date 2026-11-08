# Reflexión técnica: uso de IA en el analizador de logs

> **PLANTILLA.** Reemplaza todo lo que está entre `[corchetes]` con tu experiencia real y borra estas notas antes de entregar. Extensión máxima: 1 a 3 páginas.

## 1. Partes sugeridas o apoyadas por la IA

[Escribe qué te dio la IA. Algunas posibilidades:]

- Las expresiones regulares para separar `[NIVEL]` del resto de la línea.
- La estructura del programa en funciones (`analizar_linea`, `analizar_archivo`, `mostrar_resumen`, `main`).
- El formato de la salida en consola.
- La explicación de `datetime.strptime` y de `errors="replace"` al abrir el archivo.
- Las pruebas automáticas con `unittest`.

## 2. Decisiones que tomé yo

[Para cada regla de la sección "REGLAS DE VALIDACIÓN" del script, escribe qué decidiste y por qué. Ejemplos de justificación:]

| Decisión | Qué elegí | Por qué |
|---|---|---|
| Línea sin fecha | La cuento en su tipo **y** como incompleta | [ej: el nivel sí se conoce, así que no quiero perder ese conteo, pero hay que avisar que falta información] |
| Fecha imposible (2025-13-45) | Inválida | [ej: un log con una fecha que no existe no es confiable] |
| Nivel en minúsculas | [Aceptado / Rechazado] | [...] |
| Nivel desconocido ([DEBUG]) | Mal formateada, sin tipo | [ej: el enunciado solo define INFO, WARNING y ERROR] |
| Líneas vacías | Ignoradas | [ej: un espacio en blanco no es un evento ni un error] |
| Línea sin mensaje | Incompleta | [...] |
| Archivo inexistente | Mensaje claro, sin traceback | [...] |
| Dónde buscar nombres | Solo en el campo `usuario=` | [ej: en el mensaje hay otras palabras con mayúscula ("Login", "User") que no son nombres; sin un campo marcado no se puede distinguirlas] |
| Regla de nombre | Mayúscula inicial en cada palabra, con tildes y ñ, mínimo nombre y apellido | [ej: los nombres en español llevan tildes y ñ; un solo nombre no identifica bien a la persona] |
| Números o símbolos en el nombre | No permitidos (`Juan3 Pérez` es inválido) | [ej: un nombre propio real no lleva números ni símbolos; si aparecen, probablemente es un dato mal capturado] |
| Formato de correo | `identificador@servicio.dominio` | [ej: es la estructura mínima de cualquier correo real] |
| Correo mal escrito | Línea mal formateada (cuenta igual en su tipo) | [ej: un correo inválido es un dato corrupto, igual que una fecha inválida] |
| Línea sin `usuario=` ni `correo=` | No es error | [ej: no todos los eventos involucran a un usuario, por ejemplo "Backup completed"] |

**Casos borde que decidí NO manejar:**
[ej: fechas con hora (`2025-01-10 14:30`), varios niveles en la misma línea, archivos de varios GB, otras codificaciones distintas de UTF-8, nombres compuestos con guion o apóstrofo (`María-José`, `O'Connor`), texto suelto después del nombre sin otro campo (`usuario=Ana López logged in` se lee completo como nombre), correos con puntos seguidos (`ana..lopez@gmail.com` se acepta) o que no existen de verdad (solo se revisa el formato). Explica por qué quedaron fuera del alcance.]

## 3. Ejemplo concreto: la IA se equivocó y yo lo corregí

[Este punto es obligatorio. Cuenta un caso REAL. Si todavía no tienes uno, prueba esto: pídele a cualquier IA "una expresión regular para validar fechas AAAA-MM-DD en un log". Es muy probable que te dé algo como `\d{4}-\d{2}-\d{2}`. Pruébala con la línea 4 de `logs_malos.txt`.]

**i. Lo que sugirió la IA:**
[Pega aquí la sugerencia.]

**ii. Cómo detecté el problema:**
[ej: probé con `2025-13-45` y la regex la aceptó como válida, aunque el mes 13 no existe.]

**iii. Cómo lo corregí:**
[ej: uso la regex solo para detectar si hay un intento de fecha y valido la fecha real con `datetime.strptime`, que rechaza meses y días imposibles, incluido el 30 de febrero.]

## 4. Qué aprendí sobre la IA como herramienta y no como reemplazo

[Escribe 1 o 2 párrafos con tus propias palabras. Ideas para guiarte:]

- La IA genera código que "se ve bien", pero solo lo pruebas de verdad con casos malos.
- Las reglas de negocio (qué es un error) dependen del contexto, y ese contexto lo tengo yo, no la IA.
- [...]
