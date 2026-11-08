# Reflexión técnica: uso de IA en el analizador de logs

**Proyecto:** Analizador de logs en Python
**Curso:** Kodigo, Semana 3: IA-first mindset
**IA utilizada:** Claude (Anthropic)

## 1. Partes sugeridas o generadas por la IA

La mayor parte del código base la generó la IA a partir del enunciado de la actividad:

- **La estructura del programa en funciones:** `analizar_linea` (revisa una línea), `analizar_archivo` (recorre el archivo y acumula conteos), `validar_fecha`, `validar_nombre`, `validar_correo`, `mostrar_resumen` y `main`.
- **Las expresiones regulares:** la que separa `[NIVEL]` del resto de la línea, la que detecta si algo parece una fecha, las que extraen los campos `usuario=` y `correo=`, y la del formato de correo.
- **El uso de `datetime.strptime`** para validar que una fecha exista de verdad (no solo que tenga dígitos).
- **El manejo de errores del archivo:** archivo inexistente, carpeta en vez de archivo, archivo vacío y caracteres con otra codificación (`errors="replace"`).
- **Los archivos de prueba, las pruebas automáticas con `unittest` y la estructura del README.**

La IA también propuso una idea de diseño que me pareció útil: poner cada regla de validación en una constante al inicio del script (`NOMBRE_SOLO_LETRAS = True`, etc.). Así puedo cambiar una regla sin tocar la lógica del programa.

## 2. Decisiones que tomé yo

La IA no decidió qué se considera un error. Cuando había que definir una regla, me preguntó y yo elegí:

| Decisión | Qué elegí | Por qué |
|---|---|---|
| Validar nombres y correos | Agregué estas dos validaciones, que no estaban en el enunciado | En un log de una aplicación real los eventos de usuarios traen nombre y correo, y un dato mal capturado ahí es tan grave como una fecha mala |
| Dónde buscar nombres | Solo en el campo `usuario=` | El mensaje tiene otras palabras con mayúscula ("Login", "User") que no son nombres. Sin un campo marcado no se pueden distinguir |
| Regla de nombre | Mayúscula inicial en cada palabra, con tildes y ñ, mínimo nombre y apellido | Los nombres en español llevan tildes y ñ (Pérez, Muñoz). Un solo nombre ("Juan") no identifica bien a una persona |
| Números o símbolos en el nombre | No permitidos (`Juan3 Pérez` es inválido) | Un nombre real no lleva números ni símbolos; si aparecen, es un error de captura |
| Formato de correo | `identificador@servicio.dominio`, sin puntos seguidos y sin punto al inicio o al final del identificador | Es la estructura mínima de un correo real, y Gmail y la mayoría de servicios rechazan esos casos de puntos |
| Correo mal escrito | Cuenta como línea mal formateada, pero el evento sigue sumando en su tipo | Un correo inválido es un dato corrupto, igual que una fecha inválida, pero el nivel (INFO/ERROR) sí se conoce y no quiero perder ese conteo |
| Línea sin `usuario=` ni `correo=` | No es error | No todos los eventos involucran a un usuario, por ejemplo "Backup completed" |
| Línea sin fecha | Cuenta en su tipo **y** como incompleta | El nivel se conoce, pero falta información y hay que avisarlo |
| Fecha imposible (2025-13-45, 2025-02-30) | Inválida | Una fecha que no existe hace que el registro no sea confiable |
| Nivel desconocido (`[DEBUG]`) | Mal formateada, sin tipo | El enunciado solo define INFO, WARNING y ERROR |
| Nivel en minúsculas (`[info]`) | Aceptado | Es el mismo nivel escrito distinto; rechazarlo sería demasiado estricto |
| Líneas vacías | Se ignoran | Una línea en blanco no es un evento ni un error |

**Casos borde que decidí no manejar:** fechas con hora (`2025-01-10 14:30`), nombres compuestos con guion o apóstrofo (`María-José`, `O'Connor`), texto suelto después del nombre sin otro campo (`usuario=Ana López logged in` se lee completo como nombre) y si el correo existe de verdad (solo reviso el formato). Quedan fuera porque el enunciado pide analizar el formato del archivo, no verificar datos contra un sistema externo.

## 3. Ejemplo concreto: la IA sugirió algo incompleto y lo corregí

**i. Lo que sugirió la IA.** Para validar correos, la IA propuso esta expresión regular:

```
^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$
```

Revisa que haya un identificador, una @ y un servicio con dominio. Pero en el identificador permite cualquier cantidad de puntos en cualquier posición.

**ii. Cómo lo detecté.** Revisando la lista de casos borde que el programa no cubría, aparecían los correos con puntos seguidos. Para confirmarlo agregué esta línea al archivo de pruebas con errores:

```
[INFO] 2025-01-13 Login usuario=Ana López correo=ana..lopez@gmail.com
```

Al correr el programa, la línea 22 **no apareció en el detalle de errores**: el programa aceptaba como válido un correo que no lo es.

**iii. Cómo lo corregí.** Tenía dos opciones: prohibir solo los puntos seguidos, o además prohibir que el identificador empiece o termine con punto (`.ana@gmail.com`, `ana.@gmail.com`). Elegí la segunda porque los servicios de correo reales tampoco aceptan esos casos. Agregué dos validaciones en `validar_correo`:

```python
if ".." in correo:
    return "tiene dos puntos seguidos"
if identificador.startswith(".") or identificador.endswith("."):
    return "el identificador no puede empezar ni terminar con punto"
```

Al volver a correr el programa, la línea 22 aparece con el motivo *"tiene dos puntos seguidos"* y las líneas mal formateadas pasaron de 16 a 17. También agregué tres pruebas automáticas para estos casos.

Algo que me llamó la atención: la IA sabía que su regex tenía esa limitación (la dejó anotada como caso borde), pero no la corrigió por su cuenta. Decidir si era un problema y cómo resolverlo me tocó a mí.

## 4. Qué aprendí sobre la IA como herramienta y no como reemplazo

La IA escribe rápido código que "se ve bien" y que funciona con los casos normales. El problema aparece con los casos malos: una regex puede parecer correcta y aun así aceptar datos inválidos. Eso solo se descubre probando con datos hechos a propósito para fallar, y por eso el archivo `logs_malos.txt` fue tan importante como el código.

También aprendí que las reglas no son una cuestión técnica sino de criterio. Si `Juan3 Pérez` es un nombre válido, si una línea sin fecha es un error o solo una advertencia, o dónde buscar un nombre dentro de un mensaje: ninguna de esas preguntas tiene una única respuesta correcta. Depende de para qué se usa el programa, y ese contexto lo tengo yo, no la IA. Por ejemplo, al elegir las reglas de nombres no marqué "solo letras", y eso dejaba pasar `Juan3 Pérez`. Cuando la IA me hizo ver esa consecuencia, decidí cambiarlo porque no tiene sentido para un nombre real. La IA me mostró qué implicaba mi elección, pero la decisión fue mía.

Mi conclusión es que la IA me ahorró mucho tiempo en la parte de escribir código, pero yo sigo siendo responsable de qué hace ese código. Tengo que entender para qué sirve cada parte, decidir las reglas y comprobar que el resultado sea el correcto.
