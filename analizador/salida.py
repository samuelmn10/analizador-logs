"""Muestra el reporte en consola. Es la única parte que usa print()."""

SEPARADOR = "=" * 50


def mostrar_reporte(reporte, definicion):
    if reporte.total_eventos == 0:
        print(f"El archivo '{reporte.archivo}' no contiene eventos.")
        return

    print(SEPARADOR)
    print(f" RESUMEN DE LOGS: {reporte.archivo}")
    print(f" Agente: {reporte.agente}")
    print(SEPARADOR)
    print(f" Total de eventos:           {reporte.total_eventos}")
    for nivel, cantidad in reporte.por_tipo.items():
        print(f"   - {nivel:<10}               {cantidad}")
    sin_tipo = reporte.total_eventos - sum(reporte.por_tipo.values())
    print(f"   - Sin tipo válido          {sin_tipo}")
    print(f" Líneas mal formateadas:     {reporte.mal_formateadas}")
    print(SEPARADOR)

    if definicion.mostrar_detalle and reporte.con_problemas:
        print(" DETALLE DE LÍNEAS CON PROBLEMAS")
        print(SEPARADOR)
        for linea in reporte.con_problemas:
            print(f" Línea {linea.numero}: {linea.texto}")
            print(f"    -> {', '.join(p.mensaje for p in linea.problemas)}")
        print(SEPARADOR)

    if reporte.explicacion:
        print(f" EXPLICACIÓN ({reporte.explicacion_fuente})")
        print(SEPARADOR)
        print(reporte.explicacion)
        print(SEPARADOR)
