# Product Vision Board Assistant Specification

## Objetivo

Construir un asistente guiado para generar y validar los 9 puntos clave de un
Product Vision Board.

La aplicacion debe acompanar al usuario paso por paso. Cada paso captura los
comentarios del usuario, envia contexto e instrucciones al proveedor LLM
seleccionado, y devuelve una propuesta validada contra las reglas del bloque
correspondiente.

El contenido generado por cada paso debe ayudar a que un Jefe o Gerente pueda
formarse una idea temprana del alcance, tiempo, esfuerzo y costo relativo antes
de lanzar un proyecto. El asistente forma parte de una investigacion previa para
entender viabilidad, prioridades, impactos esperados y recursos necesarios, no
de una estimacion definitiva de proyecto.

## Postura de analisis del asistente

El asistente no debe actuar de forma complaciente ni asumir que la propuesta del
usuario es correcta solo porque esta redactada con seguridad. Debe validar con
criterio profesional, senalar inconsistencias, ambiguedades, supuestos debiles,
riesgos y datos faltantes.

Las sugerencias deben guiar al usuario hacia una mayor comprension del problema,
no limitarse a completar el formato del Product Vision Board. Cuando falte
evidencia, el asistente debe sugerir investigar aspectos concretos como metricas
actuales, volumenes, tiempos de ciclo, costos, actores impactados, dependencias,
restricciones operativas, riesgos regulatorios, benchmarks o alternativas. El
tono debe ser constructivo y respetuoso, incluso cuando desafie la idea del
usuario.

## Stack tecnico

- Lenguaje: Python
- Gestor de entorno y dependencias: uv
- Interfaz: Gradio
- IA generativa: OpenAI API y Google Gemini
- Configuracion sensible: python-dotenv + archivo `.env`
- Intercambio de informacion con el modelo: directorio `data`
- Respuestas generadas por el modelo: directorio `feedback`
- Especificacion funcional versionable: directorio `specs`
- Logs de actividad del asistente y los proveedores LLM: directorio `logs`

## Arquitectura prevista

- `app.py`: motor de interfaz, carga de configuracion y ejecucion del flujo.
- `data/business_context.md`: contexto transversal del Negocio.
- `data/01_vision_prompt.md`: prompt operativo del paso 1.
- `data/02_target_prompt.md`: prompt operativo del paso 2.
- `data/03_valor_negocio_prompt.md`: prompt operativo del paso 3.
- `data/04_necesidad_prompt.md`: prompt operativo del paso 4.
- `data/05_pps_prompt.md`: prompt operativo del paso 5.
- `data/05_1_competencia_prompt.md`: prompt operativo del paso 5.1.
- `data/05_2_canales_medios_prompt.md`: prompt operativo del paso 5.2.
- `data/06_inversion_prompt.md`: prompt operativo del paso 6.
- `data/07_ingresos_beneficios_prompt.md`: prompt operativo previsto del paso
  7.
- `data/openai_pricing.json`: tarifas configurables para estimar costos por
  tokens.
- `feedback/*_response.md`: ultimas respuestas generadas por el modelo.
- `feedback/AAMMDD_HHMM_nombre-archivo.md`: documentos finales consolidados
  generados por el usuario.
- `feedback/AAMMDD_HHMM_sesion_nombre-archivo.md`: sesiones parciales o
  completas guardadas por el usuario para pausar y retomar el trabajo.
- `specs/steps/01_vision.json`: especificacion estructurada del paso 1.
- `specs/steps/02_target.json`: especificacion estructurada del paso 2.
- `specs/steps/03_business_value.json`: especificacion estructurada del paso 3.
- `specs/steps/04_need.json`: especificacion estructurada del paso 4.
- `specs/steps/05_pps.json`: especificacion estructurada del paso 5.
- `specs/steps/05_1_competition.json`: especificacion estructurada del paso 5.1.
- `specs/steps/05_2_channels.json`: especificacion estructurada del paso 5.2.
- `specs/steps/06_investment.json`: especificacion estructurada del paso 6.
- `specs/steps/07_revenue_benefits.json`: especificacion estructurada prevista
  del paso 7.
- `specs/steps/03_beneficiary_users.json`: especificacion historica del paso
  reemplazado por Target.
- `logs/openai_interactions.jsonl`: historial de llamadas a proveedores LLM en
  formato JSON Lines.
- `logs/sesiones.jsonl`: historial de guardado y carga de sesiones, incluyendo
  errores de lectura o parseo.

## Flujo por paso

1. La app carga la especificacion del paso.
2. La app renderiza titulo, instrucciones, campos de entrada, controles de
   lista cuando correspondan, boton de procesamiento y salida del modelo.
3. El usuario escribe comentarios o carga items segun el paso.
4. El boton `Procesar` envia contexto, prompt e input al proveedor LLM
   seleccionado.
5. La app muestra la respuesta del modelo y guarda la ultima salida en
   `feedback`.
6. Para pasos posteriores al primero, la app envia al proveedor LLM un contexto
   canonico compacto construido desde las respuestas previas. Este contexto debe
   priorizar decisiones, supuestos y datos pendientes, y no debe reemplazar la
   evidencia completa guardada en `feedback`.
7. Luego de cada llamada al proveedor LLM, la app registra en `logs` el
   intercambio completo y las metricas de tokens y costo estimado.

## Interfaz global

La interfaz debe implementarse con `gr.Blocks()` y componentes de disposicion
de Gradio (`Tabs`, `Accordion`, `Group`, `Row` y `Column` cuando sea necesario).
El layout debe priorizar una estructura vertical compacta con grupos separados
por funcion.

La aplicacion debe incluir un grupo superior `Sesion de trabajo`, visible por
encima de los tabs de pasos, con estos controles:

- `Nombre de sesion / caso`, precompletado con el nombre base por defecto.
- `Modelo a utilizar`, con opciones de OpenAI y Gemini.
- `Guardar sesion actual`.
- selector de `Sesion guardada`.
- `Actualizar sesiones`.
- `Cargar sesion`.
- `Estado de sesion`.
- un detalle desplegable con la ruta del archivo de sesion.

Reglas del selector de modelo:

- El selector debe estar ubicado en `Sesion de trabajo`, no dentro de un paso
  particular.
- El selector debe estar habilitado al iniciar una sesion nueva.
- Luego de procesar correctamente el paso `1. Vision`, el selector debe quedar
  deshabilitado para evitar que un mismo PVB mezcle modelos distintos.
- Al cargar una sesion guardada, la aplicacion debe restaurar el modelo usado
  en esa sesion y mostrar el selector deshabilitado.

Reglas de layout por paso:

- Cada paso debe agrupar sus controles en bloques verticales compactos.
- Los pasos con listas deben separar: carga/edicion de items, procesamiento y
  navegacion.
- La especificacion tecnica de cada paso debe seguir disponible en un
  `Accordion` cerrado por defecto.

## Navegacion y estado

La interfaz debe permitir avanzar y retroceder entre pasos sin perder lo que el
usuario haya ingresado.

Reglas de navegacion:

- Todo paso posterior al primero debe incluir un boton con la leyenda
  `Volver al paso anterior`.
- Al presionar `Volver al paso anterior`, la app debe mostrar el paso anterior.
- Al volver, no se deben limpiar ni sobrescribir los datos que el usuario haya
  ingresado en el paso actual ni en los pasos anteriores.
- Los campos de texto, listas de items, selecciones y respuestas ya generadas
  deben mantenerse en memoria durante la sesion.
- Si un paso ya genero feedback, el feedback visible y el archivo guardado en
  `feedback` deben conservarse hasta que el usuario vuelva a procesar ese paso.
- Los botones de avance deben seguir dependiendo de que el paso haya sido
  procesado correctamente.

## Sesiones de trabajo

La aplicacion debe permitir guardar y cargar sesiones de trabajo para que un
analista pueda pausar un PVB incompleto y retomarlo posteriormente.

Reglas de guardado:

- La accion `Guardar sesion actual` debe guardar un archivo Markdown en
  `feedback`.
- El nombre del archivo debe seguir el formato
  `AAMMDD_HHMM_sesion_nombre-archivo.md`.
- El archivo debe incluir un bloque de estado estructurado en formato JSON,
  delimitado como `json pvb-session-state`.
- Justo antes del bloque JSON debe incluirse el comentario:
  `No modificar esta seccion para mantener el estado.`
- El estado debe incluir nombre de sesion, modelo seleccionado, pasos
  completados, datos crudos de formularios/listas y respuestas validadas del
  modelo.
- El estado debe incluir tambien un `context_snapshot` compacto, derivado de las
  respuestas validadas, para alimentar pasos posteriores sin reenviar todo el
  Markdown historico.
- Deben guardarse tambien los borradores que el analista haya escrito en campos
  de texto aunque todavia no haya presionado `agregar` o `Procesar`.
- El archivo debe seguir siendo legible como Markdown para que pueda revisarse
  fuera de la aplicacion.

Reglas de carga:

- La accion `Cargar sesion` debe leer un archivo de sesion generado por la
  aplicacion y restaurar el estado visible de la interfaz.
- Al cargar una sesion, la aplicacion debe reemplazar el estado activo completo.
- Los archivos `feedback/*_response.md` presentes en la sesion deben
  reescribirse con el contenido guardado.
- Los archivos `feedback/*_response.md` de pasos que no esten presentes en la
  sesion deben eliminarse para evitar mezclar datos de PVBs anteriores.
- Si una sesion antigua no contiene `context_snapshot`, la aplicacion debe
  reconstruirlo desde `validated_outputs` al cargarla.
- Los campos, listas, borradores, fechas, respuestas visibles y botones de
  avance deben restaurarse segun el contenido de la sesion.
- Si la carga falla por un archivo invalido, corrupto o incompatible, la
  interfaz debe mostrar un mensaje claro al usuario y el detalle tecnico debe
  registrarse en `logs/sesiones.jsonl`.

## Documento final Markdown

La aplicacion debe permitir generar un documento final en formato Markdown a
partir de las ultimas respuestas guardadas en `feedback` para cada paso
implementado.

Reglas:

- La generacion del documento final debe estar ubicada en un tab global
  denominado `Generar Documento`, separado de los pasos del PVB.
- La UI debe sugerir un nombre base para el archivo, pero el usuario debe poder
  ajustarlo antes de generarlo.
- El archivo debe guardarse en el directorio `feedback`.
- El nombre final debe seguir el formato `AAMMDD_HHMM_nombre-archivo.md`.
- `AAMMDD_HHMM` debe calcularse al momento de generar el documento para permitir
  varias versiones durante refinamientos sucesivos.
- El nombre base ingresado por el usuario debe normalizarse para que sea seguro
  como nombre de archivo: minusculas, espacios convertidos en guiones y sin
  caracteres especiales no permitidos.
- Si el usuario no ingresa un nombre base valido, la aplicacion debe usar un
  nombre por defecto.
- El documento debe incluir una seccion por cada paso implementado y marcar como
  pendiente cualquier feedback que aun no exista.
- Antes de cada seccion de paso del documento final debe incluirse un separador
  Markdown `---` para mejorar la lectura visual entre bloques.
- Cada archivo `feedback/*_response.md` debe guardar la ultima respuesta con un
  encabezado de tercer nivel con el formato
  `### Ultima respuesta {titulo del paso}`.
- Esta generacion no debe llamar al proveedor LLM; solo consolida contenido ya
  generado.
- El paso 7 debe avanzar al tab `Generar Documento` una vez procesado
  correctamente.

## Logging y metricas

La aplicacion debe crear el directorio `logs` y guardar alli los registros de
actividad con los proveedores LLM y con las sesiones de trabajo.

Cada llamada a un proveedor LLM debe agregar una linea JSON en
`logs/openai_interactions.jsonl` con la siguiente informacion:

- identificador unico del evento
- fecha y hora
- paso del Product Vision Board
- proveedor utilizado
- modelo utilizado
- instrucciones enviadas al modelo
- input del usuario enviado al modelo
- respuesta generada por el modelo
- identificador de respuesta devuelto por el proveedor, si esta disponible
- metricas de tokens:
  - input tokens
  - cached input tokens
  - billable input tokens
  - output tokens
  - reasoning tokens, si estan disponibles
  - total tokens
  - usage crudo devuelto por el SDK
- metricas de costo:
  - costo estimado de input
  - costo estimado de cached input
  - costo estimado de output
  - costo total estimado
  - moneda
  - fuente y fecha de la tabla de precios usada

Las tarifas deben vivir en `data/openai_pricing.json` para poder actualizarlas
sin tocar el codigo. Si un modelo no tiene tarifa configurada, el log debe
guardar tokens igualmente y marcar el costo como no disponible.

Cada guardado o carga de sesion debe agregar una linea JSON en
`logs/sesiones.jsonl` con fecha y hora, accion, archivo afectado, estado de la
operacion y detalle tecnico del error cuando corresponda.

## Paso 1: Vision

Estado: implementado.

Proposito: generar y validar una frase breve, orientada al negocio y
estrategica, que sintetice la motivacion central de la iniciativa, el impacto
positivo esperado y el valor que deberia habilitar para **El Negocio**.

Reglas:

- Frase breve de 7 a 12 palabras.
- No puede estar vacia.
- Debe ser una oracion.
- Debe expresar motivacion.
- Debe expresar cambio positivo esperado.
- Debe estar orientada al negocio y tener enfoque estrategico.
- Debe conectar la iniciativa con valor para **El Negocio**, por ejemplo
  crecimiento, eficiencia, sostenibilidad, diferenciacion, calidad de servicio,
  experiencia del afiliado/paciente, productividad operativa o toma de
  decisiones.
- No debe redactarse como una descripcion tecnica, una funcionalidad o una tarea
  de implementacion.
- Debe evitar terminos demasiado tecnicos, jerga interna o nombres de
  componentes tecnologicos salvo que sean imprescindibles para el negocio.
- Debe ser coherente con una iniciativa de **El Negocio**.

Componentes de interfaz:

- Titulo: `1. Vision`
- Instrucciones: texto de reglas del paso.
- Campo: `Tus comentarios`, textarea libre.
- Accion: `Procesar`.
- Salida: campo de texto de solo lectura con la respuesta validada del modelo.
- Avance: boton `Estoy conforme, ir al segundo paso`, visible luego de procesar
  correctamente el paso.
- Al procesar correctamente este paso, el selector global `Modelo a utilizar`
  debe quedar deshabilitado para el resto de la sesion.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/vision_response.md`.

## Paso 2: Target

Estado: implementado.

Proposito: definir el grupo beneficiario objetivo de la iniciativa a partir de
una lista de Equipos, Gerencias, Sectores o grupos de usuarios finales
beneficiarios, identificando la unidad o area de negocio beneficiaria y el
segmento especifico dentro de ella.

Reglas:

- Debe responder a que unidad o area de negocio se beneficiara.
- No puede ser una lista vacia.
- No puede contener beneficiarios, unidades, areas o segmentos repetidos.
- Cada item debe representar un Equipo, Gerencia, Sector o grupo de usuarios
  finales beneficiarios.
- Debe identificar el segmento o grupo especifico al que apunta la iniciativa.
- Los equipos que trabajan desarrollando la iniciativa no pueden ser los mismos
  que figuran como beneficiarios.
- Debe mantener coherencia con la Vision definida en el paso 1.

Componentes de interfaz:

- Titulo: `2. Target`
- Instrucciones: texto de reglas del paso.
- Campo de texto: `Equipo, Gerencia, Sector o grupo beneficiario`, para escribir
  o editar un nombre.
- Accion: boton `agregar`, que adiciona el valor escrito a la lista de
  beneficiarios objetivo.
- Accion: boton `cargar seleccionado`, que copia el item seleccionado al campo
  de texto para editarlo.
- Accion: boton `actualizar`, que reemplaza el item seleccionado por el texto
  editado.
- Lista: `Lista de beneficiarios objetivo`, editable mediante seleccion.
- Accion: boton `eliminar`, que remueve de la lista el item seleccionado.
- Accion: `Procesar`.
- Salida: campo de texto de solo lectura con la respuesta validada del modelo.
- Avance: boton `Estoy conforme, ir al tercer paso`, visible luego de procesar
  correctamente el paso.
- Retroceso: boton `Volver al paso anterior`, que vuelve al paso 1 sin perder
  los datos ingresados en el paso 2.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/target_response.md`.

## Paso Reemplazado: Usuarios Beneficiarios

Estado: reemplazado por Target.

Proposito original: establecer quienes seran los usuarios beneficiarios de la
solucion a implementar, expresados como Equipos, Gerencias o Sectores.

Decision: este paso no debe implementarse como flujo independiente. Queda
reemplazado por `specs/steps/02_target.json`, porque el paso Target ya define la
unidad o area beneficiaria y el segmento o grupo especifico objetivo.

Reglas:

- No debe existir un prompt separado para usuarios beneficiarios.
- No debe generarse `feedback/beneficiary_users_response.md`.
- Toda validacion sobre grupos beneficiarios debe concentrarse en el paso 2
  Target.

## Paso 3: Valor De Negocio

Estado: implementado.

Proposito: obtener una lista de items, escritos como oraciones, que expresen el
valor de negocio esperado de la solucion y validarlos contra los criterios de
beneficio economico, eficiencia, automatizacion e impacto en indicadores.

Reglas:

- Debe existir al menos un item de valor de negocio.
- La lista no puede estar vacia.
- No pueden existir items repetidos.
- Cada item debe estar escrito como una oracion clara.
- Los items deben expresar beneficio economico, eficiencia en FTE,
  automatizacion, NPS, conversion u otro indicador cuantificable.
- Si falta una metrica, se debe indicar que dato falta para poder calcularla.
- Los items deben mantener coherencia con la Vision y el Target definidos
  previamente.

Componentes de interfaz:

- Titulo: `3. Valor de negocio`
- Instrucciones: texto de reglas del paso.
- Campo de texto: `Item de valor de negocio`, para escribir una oracion.
- Accion: boton `agregar`, que adiciona la oracion a la lista de items.
- Accion: boton `cargar seleccionado`, que copia el item seleccionado al campo
  de texto para editarlo.
- Accion: boton `actualizar`, que reemplaza el item seleccionado por el texto
  editado.
- Lista: `Lista de items de valor de negocio`, editable mediante seleccion.
- Accion: boton `eliminar`, que remueve de la lista el item seleccionado.
- Accion: boton `Procesar`, que envia la lista de items al proveedor LLM junto
  con el contexto disponible.
- Salida: campo de texto de solo lectura con la respuesta validada del modelo.
- Avance: boton `Estoy conforme, ir al cuarto paso`, visible luego de procesar
  correctamente el paso.
- Retroceso: boton `Volver al paso anterior`, que vuelve al paso 2 sin perder
  los datos ingresados en el paso 3.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/business_value_response.md`.

Comportamiento de lista:

- No se deben agregar valores vacios.
- No se deben agregar duplicados exactos ni equivalentes por mayusculas,
  minusculas o espacios.
- La accion `actualizar` requiere un item seleccionado y un texto no vacio.
- La accion `eliminar` requiere un item seleccionado.
- La accion `Procesar` requiere al menos un item en la lista.
- La respuesta del modelo debe guardarse en `feedback`.

## Paso 4: Necesidad

Estado: implementado.

Proposito: obtener una lista editable de items que describan la problematica o
necesidad de la solucion a implementar, indicando problemas actuales a resolver
u oportunidades de innovacion a capturar.

Reglas:

- Debe existir al menos un item de necesidad.
- La lista no puede estar vacia.
- No pueden existir items repetidos.
- Cada item debe estar escrito como una oracion clara.
- Cada item debe describir un problema actual a resolver o una oportunidad de
  innovacion a capturar.
- Cada item debe responder que problema se busca resolver o que innovacion se
  requiere.
- Los items deben mantener coherencia con la Vision, el Target y el Valor de
  Negocio definidos previamente.

Componentes de interfaz:

- Titulo: `4. Necesidad`
- Instrucciones: texto de reglas del paso.
- Campo de texto: `Item de necesidad`, para escribir o editar una oracion.
- Accion: boton `agregar`, que adiciona la oracion a la lista de items.
- Accion: boton `cargar seleccionado`, que copia el item seleccionado al campo
  de texto para editarlo.
- Accion: boton `actualizar`, que reemplaza el item seleccionado por el texto
  editado.
- Lista: `Lista de items de necesidad`, editable mediante seleccion.
- Accion: boton `eliminar`, que remueve de la lista el item seleccionado.
- Accion: boton `Procesar`, que envia la lista de items al proveedor LLM junto
  con el contexto disponible.
- Salida: campo de texto de solo lectura con la respuesta validada del modelo.
- Retroceso: boton `Volver al paso anterior`, que vuelve al paso 3 sin perder
  los datos ingresados en el paso 4.
- Avance: boton `Estoy conforme, ir al quinto paso`, visible luego de procesar
  correctamente el paso.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/need_response.md`.

Comportamiento de lista:

- No se deben agregar valores vacios.
- No se deben agregar duplicados exactos ni equivalentes por mayusculas,
  minusculas o espacios.
- La accion `actualizar` requiere un item seleccionado y un texto no vacio.
- La accion `eliminar` requiere un item seleccionado.
- La accion `Procesar` requiere al menos un item en la lista.
- La respuesta del modelo debe guardarse en `feedback`.

## Proximos pasos pendientes

## Paso 5: Producto / Proceso / Servicio

Estado: implementado.

Proposito: obtener una lista editable de items que describan la solucion
propuesta, indicando que Producto, Proceso o Servicio se creara, incorporara o
modificara para resolver la necesidad.

Reglas:

- Debe responder como se propone resolverlo.
- Debe indicar que Producto, Proceso o Servicio se creara, incorporara o
  modificara.
- La lista no puede estar vacia.
- No pueden existir items repetidos.
- Cada item debe estar escrito como una oracion clara.
- La terminologia tecnica utilizada debe ser entendible para un Jefe o Gerente.
- Debe mantener coherencia con la Vision, el Target, el Valor de Negocio y la
  Necesidad definidos previamente.

Componentes de interfaz:

- Titulo: `5. Producto / Proceso / Servicio`
- Instrucciones: texto de reglas del paso.
- Campo de texto: `Item de Producto / Proceso / Servicio`, para escribir o
  editar una oracion.
- Accion: boton `agregar`, que adiciona la oracion a la lista de items.
- Accion: boton `cargar seleccionado`, que copia el item seleccionado al campo
  de texto para editarlo.
- Accion: boton `actualizar`, que reemplaza el item seleccionado por el texto
  editado.
- Lista: `Lista de items de Producto / Proceso / Servicio`, editable mediante
  seleccion.
- Accion: boton `eliminar`, que remueve de la lista el item seleccionado.
- Accion: boton `Procesar`, que envia la lista de items al proveedor LLM junto
  con el contexto disponible.
- Salida: campo de texto de solo lectura con la respuesta validada del modelo.
- Retroceso: boton `Volver al paso anterior`, que vuelve al paso 4 sin perder
  los datos ingresados en el paso 5.
- Avance: boton `Estoy conforme, ir al paso 5.1`, visible luego de procesar
  correctamente el paso.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/pps_response.md`.

## Paso 5.1: Soluciones Similares

Estado: implementado.

Proposito: obtener una lista editable de soluciones similares, competidores o
alternativas comparables, identificando fortalezas y debilidades cuando aplique.

Reglas:

- La lista no puede estar vacia.
- La respuesta `No aplica` es valida y debe estar disponible por defecto.
- No pueden existir items repetidos.
- Cada item debe describir una solucion similar, competidor o alternativa
  comparable, salvo cuando sea `No aplica`.
- Debe mantener coherencia con los pasos previos.

Componentes de interfaz:

- Titulo: `5.1. Soluciones Similares`
- Campo de texto para escribir o editar una oracion.
- Acciones: `agregar`, `cargar seleccionado`, `actualizar`, `eliminar`.
- Lista editable de soluciones similares.
- Accion: boton `Procesar`.
- Retroceso: boton `Volver al paso anterior`, que vuelve al paso 5.
- Avance: boton `Estoy conforme, ir al paso 5.2`.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/competition_response.md`.

## Paso 5.2: Canales y Medios

Estado: implementado.

Proposito: obtener una lista editable de canales y medios para llegar a los
beneficiarios de la solucion.

Reglas:

- La lista no puede estar vacia.
- No pueden existir items repetidos.
- Cada item debe describir un canal o medio concreto.
- Cada item debe explicar como se llegara a los beneficiarios.
- Debe mantener coherencia con el Target y los pasos previos.

Componentes de interfaz:

- Titulo: `5.2. Canales y Medios`
- Campo de texto para escribir o editar una oracion.
- Acciones: `agregar`, `cargar seleccionado`, `actualizar`, `eliminar`.
- Lista editable de canales y medios.
- Accion: boton `Procesar`.
- Retroceso: boton `Volver al paso anterior`, que vuelve al paso 5.1.
- Avance: boton `Estoy conforme, ir al sexto paso`.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/channels_response.md`.

## Paso 6: Inversion

Estado: implementado.

Proposito: capturar la inversion estimada para desarrollar o implementar la
solucion, incluyendo equipos participantes, horas, roles, FTEs, totales y fechas
tentativas. En este paso, presupuesto se interpreta como una idea macro de
esfuerzo: cantidad de horas, FTEs y equipos o personas participantes. No se
requiere estimar montos economicos.

Reglas:

- La lista de equipos participantes no puede estar vacia.
- Cada item debe estar compuesto por Nombre de Equipo, Cantidad de horas, Rol a
  desempenar y FTE.
- Nombre de Equipo no puede estar vacio.
- Cantidad de horas debe ser un numero entero mayor a cero.
- Rol a desempenar debe ser un texto explicativo a nivel macro.
- FTE es de solo lectura y debe calcularse como `Cantidad de horas / 160`.
- No pueden existir equipos repetidos; la comparacion se realiza solamente por
  Nombre de Equipo.
- Total Horas debe calcularse sumando todas las horas cargadas.
- Total FTEs debe calcularse como `Total Horas / 160`.
- El presupuesto debe interpretarse como esfuerzo estimado en horas, FTEs y
  equipos o personas participantes, no como monto economico.
- Fecha Tentativa inicio y Fecha Tentativa fin deben usar formato `AAAA-MM-DD`.
- Fecha Tentativa fin no deberia ser anterior a Fecha Tentativa inicio.

Componentes de interfaz previstos:

- Titulo: `6. Inversion`.
- Campo: `Nombre de Equipo`.
- Campo: `Cantidad de horas`.
- Campo: `Rol a desempenar`.
- Campo de solo lectura: `FTE`, calculado como `Cantidad de horas / 160`.
- Accion: boton `agregar`, que adiciona el item compuesto a la lista.
- Accion: boton `cargar seleccionado`, que copia el item seleccionado a los
  campos para modificarlo.
- Accion: boton `modificar`, que reemplaza el item seleccionado por los valores
  editados.
- Accion: boton `eliminar`, que remueve el item seleccionado.
- Lista: `Lista de equipos participantes`.
- Campo de solo lectura `Estimacion` con:
  - `Total Horas: XXXX`
  - `Total FTEs: XXXX`
- Campo fecha: `Fecha Tentativa inicio`, formato `AAAA-MM-DD`.
- Campo fecha: `Fecha Tentativa fin`, formato `AAAA-MM-DD`.
- Accion: boton `Procesar`, que envia la lista, totales y fechas al proveedor
  LLM junto con el contexto disponible.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/investment_response.md`.

Logica de calculo:

- `FTE por item = Cantidad de horas / 160`.
- `Total Horas = suma de Cantidad de horas de todos los items`.
- `Total FTEs = Total Horas / 160`.
- Los calculos deben realizarse en funciones Python reutilizables para que se
  actualicen al agregar, modificar o eliminar items.

Preguntas abiertas:

- Confirmar si los FTEs deben mostrarse con 2 decimales.
- Confirmar si un mismo equipo puede aparecer mas de una vez con roles
  distintos. La regla actual no lo permite porque la deteccion de duplicados se
  realiza solo por Nombre de Equipo.

## Paso 7: Flujos de Ingresos y/o Beneficios

Estado: especificado.

Proposito: obtener una lista editable de items que describan ingresos y/o
beneficios esperados para construir una vision preliminar del caso de negocio.
Si no existen ingresos directos, los items pueden expresar ahorro, eficiencia,
mejora de experiencia u otro impacto cuantificable.

Reglas:

- La lista no puede estar vacia.
- No pueden existir items repetidos.
- Cada item debe estar escrito como una oracion clara.
- Cada item debe expresar un ingreso, ahorro, eficiencia, mejora de experiencia
  u otro beneficio esperado.
- Cada item debe intentar cuantificar el beneficio o indicar que dato falta para
  poder cuantificarlo.
- Cuando el beneficio sea de experiencia o UX, debe indicar a cuantos individuos
  afecta o que poblacion se veria impactada.
- La terminologia debe ser entendible para un Jefe o Gerente.
- Debe mantener coherencia con la Vision, Target, Valor de Negocio, Necesidad,
  Solucion Propuesta, Canales e Inversion definidos previamente.

Componentes de interfaz previstos:

- Titulo: `7. Flujos de Ingresos y/o Beneficios`.
- Campo de texto: `Item de ingreso o beneficio`, para escribir o editar una
  oracion.
- Accion: boton `agregar`, que adiciona la oracion a la lista de items.
- Accion: boton `cargar seleccionado`, que copia el item seleccionado al campo
  de texto para editarlo.
- Accion: boton `actualizar`, que reemplaza el item seleccionado por el texto
  editado.
- Lista: `Lista de ingresos y/o beneficios`, editable mediante seleccion.
- Accion: boton `eliminar`, que remueve de la lista el item seleccionado.
- Accion: boton `Procesar`, que envia la lista de items al proveedor LLM junto
  con el contexto disponible.
- Salida: campo de texto de solo lectura con la respuesta validada del modelo.
- Retroceso: boton `Volver al paso anterior`, que vuelve al paso 6 sin perder
  los datos ingresados en el paso 7.
- Avance: boton `Estoy conforme, ir al octavo paso`, visible luego de procesar
  correctamente el paso, que navega al tab global `Generar Documento`.
- Persistencia: la respuesta del modelo debe guardarse en
  `feedback/revenue_benefits_response.md`.

## Tab global: Generar Documento

Estado: implementado.

Proposito: generar el documento Markdown consolidado del PVB a partir de las
respuestas disponibles en `feedback`, sin depender de un paso particular.

Componentes de interfaz previstos:

- Tab: `Generar Documento`.
- Titulo: `Generar Documento`.
- Accordion: `Documento final`, abierto por defecto.
- Campo de texto: `Nombre sugerido del archivo`, precompletado con el nombre
  base por defecto.
- Accion: boton `Generar documento Markdown`.
- Salida: campo `Documento generado`, de solo lectura.
- Accordion: `Detalle del documento`, cerrado por defecto.
- Salida de detalle: `Ruta del archivo`, de solo lectura.

Reglas:

- Este tab debe estar separado del paso 7 porque la generacion del documento es
  una accion global sobre el PVB completo.
- La accion debe consolidar las ultimas respuestas disponibles en `feedback`.
- Si faltan pasos, el documento debe incluirlos como pendientes.
- La accion no debe llamar al proveedor LLM.

Los pasos 8 a 9 se agregaran siguiendo el mismo patron:

- especificacion estructurada en `specs/steps`
- prompt operativo en `data`
- renderizado guiado en la interfaz
- persistencia de la ultima respuesta generada en `feedback`
