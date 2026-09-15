# Product Vision Board Builder

Asistente en Python para generar y validar un Product Vision Board.

## Configuracion

1. Completar `.env`:

```env
OPENAI_API_KEY=tu-api-key
GEMINI_API_KEY=tu-api-key-gemini
SSL_CERT_FILE=C:\certs\netskope.pem
REQUESTS_CA_BUNDLE=C:\certs\netskope.pem
```

El modelo se selecciona desde la interfaz en el paso `1. Vision`. Las opciones
disponibles son `OpenAI GPT-4o mini`, `OpenAI GPT-5 mini`, `OpenAI GPT-5`,
`Gemini 2.5 Flash-Lite` y `Gemini 3.5 Flash`. Por defecto se usa
`OpenAI GPT-5` para mantener el comportamiento original.

2. Instalar dependencias:

```powershell
uv sync
```

## Ejecucion manual

Desde una terminal PowerShell, ubicarse en la carpeta del proyecto:

```powershell
cd "C:\Users\_diegoz\_mini_pvb\pvb-builder-python"
```

Si es la primera ejecucion, o si cambiaron las dependencias, instalar el entorno:

```powershell
uv sync
```

Ejecutar el asistente:

```powershell
uv run python app.py
```

Luego abrir en el navegador:

```text
http://127.0.0.1:7860
```

Para detener el asistente, presionar `Ctrl + C` en la terminal donde se esta
ejecutando.

La interfaz implementa actualmente:

- `1. Vision`
- `2. Target`
- `3. Valor de negocio`
- `4. Necesidad`
- `5. Producto / Proceso / Servicio`
- `5.1. Soluciones Similares`
- `5.2. Canales y Medios`

El paso `3. Usuarios beneficiarios` fue reemplazado por `2. Target`; no tiene
prompt ni flujo independiente.

Nota: la app usa `share=False` para ejecutarse solo localmente. En algunos
entornos corporativos, el modulo de tuneles publicos de Gradio puede ser
cuarentenado por herramientas de seguridad; no es necesario para esta app local.

## Especificacion

La especificacion funcional vive en `specs/`.

- `specs/pvb_assistant_spec.md`: vision general del asistente, arquitectura y
  flujo por paso.
- `specs/steps/01_vision.json`: especificacion estructurada del paso 1.
- `specs/steps/02_target.json`: especificacion estructurada del paso 2.
- `specs/steps/03_business_value.json`: especificacion estructurada del paso 3.
- `specs/steps/04_need.json`: especificacion estructurada del paso 4.
- `specs/steps/05_pps.json`: especificacion estructurada del paso 5.
- `specs/steps/05_1_competition.json`: especificacion estructurada del paso 5.1.
- `specs/steps/05_2_channels.json`: especificacion estructurada del paso 5.2.
- `specs/steps/03_beneficiary_users.json`: especificacion historica del paso
  reemplazado por Target.

Los prompts y contexto que se envian al modelo viven en `data/`.
Las respuestas generadas por el modelo se guardan en `feedback/`.
La interfaz debe permitir volver al paso anterior sin perder los datos cargados
durante la sesion.

## Logs

Cada llamada al LLM agrega un registro JSONL en `logs/openai_interactions.jsonl`.
El registro incluye request, respuesta, tokens y costo estimado cuando el modelo
tiene tarifa configurada en `data/openai_pricing.json`.
