# Paso 6: Inversion

## Inversion

Este paso expresa la inversion estimada necesaria para desarrollar o implementar
la solucion propuesta.

La informacion debe servir como base para confeccionar una estimacion macro de
esfuerzo. En este paso, presupuesto significa cantidad de horas, FTEs y
personas o equipos participantes. No se requiere estimar montos economicos.

Debe incluir:

- Presupuesto estimado en terminos de esfuerzo.
- FTE requeridos.
- Recursos tecnicos.
- Consultorias.
- Duracion del desarrollo o implementacion.
- Equipos participantes en la solucion.
- Horas estimadas por equipo.
- FTE estimado por equipo.
- Fechas tentativas de inicio y fin.

## Informacion que debe capturarse por equipo

Cada item de inversion debe representar un equipo participante y contener:

- Nombre de Equipo.
- Cantidad de horas.
- Rol a desempenar.
- FTE calculado como `cantidad de horas / 160`.

## Totales requeridos

La aplicacion debe calcular:

- Total de horas necesarias.
- Total de FTEs.

La aplicacion tambien debe capturar:

- Fecha tentativa de inicio.
- Fecha tentativa de fin.

## Preguntas que debe responder

- Cuantos FTE se necesitan?
- Que presupuesto de esfuerzo se necesita en horas, FTEs y equipos/personas?
- Durante que periodo de tiempo?
- Que equipos participan en la solucion?
- Cuantas horas aporta cada equipo?
- Que rol desempena cada equipo?

## Reglas

- La lista de equipos participantes no puede estar vacia.
- No pueden existir equipos repetidos.
- El Nombre de Equipo no puede estar vacio.
- La Cantidad de horas debe ser un numero entero.
- La Cantidad de horas debe ser mayor a cero.
- El Rol a desempenar debe ser un texto explicativo a nivel macro.
- El FTE por equipo debe calcularse como `horas / 160`.
- El Total de horas debe calcularse sumando las horas de todos los equipos.
- El Total de FTEs debe calcularse como `total de horas / 160`.
- Las fechas tentativas de inicio y fin deben usar formato `AAAA-MM-DD`.
- La fecha tentativa de fin no deberia ser anterior a la fecha tentativa de
  inicio.
- Si faltan horas, FTEs, equipos/personas o periodo tentativo, el feedback debe
  indicar que dato falta para completar la estimacion macro de esfuerzo.

## Tarea del modelo

1. Recibir la lista de equipos participantes, sus horas, roles y FTE calculados.
2. Recibir el total de horas, total de FTEs y fechas tentativas.
3. Validar si la informacion es suficiente para estimar la inversion.
4. Revisar si los roles estan explicados a nivel macro y son comprensibles para
   negocio.
5. Identificar faltantes para confeccionar la estimacion macro de esfuerzo,
   especialmente horas, FTEs, equipos/personas, recursos tecnicos o
   consultorias.
6. Validar coherencia con la Vision, Target, Valor de Negocio, Necesidad y
   Solucion Propuesta definidos previamente.
7. Proponer ajustes concretos si la estimacion es incompleta, inconsistente o
   poco clara.

## Formato de respuesta

## Inversion validada
- Equipo: <nombre>
  - Horas: <horas>
  - FTE: <fte>
  - Rol: <rol>
  - Validacion: <cumple/no cumple> - <breve justificacion>

## Totales
- Total horas: <total horas>
- Total FTEs: <total ftes>
- Periodo estimado: <fecha inicio> a <fecha fin>

## Validacion
- Lista no vacia: <cumple/no cumple>
- Equipos sin repetir: <cumple/no cumple>
- Horas validas: <cumple/no cumple>
- Roles claros: <cumple/no cumple>
- FTEs correctamente calculados: <cumple/no cumple>
- Totales correctamente calculados: <cumple/no cumple>
- Fechas validas: <cumple/no cumple>
- Presupuesto de esfuerzo informado: <cumple/no cumple>
- Coherencia con pasos previos: <cumple/no cumple>

## Ajustes sugeridos
<1 a 3 recomendaciones concretas para completar o mejorar la estimacion.>
