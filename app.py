from __future__ import annotations

import os
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FEEDBACK_DIR = BASE_DIR / "feedback"
LOGS_DIR = BASE_DIR / "logs"
SPECS_DIR = BASE_DIR / "specs"
VISION_SPEC_PATH = SPECS_DIR / "steps" / "01_vision.json"
TARGET_SPEC_PATH = SPECS_DIR / "steps" / "02_target.json"
BUSINESS_VALUE_SPEC_PATH = SPECS_DIR / "steps" / "03_business_value.json"
NEED_SPEC_PATH = SPECS_DIR / "steps" / "04_need.json"
PPS_SPEC_PATH = SPECS_DIR / "steps" / "05_pps.json"
COMPETITION_SPEC_PATH = SPECS_DIR / "steps" / "05_1_competition.json"
CHANNELS_SPEC_PATH = SPECS_DIR / "steps" / "05_2_channels.json"
INVESTMENT_SPEC_PATH = SPECS_DIR / "steps" / "06_investment.json"
REVENUE_BENEFITS_SPEC_PATH = SPECS_DIR / "steps" / "07_revenue_benefits.json"
BUSINESS_CONTEXT_PATH = DATA_DIR / "business_context.md"
OPENAI_PRICING_PATH = DATA_DIR / "openai_pricing.json"
OPENAI_INTERACTIONS_LOG = LOGS_DIR / "openai_interactions.jsonl"
SESSIONS_LOG_PATH = LOGS_DIR / "sesiones.jsonl"
DEFAULT_EXPORT_BASENAME = "pvb-example"
DEFAULT_LLM_MODEL_ID = "gemini:gemini-2.5-flash-lite"
SESSION_STATE_WARNING = "<!-- No modificar esta sección para mantener el estado. -->"
SESSION_STATE_FENCE = "```json pvb-session-state"
LLM_MODEL_OPTIONS = {
    "openai:gpt-4o-mini": {
        "label": "OpenAI GPT-4o mini",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
    "openai:gpt-5-mini": {
        "label": "OpenAI GPT-5 mini",
        "provider": "openai",
        "model": "gpt-5-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
    "openai:gpt-5": {
        "label": "OpenAI GPT-5",
        "provider": "openai",
        "model": "gpt-5",
        "api_key_env": "OPENAI_API_KEY",
    },
    "gemini:gemini-2.5-flash-lite": {
        "label": "Gemini 2.5 Flash-Lite",
        "provider": "gemini",
        "model": "gemini-2.5-flash-lite",
        "api_key_env": "GEMINI_API_KEY",
    },
    "gemini:gemini-3.5-flash": {
        "label": "Gemini 3.5 Flash",
        "provider": "gemini",
        "model": "gemini-3.5-flash",
        "api_key_env": "GEMINI_API_KEY",
    },
}
LLM_MODEL_DROPDOWN_CHOICES = [
    (model_config["label"], model_id)
    for model_id, model_config in LLM_MODEL_OPTIONS.items()
]

load_dotenv(BASE_DIR / ".env")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_step_spec(path: Path) -> dict:
    return json.loads(read_text(path))


VISION_SPEC = load_step_spec(VISION_SPEC_PATH)
TARGET_SPEC = load_step_spec(TARGET_SPEC_PATH)
BUSINESS_VALUE_SPEC = load_step_spec(BUSINESS_VALUE_SPEC_PATH)
NEED_SPEC = load_step_spec(NEED_SPEC_PATH)
PPS_SPEC = load_step_spec(PPS_SPEC_PATH)
COMPETITION_SPEC = load_step_spec(COMPETITION_SPEC_PATH)
CHANNELS_SPEC = load_step_spec(CHANNELS_SPEC_PATH)
INVESTMENT_SPEC = load_step_spec(INVESTMENT_SPEC_PATH)
REVENUE_BENEFITS_SPEC = load_step_spec(REVENUE_BENEFITS_SPEC_PATH)


SESSION_STEP_DEFINITIONS = [
    {
        "id": VISION_SPEC["id"],
        "title": VISION_SPEC["title"],
        "feedback_file_name": "vision_response.md",
    },
    {
        "id": TARGET_SPEC["id"],
        "title": TARGET_SPEC["title"],
        "feedback_file_name": "target_response.md",
    },
    {
        "id": BUSINESS_VALUE_SPEC["id"],
        "title": BUSINESS_VALUE_SPEC["title"],
        "feedback_file_name": "business_value_response.md",
    },
    {
        "id": NEED_SPEC["id"],
        "title": NEED_SPEC["title"],
        "feedback_file_name": "need_response.md",
    },
    {
        "id": PPS_SPEC["id"],
        "title": PPS_SPEC["title"],
        "feedback_file_name": "pps_response.md",
    },
    {
        "id": COMPETITION_SPEC["id"],
        "title": COMPETITION_SPEC["title"],
        "feedback_file_name": "competition_response.md",
    },
    {
        "id": CHANNELS_SPEC["id"],
        "title": CHANNELS_SPEC["title"],
        "feedback_file_name": "channels_response.md",
    },
    {
        "id": INVESTMENT_SPEC["id"],
        "title": INVESTMENT_SPEC["title"],
        "feedback_file_name": "investment_response.md",
    },
    {
        "id": REVENUE_BENEFITS_SPEC["id"],
        "title": REVENUE_BENEFITS_SPEC["title"],
        "feedback_file_name": "revenue_benefits_response.md",
    },
]
FINAL_DOCUMENT_STEPS = [
    (step["title"], step["feedback_file_name"])
    for step in SESSION_STEP_DEFINITIONS
]
STEP_BY_ID = {step["id"]: step for step in SESSION_STEP_DEFINITIONS}
STEP_ID_BY_FEEDBACK_FILE = {
    step["feedback_file_name"]: step["id"] for step in SESSION_STEP_DEFINITIONS
}
CONTEXT_DECISION_HEADINGS = {
    "vision": ["Vision propuesta"],
    "target": ["Target propuesto"],
    "business_value": ["Items validados", "Versiones corregidas (propuesta)"],
    "need": ["Necesidades validadas"],
    "pps": ["Soluciones validadas"],
    "competition": ["Soluciones similares validadas"],
    "channels": ["Canales y medios validados"],
    "investment": ["Inversion validada", "Totales"],
    "revenue_benefits": ["Ingresos y beneficios validados"],
}
CONTEXT_GUIDANCE_HEADINGS = {
    step["id"]: ["Ajustes sugeridos"] for step in SESSION_STEP_DEFINITIONS
}
MAX_CONTEXT_FIELD_CHARS = 1600


def project_path(relative_path: str) -> Path:
    return BASE_DIR / relative_path


def save_latest_response(content: str, output_path: Path, title: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        f"### Ultima respuesta {title}\n\nGenerada: {timestamp}\n\n{content}\n",
        encoding="utf-8",
    )


def object_to_dict(value: object) -> dict:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    if hasattr(value, "__dict__"):
        return vars(value)
    return {}


def get_nested_int(data: dict, *keys: str) -> int:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return 0
        current = current.get(key)
    return current if isinstance(current, int) else 0


def extract_token_metrics(response: object) -> dict:
    usage = object_to_dict(getattr(response, "usage", None))
    if not usage:
        usage = object_to_dict(getattr(response, "usage_metadata", None))

    input_tokens = usage.get("input_tokens", usage.get("prompt_token_count", 0)) or 0
    output_tokens = (
        usage.get("output_tokens", usage.get("candidates_token_count", 0)) or 0
    )
    total_tokens = (
        usage.get("total_tokens", usage.get("total_token_count", input_tokens + output_tokens))
        or 0
    )
    cached_input_tokens = get_nested_int(usage, "input_tokens_details", "cached_tokens")
    reasoning_tokens = get_nested_int(usage, "output_tokens_details", "reasoning_tokens")

    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "billable_input_tokens": max(input_tokens - cached_input_tokens, 0),
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
        "raw_usage": usage,
    }


def resolve_llm_model(selected_model_id: str | None = None) -> dict:
    model_id = selected_model_id or DEFAULT_LLM_MODEL_ID
    return LLM_MODEL_OPTIONS.get(model_id, LLM_MODEL_OPTIONS[DEFAULT_LLM_MODEL_ID])


def load_google_genai():
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "Falta instalar la dependencia google-genai. Ejecuta `uv sync` y volve a intentar."
        ) from exc
    return genai


def calculate_cost(model: str, token_metrics: dict) -> dict:
    pricing = json.loads(read_text(OPENAI_PRICING_PATH))
    model_pricing = pricing["models"].get(model)
    if not model_pricing:
        return {
            "currency": pricing["currency"],
            "estimated_total": None,
            "pricing_found": False,
            "pricing_note": f"No hay tarifa configurada para el modelo {model}.",
        }

    billable_input_cost = (
        token_metrics["billable_input_tokens"] * model_pricing["input"] / 1_000_000
    )
    cached_input_cost = (
        token_metrics["cached_input_tokens"] * model_pricing["cached_input"] / 1_000_000
    )
    output_cost = token_metrics["output_tokens"] * model_pricing["output"] / 1_000_000
    total = billable_input_cost + cached_input_cost + output_cost

    return {
        "currency": pricing["currency"],
        "estimated_total": round(total, 8),
        "billable_input_cost": round(billable_input_cost, 8),
        "cached_input_cost": round(cached_input_cost, 8),
        "output_cost": round(output_cost, 8),
        "pricing_found": True,
        "pricing_unit": pricing["unit"],
        "pricing_source": pricing["source"],
        "pricing_updated_at": pricing["updated_at"],
    }


def append_openai_log(entry: dict) -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    with OPENAI_INTERACTIONS_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_openai_interaction(
    *,
    step_id: str,
    provider: str,
    model: str,
    instructions: str,
    user_input: str,
    response: object,
    output: str,
) -> None:
    token_metrics = extract_token_metrics(response)
    cost_metrics = calculate_cost(model, token_metrics)
    entry = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "step_id": step_id,
        "provider": provider,
        "model": model,
        "request": {
            "instructions": instructions,
            "input": user_input,
        },
        "response": {
            "id": getattr(response, "id", None),
            "output_text": output,
        },
        "metrics": {
            "tokens": token_metrics,
            "cost": cost_metrics,
        },
    }
    append_openai_log(entry)


def build_llm_instructions(
    step_spec: dict,
    extra_context: list[str] | None = None,
) -> str:
    prompt_path = project_path(step_spec["prompt_path"])
    instruction_parts = [
        "Sos un asistente experto en Product Vision Boards para iniciativas de salud.",
        read_text(BUSINESS_CONTEXT_PATH),
        read_text(prompt_path),
    ]
    if extra_context:
        instruction_parts.extend(extra_context)
    return "\n\n".join(instruction_parts)


def call_openai_model(
    *,
    api_key: str,
    model: str,
    instructions: str,
    user_input: str,
) -> tuple[object, str]:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=user_input,
    )
    return response, response.output_text.strip()


def call_gemini_model(
    *,
    api_key: str,
    model: str,
    instructions: str,
    user_input: str,
) -> tuple[object, str]:
    genai = load_google_genai()
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user_input,
        config={"system_instruction": instructions},
    )
    return response, getattr(response, "text", "").strip()


def call_openai_step(
    step_spec: dict,
    user_input: str,
    extra_context: list[str] | None = None,
    selected_model_id: str | None = None,
) -> str:
    selected_model = resolve_llm_model(selected_model_id)
    api_key_env = selected_model["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        return (
            f"Falta configurar {api_key_env} en el archivo .env. "
            "Cargala y volve a presionar Procesar."
        )

    provider = selected_model["provider"]
    model = selected_model["model"]
    output_path = project_path(step_spec["output_path"])
    instructions = build_llm_instructions(step_spec, extra_context)
    if provider == "openai":
        response, output = call_openai_model(
            api_key=api_key,
            model=model,
            instructions=instructions,
            user_input=user_input,
        )
    elif provider == "gemini":
        response, output = call_gemini_model(
            api_key=api_key,
            model=model,
            instructions=instructions,
            user_input=user_input,
        )
    else:
        return f"Proveedor LLM no soportado: {provider}."

    save_latest_response(output, output_path, step_spec["title"])
    log_openai_interaction(
        step_id=step_spec["id"],
        provider=provider,
        model=model,
        instructions=instructions,
        user_input=user_input,
        response=response,
        output=output,
    )
    return output


def build_vision(user_comments: str, selected_model_id: str | None = None) -> str:
    comments = user_comments.strip()
    if not comments:
        return "Agrega tus comentarios para poder generar y validar la Vision."

    user_input = f"Comentarios del usuario:\n{comments}"
    return call_openai_step(
        VISION_SPEC,
        user_input,
        selected_model_id=selected_model_id,
    )


def process_vision(user_comments: str, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_vision(user_comments, selected_model_id)
    can_continue = bool(user_comments.strip()) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


def process_vision_and_lock_model(
    user_comments: str,
    selected_model_id: str | None = None,
) -> tuple[str, gr.Button, gr.Dropdown]:
    result, next_step_update = process_vision(user_comments, selected_model_id)
    can_continue = bool(next_step_update.get("visible"))
    model_update = gr.update(
        value=selected_model_id or DEFAULT_LLM_MODEL_ID,
        interactive=not can_continue,
    )
    return result, next_step_update, model_update


def normalize_for_duplicate(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def has_duplicates(values: list[str]) -> bool:
    normalized_values = [normalize_for_duplicate(value) for value in values if value.strip()]
    return len(normalized_values) != len(set(normalized_values))


def extract_list_like_lines(value: str) -> list[str]:
    lines = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        line = line.lstrip("-*0123456789. )").strip()
        if line:
            lines.append(line)
    return lines


def add_list_item(item: str, items: list[str] | None) -> tuple[list[str], str, gr.Dropdown, str]:
    current_items = list(items or [])
    normalized_item = item.strip()
    current_normalized_items = {
        normalize_for_duplicate(current_item) for current_item in current_items
    }
    if (
        normalized_item
        and normalize_for_duplicate(normalized_item) not in current_normalized_items
    ):
        current_items.append(normalized_item)
    return (
        current_items,
        format_items(current_items),
        gr.update(choices=current_items, value=None),
        "",
    )


def delete_list_item(selected_item: str, items: list[str] | None) -> tuple[list[str], str, gr.Dropdown, str]:
    current_items = [item for item in list(items or []) if item != selected_item]
    return (
        current_items,
        format_items(current_items),
        gr.update(choices=current_items, value=None),
        "",
    )


def build_target(items: list[str] | None, selected_model_id: str | None = None) -> str:
    current_items = [item.strip() for item in list(items or []) if item.strip()]
    if not current_items:
        return "Agrega al menos un Equipo, Gerencia, Sector o grupo beneficiario para poder procesar el Target."
    if has_duplicates(current_items):
        return "El Target no puede contener beneficiarios, unidades, areas o segmentos repetidos."

    item_text = "\n".join(f"- {item}" for item in current_items)
    user_input = f"Beneficiarios objetivo propuestos por el usuario:\n{item_text}"
    return call_openai_step(
        TARGET_SPEC,
        user_input,
        extra_context=load_compact_feedback_context(["vision_response.md"]),
        selected_model_id=selected_model_id,
    )


def process_target(items: list[str] | None, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_target(items, selected_model_id)
    can_continue = bool(items) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


def format_items(items: list[str]) -> str:
    if not items:
        return ""
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def load_selected_item(selected_item: str) -> str:
    return selected_item or ""


def update_list_item(
    selected_item: str,
    updated_item: str,
    items: list[str] | None,
) -> tuple[list[str], str, gr.Dropdown, str]:
    current_items = list(items or [])
    edited_item = updated_item.strip()
    if not selected_item or not edited_item:
        return (
            current_items,
            format_items(current_items),
            gr.update(choices=current_items, value=selected_item or None),
            updated_item,
        )

    updated_items = []
    replaced = False
    for item in current_items:
        if item == selected_item and not replaced:
            updated_items.append(edited_item)
            replaced = True
        else:
            updated_items.append(item)

    if has_duplicates(updated_items):
        return (
            current_items,
            format_items(current_items),
            gr.update(choices=current_items, value=selected_item),
            updated_item,
        )

    return (
        updated_items,
        format_items(updated_items),
        gr.update(choices=updated_items, value=edited_item),
        edited_item,
    )


def load_feedback_context(file_names: list[str]) -> list[str]:
    context = []
    for file_name in file_names:
        path = FEEDBACK_DIR / file_name
        if path.exists():
            context.append(f"Contexto previo desde {path.name}:\n{read_text(path)}")
    return context


def load_previous_feedback() -> list[str]:
    return load_compact_feedback_context(
        [
            "vision_response.md",
            "target_response.md",
        ]
    )


def sanitize_export_basename(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug or DEFAULT_EXPORT_BASENAME


def build_export_filename(
    base_name: str,
    generated_at: datetime | None = None,
) -> str:
    timestamp = (generated_at or datetime.now()).strftime("%y%m%d_%H%M")
    return f"{timestamp}_{sanitize_export_basename(base_name)}.md"


def build_session_filename(
    base_name: str,
    generated_at: datetime | None = None,
) -> str:
    timestamp = (generated_at or datetime.now()).strftime("%y%m%d_%H%M")
    return f"{timestamp}_sesion_{sanitize_export_basename(base_name)}.md"


def build_final_markdown_content(generated_at: datetime | None = None) -> str:
    generated_timestamp = (generated_at or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    sections = [
        "# Product Vision Board",
        "",
        f"Generado: {generated_timestamp}",
        "",
        "Este documento consolida las ultimas respuestas disponibles del asistente.",
    ]

    for title, feedback_file_name in FINAL_DOCUMENT_STEPS:
        feedback_path = FEEDBACK_DIR / feedback_file_name
        sections.extend(["", "---", f"## {title}", ""])
        if feedback_path.exists():
            sections.append(read_text(feedback_path).strip())
        else:
            sections.append(f"_Pendiente: aun no se genero feedback para {title}._")

    return "\n".join(sections).strip() + "\n"


def generate_final_markdown_document(
    base_name: str,
    generated_at: datetime | None = None,
) -> tuple[str, str]:
    generated_at = generated_at or datetime.now()
    filename = build_export_filename(base_name, generated_at)
    output_path = FEEDBACK_DIR / filename
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_final_markdown_content(generated_at),
        encoding="utf-8",
    )
    return f"Documento generado: {output_path}", str(output_path)


def log_session_event(
    action: str,
    file_path: str | Path,
    status: str,
    details: dict | None = None,
    error: Exception | str | None = None,
) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "file_path": str(file_path),
        "status": status,
        "details": details or {},
    }
    if error is not None:
        record["error"] = str(error)
    with SESSIONS_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_validated_session_outputs() -> dict:
    outputs = {}
    for step in SESSION_STEP_DEFINITIONS:
        feedback_path = FEEDBACK_DIR / step["feedback_file_name"]
        if feedback_path.exists():
            content = read_text(feedback_path).strip()
            if content:
                outputs[step["id"]] = content
    return outputs


def extract_markdown_section(content: str, heading: str) -> str:
    lines = content.splitlines()
    heading_pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$")
    next_heading_pattern = re.compile(r"^##\s+\S")
    section_lines = []
    in_section = False
    for line in lines:
        if heading_pattern.match(line.strip()):
            in_section = True
            continue
        if in_section and next_heading_pattern.match(line.strip()):
            break
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines).strip()


def compact_context_field(value: str) -> str:
    compacted = "\n".join(line.rstrip() for line in value.strip().splitlines()).strip()
    if len(compacted) <= MAX_CONTEXT_FIELD_CHARS:
        return compacted
    return (
        compacted[:MAX_CONTEXT_FIELD_CHARS].rstrip()
        + "\n[Contexto truncado: revisar la respuesta completa en la sesion guardada.]"
    )


def extract_context_field(
    content: str,
    headings: list[str],
    fallback_to_full: bool = True,
) -> str:
    sections = [
        extract_markdown_section(content, heading)
        for heading in headings
    ]
    sections = [section for section in sections if section]
    if not sections and fallback_to_full:
        return compact_context_field(content)
    if not sections:
        return ""
    return compact_context_field("\n\n".join(sections))


def build_context_snapshot(validated_outputs: dict | None) -> dict:
    snapshot = {}
    for step in SESSION_STEP_DEFINITIONS:
        step_id = step["id"]
        content = str((validated_outputs or {}).get(step_id, "") or "").strip()
        if not content:
            continue
        decision = extract_context_field(
            content,
            CONTEXT_DECISION_HEADINGS.get(step_id, []),
        )
        guidance = extract_context_field(
            content,
            CONTEXT_GUIDANCE_HEADINGS.get(step_id, []),
            fallback_to_full=False,
        )
        step_snapshot = {
            "title": step["title"],
            "decision": decision,
        }
        if guidance:
            step_snapshot["guidance"] = guidance
        snapshot[step_id] = step_snapshot
    return snapshot


def format_context_snapshot(snapshot: dict, step_ids: list[str] | None = None) -> str:
    selected_ids = step_ids or [step["id"] for step in SESSION_STEP_DEFINITIONS]
    lines = [
        "Contexto canonico compacto del PVB hasta ahora.",
        "Usalo como memoria de trabajo, no como evidencia completa.",
        "No inventes datos: si una metrica, supuesto o alcance no aparece aqui ni en el input del usuario, marcalo como dato pendiente.",
        "No conviertas ajustes sugeridos o preguntas abiertas en hechos confirmados.",
    ]
    for step_id in selected_ids:
        step_snapshot = snapshot.get(step_id)
        if not step_snapshot:
            continue
        lines.extend(
            [
                "",
                f"## {step_snapshot.get('title', step_id)}",
                "Decision canonica:",
                str(step_snapshot.get("decision", "")).strip(),
            ]
        )
        guidance = str(step_snapshot.get("guidance", "") or "").strip()
        if guidance:
            lines.extend(["", "Ajustes, supuestos o datos pendientes:", guidance])
    return "\n".join(lines).strip()


def load_compact_feedback_context(file_names: list[str]) -> list[str]:
    outputs = {}
    for file_name in file_names:
        step_id = STEP_ID_BY_FEEDBACK_FILE.get(file_name)
        path = FEEDBACK_DIR / file_name
        if step_id and path.exists():
            content = read_text(path).strip()
            if content:
                outputs[step_id] = content
    snapshot = build_context_snapshot(outputs)
    if not snapshot:
        return []
    step_ids = [
        STEP_ID_BY_FEEDBACK_FILE[file_name]
        for file_name in file_names
        if file_name in STEP_ID_BY_FEEDBACK_FILE
    ]
    return [format_context_snapshot(snapshot, step_ids)]


def collect_session_validated_outputs(
    vision_output: str,
    target_output: str,
    business_output: str,
    need_output: str,
    pps_output: str,
    competition_output: str,
    channels_output: str,
    investment_output: str,
    revenue_output: str,
) -> dict:
    output_values = {
        "vision": vision_output,
        "target": target_output,
        "business_value": business_output,
        "need": need_output,
        "pps": pps_output,
        "competition": competition_output,
        "channels": channels_output,
        "investment": investment_output,
        "revenue_benefits": revenue_output,
    }
    return {
        step_id: str(content).strip()
        for step_id, content in output_values.items()
        if str(content or "").strip()
    }


def build_session_state(
    session_name: str,
    raw_inputs: dict | None,
    validated_outputs: dict | None,
    selected_model_id: str | None,
    generated_at: datetime,
) -> dict:
    current_outputs = dict(validated_outputs or {})
    context_snapshot = build_context_snapshot(current_outputs)
    completed_steps = [
        step["id"]
        for step in SESSION_STEP_DEFINITIONS
        if step["id"] in current_outputs
    ]
    return {
        "pvb_session": True,
        "version": 1,
        "status": (
            "complete"
            if len(completed_steps) == len(SESSION_STEP_DEFINITIONS)
            else "partial"
        ),
        "generated_at": generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "session_name": session_name or DEFAULT_EXPORT_BASENAME,
        "selected_model_id": selected_model_id or DEFAULT_LLM_MODEL_ID,
        "completed_steps": completed_steps,
        "raw_inputs": raw_inputs or {},
        "validated_outputs": current_outputs,
        "context_snapshot": context_snapshot,
    }


def build_session_readable_sections(validated_outputs: dict | None) -> list[str]:
    sections = []
    current_outputs = dict(validated_outputs or {})
    for step in SESSION_STEP_DEFINITIONS:
        sections.extend(["", "---", f"## {step['title']}", ""])
        if step["id"] in current_outputs:
            sections.append(str(current_outputs[step["id"]]).strip())
        else:
            sections.append(
                f"_Pendiente: aun no se genero feedback para {step['title']}._"
            )
    return sections


def build_session_markdown_content(
    session_name: str,
    raw_inputs: dict | None,
    validated_outputs: dict | None,
    selected_model_id: str | None = None,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now()
    state = build_session_state(
        session_name,
        raw_inputs,
        validated_outputs,
        selected_model_id,
        generated_at,
    )
    state_json = json.dumps(state, ensure_ascii=False, indent=2)
    sections = [
        "---",
        "pvb_session: true",
        "version: 1",
        f"status: {state['status']}",
        f"generated_at: {state['generated_at']}",
        f"session_name: {state['session_name']}",
        "---",
        "",
        "# Product Vision Board - Sesion parcial",
        "",
        SESSION_STATE_WARNING,
        "",
        SESSION_STATE_FENCE,
        state_json,
        "```",
        "",
        "Este documento consolida una sesion guardada del asistente.",
    ]
    sections.extend(build_session_readable_sections(validated_outputs))
    return "\n".join(sections).strip() + "\n"


def generate_session_markdown_document(
    session_name: str,
    raw_inputs: dict | None,
    selected_model_id: str | None = None,
    generated_at: datetime | None = None,
    validated_outputs: dict | None = None,
) -> tuple[str, str]:
    generated_at = generated_at or datetime.now()
    validated_outputs = (
        validated_outputs
        if validated_outputs is not None
        else read_validated_session_outputs()
    )
    filename = build_session_filename(session_name, generated_at)
    output_path = FEEDBACK_DIR / filename
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_session_markdown_content(
            session_name,
            raw_inputs,
            validated_outputs,
            selected_model_id,
            generated_at,
        ),
        encoding="utf-8",
    )
    log_session_event(
        "save_session",
        output_path,
        "success",
        {"completed_steps": len(validated_outputs)},
    )
    return f"Sesion guardada: {output_path}", str(output_path)


def collect_session_raw_inputs(
    vision_comments: str,
    target_items: list[str] | None,
    target_draft_item: str,
    business_items: list[str] | None,
    business_draft_item: str,
    need_items: list[str] | None,
    need_draft_item: str,
    pps_items: list[str] | None,
    pps_draft_item: str,
    competition_items: list[str] | None,
    competition_draft_item: str,
    channels_items: list[str] | None,
    channels_draft_item: str,
    investment_items: list[dict] | None,
    investment_team: str,
    investment_hours: object,
    investment_role: str,
    investment_start_date: str,
    investment_end_date: str,
    revenue_items: list[str] | None,
    revenue_draft_item: str,
) -> dict:
    investment_draft = {}
    if str(investment_team or "").strip() or investment_hours or str(investment_role or "").strip():
        investment_draft = {
            "team_name": str(investment_team or "").strip(),
            "hours": investment_hours,
            "role": str(investment_role or "").strip(),
        }
    return {
        "vision": {
            "comments": str(vision_comments or "").strip(),
        },
        "target": {
            "items": list(target_items or []),
            "draft_item": str(target_draft_item or "").strip(),
        },
        "business_value": {
            "items": list(business_items or []),
            "draft_item": str(business_draft_item or "").strip(),
        },
        "need": {
            "items": list(need_items or []),
            "draft_item": str(need_draft_item or "").strip(),
        },
        "pps": {
            "items": list(pps_items or []),
            "draft_item": str(pps_draft_item or "").strip(),
        },
        "competition": {
            "items": list(competition_items or []),
            "draft_item": str(competition_draft_item or "").strip(),
        },
        "channels": {
            "items": list(channels_items or []),
            "draft_item": str(channels_draft_item or "").strip(),
        },
        "investment": {
            "items": list(investment_items or []),
            "draft_item": investment_draft,
            "start_date": str(investment_start_date or "").strip(),
            "end_date": str(investment_end_date or "").strip(),
        },
        "revenue_benefits": {
            "items": list(revenue_items or []),
            "draft_item": str(revenue_draft_item or "").strip(),
        },
    }


def extract_session_state(content: str) -> dict:
    marker_index = content.find(SESSION_STATE_FENCE)
    if marker_index == -1:
        raise ValueError("El archivo no contiene un bloque pvb-session-state.")
    json_start = marker_index + len(SESSION_STATE_FENCE)
    json_end = content.find("\n```", json_start)
    if json_end == -1:
        raise ValueError("El bloque pvb-session-state no esta cerrado.")
    state_text = content[json_start:json_end].strip()
    state = json.loads(state_text)
    if not isinstance(state, dict) or state.get("pvb_session") is not True:
        raise ValueError("El bloque de estado no corresponde a una sesion PVB.")
    if state.get("version") != 1:
        raise ValueError("La version de sesion no es compatible.")
    if not isinstance(state.get("raw_inputs"), dict):
        raise ValueError("La sesion no contiene raw_inputs validos.")
    if not isinstance(state.get("validated_outputs"), dict):
        raise ValueError("La sesion no contiene validated_outputs validos.")
    if not isinstance(state.get("context_snapshot"), dict):
        state["context_snapshot"] = build_context_snapshot(state["validated_outputs"])
    return state


def replace_active_feedback(validated_outputs: dict) -> tuple[int, int]:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    restored_count = 0
    cleared_count = 0
    for step in SESSION_STEP_DEFINITIONS:
        feedback_path = FEEDBACK_DIR / step["feedback_file_name"]
        content = str(validated_outputs.get(step["id"], "")).strip()
        if content:
            feedback_path.write_text(content + "\n", encoding="utf-8")
            restored_count += 1
        elif feedback_path.exists():
            feedback_path.unlink()
            cleared_count += 1
    return restored_count, cleared_count


def restore_session_from_path(session_path: str | Path) -> tuple[str, dict]:
    try:
        path = Path(session_path)
        state = extract_session_state(read_text(path))
        restored_count, cleared_count = replace_active_feedback(
            state["validated_outputs"]
        )
        log_session_event(
            "load_session",
            path,
            "success",
            {
                "restored_steps": restored_count,
                "cleared_steps": cleared_count,
            },
        )
        return (
            "Sesion cargada. "
            f"Se restauraron {restored_count} pasos y "
            f"se limpiaron {cleared_count} pasos pendientes.",
            state,
        )
    except Exception as exc:
        log_session_event("load_session", session_path, "error", error=exc)
        return (
            "No se pudo cargar la sesion. Verifica que el archivo sea una "
            "sesion valida generada por la aplicacion.",
            {},
        )


def list_session_files() -> list[str]:
    if not FEEDBACK_DIR.exists():
        return []
    return sorted(
        [path.name for path in FEEDBACK_DIR.glob("*_sesion_*.md")],
        reverse=True,
    )


def save_current_session(
    session_name: str,
    selected_model_id: str | None,
    vision_comments: str,
    target_items: list[str] | None,
    target_draft_item: str,
    business_items: list[str] | None,
    business_draft_item: str,
    need_items: list[str] | None,
    need_draft_item: str,
    pps_items: list[str] | None,
    pps_draft_item: str,
    competition_items: list[str] | None,
    competition_draft_item: str,
    channels_items: list[str] | None,
    channels_draft_item: str,
    investment_items: list[dict] | None,
    investment_team: str,
    investment_hours: object,
    investment_role: str,
    investment_start_date: str,
    investment_end_date: str,
    revenue_items: list[str] | None,
    revenue_draft_item: str,
    vision_output: str,
    target_output: str,
    business_output: str,
    need_output: str,
    pps_output: str,
    competition_output: str,
    channels_output: str,
    investment_output: str,
    revenue_output: str,
) -> tuple[str, str, gr.Dropdown]:
    raw_inputs = collect_session_raw_inputs(
        vision_comments,
        target_items,
        target_draft_item,
        business_items,
        business_draft_item,
        need_items,
        need_draft_item,
        pps_items,
        pps_draft_item,
        competition_items,
        competition_draft_item,
        channels_items,
        channels_draft_item,
        investment_items,
        investment_team,
        investment_hours,
        investment_role,
        investment_start_date,
        investment_end_date,
        revenue_items,
        revenue_draft_item,
    )
    validated_outputs = collect_session_validated_outputs(
        vision_output,
        target_output,
        business_output,
        need_output,
        pps_output,
        competition_output,
        channels_output,
        investment_output,
        revenue_output,
    )
    status, output_path = generate_session_markdown_document(
        session_name,
        raw_inputs,
        selected_model_id,
        validated_outputs=validated_outputs,
    )
    file_name = Path(output_path).name
    return status, output_path, gr.update(choices=list_session_files(), value=file_name)


def refresh_session_file_choices() -> gr.Dropdown:
    session_files = list_session_files()
    selected_file = session_files[0] if session_files else None
    return gr.update(choices=session_files, value=selected_file)


def session_raw_step(state: dict, step_id: str) -> dict:
    raw_inputs = state.get("raw_inputs", {})
    step_raw = raw_inputs.get(step_id, {})
    return step_raw if isinstance(step_raw, dict) else {}


def session_validated_output(state: dict, step_id: str) -> str:
    validated_outputs = state.get("validated_outputs", {})
    return str(validated_outputs.get(step_id, "") or "")


def build_loaded_session_outputs(status: str, state: dict) -> tuple:
    target_raw = session_raw_step(state, "target")
    target_items_value = list(target_raw.get("items") or [])
    business_raw = session_raw_step(state, "business_value")
    business_items_value = list(business_raw.get("items") or [])
    need_raw = session_raw_step(state, "need")
    need_items_value = list(need_raw.get("items") or [])
    pps_raw = session_raw_step(state, "pps")
    pps_items_value = list(pps_raw.get("items") or [])
    competition_raw = session_raw_step(state, "competition")
    competition_items_value = list(competition_raw.get("items") or [])
    channels_raw = session_raw_step(state, "channels")
    channels_items_value = list(channels_raw.get("items") or [])
    investment_raw = session_raw_step(state, "investment")
    investment_items_value = list(investment_raw.get("items") or [])
    investment_draft = investment_raw.get("draft_item") or {}
    if not isinstance(investment_draft, dict):
        investment_draft = {}
    revenue_raw = session_raw_step(state, "revenue_benefits")
    revenue_items_value = list(revenue_raw.get("items") or [])

    vision_output = session_validated_output(state, "vision")
    target_output_value = session_validated_output(state, "target")
    business_output_value = session_validated_output(state, "business_value")
    need_output_value = session_validated_output(state, "need")
    pps_output_value = session_validated_output(state, "pps")
    competition_output_value = session_validated_output(state, "competition")
    channels_output_value = session_validated_output(state, "channels")
    investment_output_value = session_validated_output(state, "investment")
    revenue_output_value = session_validated_output(state, "revenue_benefits")
    investment_hours_value = investment_draft.get("hours")

    return (
        status,
        state.get("session_name", DEFAULT_EXPORT_BASENAME),
        gr.update(
            value=state.get("selected_model_id", DEFAULT_LLM_MODEL_ID),
            interactive=False,
        ),
        session_raw_step(state, "vision").get("comments", ""),
        vision_output,
        gr.update(visible=bool(vision_output)),
        target_items_value,
        format_items(target_items_value),
        gr.update(choices=target_items_value, value=None),
        target_raw.get("draft_item", ""),
        target_output_value,
        gr.update(visible=bool(target_output_value)),
        business_items_value,
        format_items(business_items_value),
        gr.update(choices=business_items_value, value=None),
        business_raw.get("draft_item", ""),
        business_output_value,
        gr.update(visible=bool(business_output_value)),
        need_items_value,
        format_items(need_items_value),
        gr.update(choices=need_items_value, value=None),
        need_raw.get("draft_item", ""),
        need_output_value,
        gr.update(visible=bool(need_output_value)),
        pps_items_value,
        format_items(pps_items_value),
        gr.update(choices=pps_items_value, value=None),
        pps_raw.get("draft_item", ""),
        pps_output_value,
        gr.update(visible=bool(pps_output_value)),
        competition_items_value,
        format_items(competition_items_value),
        gr.update(choices=competition_items_value, value=None),
        competition_raw.get("draft_item", ""),
        competition_output_value,
        gr.update(visible=bool(competition_output_value)),
        channels_items_value,
        format_items(channels_items_value),
        gr.update(choices=channels_items_value, value=None),
        channels_raw.get("draft_item", ""),
        channels_output_value,
        gr.update(visible=bool(channels_output_value)),
        investment_items_value,
        format_investment_items(investment_items_value),
        gr.update(choices=investment_dropdown_choices(investment_items_value), value=None),
        investment_draft.get("team_name", ""),
        investment_hours_value,
        investment_draft.get("role", ""),
        calculate_investment_fte_display(investment_hours_value),
        format_investment_estimate(investment_items_value),
        investment_raw.get("start_date", ""),
        investment_raw.get("end_date", ""),
        investment_output_value,
        gr.update(visible=bool(investment_output_value)),
        revenue_items_value,
        format_items(revenue_items_value),
        gr.update(choices=revenue_items_value, value=None),
        revenue_raw.get("draft_item", ""),
        revenue_output_value,
        gr.update(visible=bool(revenue_output_value)),
    )


def load_session_into_ui(selected_session_file: str) -> tuple:
    if not selected_session_file:
        return (
            "Selecciona una sesion para cargar.",
            *[gr.update() for _ in range(59)],
        )
    session_path = FEEDBACK_DIR / Path(selected_session_file).name
    status, state = restore_session_from_path(session_path)
    if not state:
        return (status, *[gr.update() for _ in range(59)])
    return build_loaded_session_outputs(status, state)


def build_business_value(items: list[str] | None, selected_model_id: str | None = None) -> str:
    current_items = [item.strip() for item in list(items or []) if item.strip()]
    if not current_items:
        return "Agrega al menos un item de valor de negocio para poder procesar este paso."
    if has_duplicates(current_items):
        return "La lista de items de valor de negocio no puede contener repetidos."

    item_text = "\n".join(f"- {item}" for item in current_items)
    user_input = f"Items de valor de negocio propuestos por el usuario:\n{item_text}"
    return call_openai_step(
        BUSINESS_VALUE_SPEC,
        user_input,
        extra_context=load_previous_feedback(),
        selected_model_id=selected_model_id,
    )


def build_need(items: list[str] | None, selected_model_id: str | None = None) -> str:
    current_items = [item.strip() for item in list(items or []) if item.strip()]
    if not current_items:
        return "Agrega al menos un item de necesidad para poder procesar este paso."
    if has_duplicates(current_items):
        return "La lista de items de necesidad no puede contener repetidos."

    item_text = "\n".join(f"- {item}" for item in current_items)
    user_input = f"Items de necesidad propuestos por el usuario:\n{item_text}"
    return call_openai_step(
        NEED_SPEC,
        user_input,
        extra_context=load_compact_feedback_context(
            [
                "vision_response.md",
                "target_response.md",
                "business_value_response.md",
            ]
        ),
        selected_model_id=selected_model_id,
    )


def build_pps(items: list[str] | None, selected_model_id: str | None = None) -> str:
    current_items = [item.strip() for item in list(items or []) if item.strip()]
    if not current_items:
        return "Agrega al menos un item de Producto / Proceso / Servicio para poder procesar este paso."
    if has_duplicates(current_items):
        return "La lista de items de Producto / Proceso / Servicio no puede contener repetidos."

    item_text = "\n".join(f"- {item}" for item in current_items)
    user_input = f"Items de Producto / Proceso / Servicio propuestos por el usuario:\n{item_text}"
    return call_openai_step(
        PPS_SPEC,
        user_input,
        extra_context=load_compact_feedback_context(
            [
                "vision_response.md",
                "target_response.md",
                "business_value_response.md",
                "need_response.md",
            ]
        ),
        selected_model_id=selected_model_id,
    )


def build_competition(items: list[str] | None, selected_model_id: str | None = None) -> str:
    current_items = [item.strip() for item in list(items or []) if item.strip()]
    if not current_items:
        return "Agrega al menos un item de soluciones similares o utiliza No aplica."
    if has_duplicates(current_items):
        return "La lista de soluciones similares no puede contener repetidos."

    item_text = "\n".join(f"- {item}" for item in current_items)
    user_input = f"Items de soluciones similares propuestos por el usuario:\n{item_text}"
    return call_openai_step(
        COMPETITION_SPEC,
        user_input,
        extra_context=load_compact_feedback_context(
            [
                "vision_response.md",
                "target_response.md",
                "business_value_response.md",
                "need_response.md",
                "pps_response.md",
            ]
        ),
        selected_model_id=selected_model_id,
    )


def build_channels(items: list[str] | None, selected_model_id: str | None = None) -> str:
    current_items = [item.strip() for item in list(items or []) if item.strip()]
    if not current_items:
        return "Agrega al menos un item de canales y medios para poder procesar este paso."
    if has_duplicates(current_items):
        return "La lista de canales y medios no puede contener repetidos."

    item_text = "\n".join(f"- {item}" for item in current_items)
    user_input = f"Items de canales y medios propuestos por el usuario:\n{item_text}"
    return call_openai_step(
        CHANNELS_SPEC,
        user_input,
        extra_context=load_compact_feedback_context(
            [
                "vision_response.md",
                "target_response.md",
                "business_value_response.md",
                "need_response.md",
                "pps_response.md",
                "competition_response.md",
            ]
        ),
        selected_model_id=selected_model_id,
    )


def parse_investment_hours(value: object) -> int | None:
    if value is None:
        return None
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric_value.is_integer():
        return None
    hours = int(numeric_value)
    return hours if hours > 0 else None


def calculate_investment_fte(hours: int) -> float:
    return round(hours / 160, 2)


def format_investment_fte(value: float) -> str:
    return f"{value:.2f}"


def calculate_investment_fte_display(hours: object) -> str:
    parsed_hours = parse_investment_hours(hours)
    if parsed_hours is None:
        return ""
    return format_investment_fte(calculate_investment_fte(parsed_hours))


def make_investment_item(team_name: str, hours: object, role: str) -> dict:
    parsed_hours = parse_investment_hours(hours)
    if parsed_hours is None:
        raise ValueError("Cantidad de horas debe ser un numero entero mayor a cero.")
    clean_team_name = team_name.strip()
    clean_role = role.strip()
    if not clean_team_name:
        raise ValueError("Nombre de Equipo no puede estar vacio.")
    if not clean_role:
        raise ValueError("Rol a desempenar no puede estar vacio.")
    return {
        "team_name": clean_team_name,
        "hours": parsed_hours,
        "role": clean_role,
        "fte": calculate_investment_fte(parsed_hours),
    }


def normalize_investment_team(item: dict) -> str:
    return normalize_for_duplicate(str(item.get("team_name", "")))


def has_duplicate_investment_teams(items: list[dict]) -> bool:
    normalized_names = [
        normalize_investment_team(item)
        for item in items
        if normalize_investment_team(item)
    ]
    return len(normalized_names) != len(set(normalized_names))


def calculate_investment_totals(items: list[dict] | None) -> dict:
    total_hours = sum(int(item.get("hours", 0) or 0) for item in list(items or []))
    return {
        "total_hours": total_hours,
        "total_ftes": calculate_investment_fte(total_hours),
    }


def format_investment_estimate(items: list[dict] | None) -> str:
    totals = calculate_investment_totals(items)
    return (
        "Estimacion\n"
        f"Total Horas: {totals['total_hours']}\n"
        f"Total FTEs: {format_investment_fte(totals['total_ftes'])}"
    )


def investment_dropdown_choices(items: list[dict] | None) -> list[str]:
    return [item["team_name"] for item in list(items or [])]


def format_investment_items(items: list[dict] | None) -> str:
    if not items:
        return ""
    lines = []
    for index, item in enumerate(items, start=1):
        lines.append(
            f"{index}. {item['team_name']} | Horas: {item['hours']} | "
            f"FTE: {format_investment_fte(item['fte'])} | Rol: {item['role']}"
        )
    return "\n".join(lines)


def find_investment_item(selected_team: str, items: list[dict] | None) -> dict | None:
    normalized_selected = normalize_for_duplicate(selected_team or "")
    for item in list(items or []):
        if normalize_investment_team(item) == normalized_selected:
            return item
    return None


def add_investment_item(
    team_name: str,
    hours: object,
    role: str,
    items: list[dict] | None,
) -> tuple[list[dict], str, gr.Dropdown, str, object, str, str, str]:
    current_items = list(items or [])
    try:
        new_item = make_investment_item(team_name, hours, role)
    except ValueError:
        return (
            current_items,
            format_investment_items(current_items),
            gr.update(choices=investment_dropdown_choices(current_items), value=None),
            team_name,
            hours,
            role,
            calculate_investment_fte_display(hours),
            format_investment_estimate(current_items),
        )

    if find_investment_item(new_item["team_name"], current_items):
        return (
            current_items,
            format_investment_items(current_items),
            gr.update(choices=investment_dropdown_choices(current_items), value=None),
            team_name,
            hours,
            role,
            calculate_investment_fte_display(hours),
            format_investment_estimate(current_items),
        )

    updated_items = current_items + [new_item]
    return (
        updated_items,
        format_investment_items(updated_items),
        gr.update(choices=investment_dropdown_choices(updated_items), value=None),
        "",
        None,
        "",
        "",
        format_investment_estimate(updated_items),
    )


def load_selected_investment_item(
    selected_team: str,
    items: list[dict] | None,
) -> tuple[str, int | None, str, str]:
    item = find_investment_item(selected_team, items)
    if not item:
        return "", None, "", ""
    return (
        item["team_name"],
        item["hours"],
        item["role"],
        format_investment_fte(item["fte"]),
    )


def update_investment_item(
    selected_team: str,
    team_name: str,
    hours: object,
    role: str,
    items: list[dict] | None,
) -> tuple[list[dict], str, gr.Dropdown, str, object, str, str, str]:
    current_items = list(items or [])
    if not selected_team or not find_investment_item(selected_team, current_items):
        return (
            current_items,
            format_investment_items(current_items),
            gr.update(choices=investment_dropdown_choices(current_items), value=None),
            team_name,
            hours,
            role,
            calculate_investment_fte_display(hours),
            format_investment_estimate(current_items),
        )

    try:
        updated_item = make_investment_item(team_name, hours, role)
    except ValueError:
        return (
            current_items,
            format_investment_items(current_items),
            gr.update(choices=investment_dropdown_choices(current_items), value=selected_team),
            team_name,
            hours,
            role,
            calculate_investment_fte_display(hours),
            format_investment_estimate(current_items),
        )

    normalized_selected = normalize_for_duplicate(selected_team)
    updated_items = []
    for item in current_items:
        if normalize_investment_team(item) == normalized_selected:
            updated_items.append(updated_item)
        else:
            updated_items.append(item)

    if has_duplicate_investment_teams(updated_items):
        return (
            current_items,
            format_investment_items(current_items),
            gr.update(choices=investment_dropdown_choices(current_items), value=selected_team),
            team_name,
            hours,
            role,
            calculate_investment_fte_display(hours),
            format_investment_estimate(current_items),
        )

    return (
        updated_items,
        format_investment_items(updated_items),
        gr.update(
            choices=investment_dropdown_choices(updated_items),
            value=updated_item["team_name"],
        ),
        updated_item["team_name"],
        updated_item["hours"],
        updated_item["role"],
        format_investment_fte(updated_item["fte"]),
        format_investment_estimate(updated_items),
    )


def delete_investment_item(
    selected_team: str,
    items: list[dict] | None,
) -> tuple[list[dict], str, gr.Dropdown, str, None, str, str, str]:
    normalized_selected = normalize_for_duplicate(selected_team or "")
    updated_items = [
        item
        for item in list(items or [])
        if normalize_investment_team(item) != normalized_selected
    ]
    return (
        updated_items,
        format_investment_items(updated_items),
        gr.update(choices=investment_dropdown_choices(updated_items), value=None),
        "",
        None,
        "",
        "",
        format_investment_estimate(updated_items),
    )


def parse_investment_date(value: str):
    date_text = (value or "").strip()
    if not date_text:
        return None
    try:
        parsed_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None
    if parsed_date.strftime("%Y-%m-%d") != date_text:
        return None
    return parsed_date


def validate_investment_dates(start_date: str, end_date: str) -> str | None:
    parsed_start_date = parse_investment_date(start_date)
    parsed_end_date = parse_investment_date(end_date)
    if parsed_start_date is None:
        return "Fecha Tentativa inicio debe usar formato AAAA-MM-DD."
    if parsed_end_date is None:
        return "Fecha Tentativa fin debe usar formato AAAA-MM-DD."
    if parsed_end_date < parsed_start_date:
        return "Fecha Tentativa fin no puede ser anterior a Fecha Tentativa inicio."
    return None


def build_investment(
    items: list[dict] | None,
    start_date: str,
    end_date: str,
    selected_model_id: str | None = None,
) -> str:
    current_items = list(items or [])
    if not current_items:
        return "Agrega al menos un equipo participante para poder procesar la Inversion."
    if has_duplicate_investment_teams(current_items):
        return "La lista de inversion no puede contener equipos repetidos."

    date_error = validate_investment_dates(start_date, end_date)
    if date_error:
        return date_error

    totals = calculate_investment_totals(current_items)
    item_text = "\n".join(
        "\n".join(
            [
                f"- Equipo: {item['team_name']}",
                f"  Horas: {item['hours']}",
                f"  FTE: {format_investment_fte(item['fte'])}",
                f"  Rol: {item['role']}",
            ]
        )
        for item in current_items
    )
    user_input = "\n".join(
        [
            "Equipos participantes:",
            item_text,
            "",
            "Estimacion:",
            f"Total Horas: {totals['total_hours']}",
            f"Total FTEs: {format_investment_fte(totals['total_ftes'])}",
            f"Fecha Tentativa inicio: {start_date.strip()}",
            f"Fecha Tentativa fin: {end_date.strip()}",
        ]
    )
    return call_openai_step(
        INVESTMENT_SPEC,
        user_input,
        extra_context=load_compact_feedback_context(
            [
                "vision_response.md",
                "target_response.md",
                "business_value_response.md",
                "need_response.md",
                "pps_response.md",
                "competition_response.md",
                "channels_response.md",
            ]
        ),
        selected_model_id=selected_model_id,
    )


def build_revenue_benefits(items: list[str] | None, selected_model_id: str | None = None) -> str:
    current_items = [item.strip() for item in list(items or []) if item.strip()]
    if not current_items:
        return "Agrega al menos un item de ingreso o beneficio para poder procesar este paso."
    if has_duplicates(current_items):
        return "La lista de ingresos y/o beneficios no puede contener repetidos."

    item_text = "\n".join(f"- {item}" for item in current_items)
    user_input = f"Items de ingresos y/o beneficios propuestos por el usuario:\n{item_text}"
    return call_openai_step(
        REVENUE_BENEFITS_SPEC,
        user_input,
        extra_context=load_compact_feedback_context(
            [
                "vision_response.md",
                "target_response.md",
                "business_value_response.md",
                "need_response.md",
                "pps_response.md",
                "competition_response.md",
                "channels_response.md",
                "investment_response.md",
            ]
        ),
        selected_model_id=selected_model_id,
    )


def process_business_value(items: list[str] | None, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_business_value(items, selected_model_id)
    can_continue = bool(items) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


def process_need(items: list[str] | None, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_need(items, selected_model_id)
    can_continue = bool(items) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


def process_pps(items: list[str] | None, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_pps(items, selected_model_id)
    can_continue = bool(items) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


def process_competition(items: list[str] | None, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_competition(items, selected_model_id)
    can_continue = bool(items) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


def process_channels(items: list[str] | None, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_channels(items, selected_model_id)
    can_continue = bool(items) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


def process_investment(
    items: list[dict] | None,
    start_date: str,
    end_date: str,
    selected_model_id: str | None = None,
) -> tuple[str, gr.Button]:
    result = build_investment(items, start_date, end_date, selected_model_id)
    blocking_prefixes = (
        "Falta configurar",
        "Agrega",
        "La lista",
        "Fecha Tentativa",
    )
    can_continue = bool(items) and not result.startswith(blocking_prefixes)
    return result, gr.update(visible=can_continue)


def process_revenue_benefits(items: list[str] | None, selected_model_id: str | None = None) -> tuple[str, gr.Button]:
    result = build_revenue_benefits(items, selected_model_id)
    can_continue = bool(items) and not result.startswith("Falta configurar")
    return result, gr.update(visible=can_continue)


with gr.Blocks(title="Product Vision Board") as demo:
    with gr.Accordion("Sesion de trabajo", open=True):
        with gr.Group():
            session_name = gr.Textbox(
                label="Nombre de sesion / caso",
                value=DEFAULT_EXPORT_BASENAME,
            )
            llm_model = gr.Dropdown(
                label="Modelo a utilizar",
                choices=LLM_MODEL_DROPDOWN_CHOICES,
                value=DEFAULT_LLM_MODEL_ID,
                interactive=True,
            )
            with gr.Row():
                save_session_button = gr.Button("Guardar sesion actual", variant="primary")
                session_file = gr.Dropdown(
                    label="Sesion guardada",
                    choices=list_session_files(),
                    interactive=True,
                )
                refresh_sessions_button = gr.Button("Actualizar sesiones")
                load_session_button = gr.Button("Cargar sesion")
            session_status = gr.Textbox(
                label="Estado de sesion",
                interactive=False,
            )
            with gr.Accordion("Detalle de sesion", open=False):
                session_path_output = gr.Textbox(
                    label="Ruta de sesion",
                    interactive=False,
                )

    with gr.Tabs(selected="vision") as pvb_tabs:
        with gr.Tab("1. Vision", id="vision"):
            form_spec = VISION_SPEC["form"]

            gr.Markdown(f"# {VISION_SPEC['title']}")
            gr.Markdown(VISION_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(VISION_SPEC)

            with gr.Group():
                comments = gr.Textbox(
                    label=form_spec["comment_label"],
                    placeholder=form_spec["comment_placeholder"],
                    lines=form_spec["comment_lines"],
                )
                process = gr.Button(form_spec["submit_label"], variant="primary")
            with gr.Group():
                output = gr.Textbox(
                    label=form_spec["output_label"],
                    lines=form_spec["output_lines"],
                    interactive=False,
                )
                next_step = gr.Button(
                    form_spec["next_step_label"],
                    variant="secondary",
                    visible=False,
                )

            process.click(
                fn=process_vision_and_lock_model,
                inputs=[comments, llm_model],
                outputs=[output, next_step, llm_model],
            )
            next_step.click(fn=lambda: gr.update(selected="target"), outputs=pvb_tabs)

        with gr.Tab("2. Target", id="target"):
            target_form_spec = TARGET_SPEC["form"]
            target_items = gr.State([])

            gr.Markdown(f"# {TARGET_SPEC['title']}")
            gr.Markdown(TARGET_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(TARGET_SPEC)

            with gr.Group():
                target_item = gr.Textbox(
                    label=target_form_spec["entry_label"],
                    placeholder=target_form_spec["entry_placeholder"],
                    lines=target_form_spec["entry_lines"],
                )
                with gr.Row():
                    add_target_item_button = gr.Button(target_form_spec["add_button_label"])
                    load_target_item_button = gr.Button(target_form_spec["load_button_label"])
                    update_target_item_button = gr.Button(target_form_spec["update_button_label"])
                    delete_target_item_button = gr.Button(target_form_spec["delete_button_label"])
                target_items_display = gr.Textbox(
                    label=target_form_spec["list_label"],
                    lines=8,
                    interactive=False,
                )
                target_item_to_delete = gr.Dropdown(
                    label=target_form_spec["selected_item_label"],
                    choices=[],
                    interactive=True,
                )
            with gr.Group():
                process_target_button = gr.Button(
                    target_form_spec["submit_label"],
                    variant="primary",
                )
                target_output = gr.Textbox(
                    label=target_form_spec["output_label"],
                    lines=target_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_target_step = gr.Button(target_form_spec["previous_step_label"])
                    next_target_step = gr.Button(
                        target_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            previous_target_step.click(
                fn=lambda: gr.update(selected="vision"),
                outputs=pvb_tabs,
            )
            add_target_item_button.click(
                fn=add_list_item,
                inputs=[target_item, target_items],
                outputs=[
                    target_items,
                    target_items_display,
                    target_item_to_delete,
                    target_item,
                ],
            )
            load_target_item_button.click(
                fn=load_selected_item,
                inputs=target_item_to_delete,
                outputs=target_item,
            )
            update_target_item_button.click(
                fn=update_list_item,
                inputs=[target_item_to_delete, target_item, target_items],
                outputs=[
                    target_items,
                    target_items_display,
                    target_item_to_delete,
                    target_item,
                ],
            )
            delete_target_item_button.click(
                fn=delete_list_item,
                inputs=[target_item_to_delete, target_items],
                outputs=[
                    target_items,
                    target_items_display,
                    target_item_to_delete,
                    target_item,
                ],
            )
            process_target_button.click(
                fn=process_target,
                inputs=[target_items, llm_model],
                outputs=[target_output, next_target_step],
            )
            next_target_step.click(
                fn=lambda: gr.update(selected="business_value"),
                outputs=pvb_tabs,
            )

        with gr.Tab("3. Valor de negocio", id="business_value"):
            business_form_spec = BUSINESS_VALUE_SPEC["form"]
            business_items = gr.State([])

            gr.Markdown(f"# {BUSINESS_VALUE_SPEC['title']}")
            gr.Markdown(BUSINESS_VALUE_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(BUSINESS_VALUE_SPEC)

            with gr.Group():
                business_item = gr.Textbox(
                    label=business_form_spec["entry_label"],
                    placeholder=business_form_spec["entry_placeholder"],
                    lines=business_form_spec["entry_lines"],
                )
                with gr.Row():
                    add_business_item = gr.Button(business_form_spec["add_button_label"])
                    load_business_item = gr.Button(business_form_spec["load_button_label"])
                    update_business_item = gr.Button(business_form_spec["update_button_label"])
                    delete_business_item = gr.Button(business_form_spec["delete_button_label"])
                business_items_display = gr.Textbox(
                    label=business_form_spec["list_label"],
                    lines=8,
                    interactive=False,
                )
                business_item_to_delete = gr.Dropdown(
                    label=business_form_spec["selected_item_label"],
                    choices=[],
                    interactive=True,
                )
            with gr.Group():
                process_business_items = gr.Button(
                    business_form_spec["submit_label"],
                    variant="primary",
                )
                business_output = gr.Textbox(
                    label=business_form_spec["output_label"],
                    lines=business_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_business_step = gr.Button(business_form_spec["previous_step_label"])
                    next_business_step = gr.Button(
                        business_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            previous_business_step.click(
                fn=lambda: gr.update(selected="target"),
                outputs=pvb_tabs,
            )
            add_business_item.click(
                fn=add_list_item,
                inputs=[business_item, business_items],
                outputs=[
                    business_items,
                    business_items_display,
                    business_item_to_delete,
                    business_item,
                ],
            )
            load_business_item.click(
                fn=load_selected_item,
                inputs=business_item_to_delete,
                outputs=business_item,
            )
            update_business_item.click(
                fn=update_list_item,
                inputs=[business_item_to_delete, business_item, business_items],
                outputs=[
                    business_items,
                    business_items_display,
                    business_item_to_delete,
                    business_item,
                ],
            )
            delete_business_item.click(
                fn=delete_list_item,
                inputs=[business_item_to_delete, business_items],
                outputs=[
                    business_items,
                    business_items_display,
                    business_item_to_delete,
                    business_item,
                ],
            )
            process_business_items.click(
                fn=process_business_value,
                inputs=[business_items, llm_model],
                outputs=[business_output, next_business_step],
            )
            next_business_step.click(
                fn=lambda: gr.update(selected="need"),
                outputs=pvb_tabs,
            )

        with gr.Tab("4. Necesidad", id="need"):
            need_form_spec = NEED_SPEC["form"]
            need_items = gr.State([])

            gr.Markdown(f"# {NEED_SPEC['title']}")
            gr.Markdown(NEED_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(NEED_SPEC)

            with gr.Group():
                need_item = gr.Textbox(
                    label=need_form_spec["entry_label"],
                    placeholder=need_form_spec["entry_placeholder"],
                    lines=need_form_spec["entry_lines"],
                )
                with gr.Row():
                    add_need_item_button = gr.Button(need_form_spec["add_button_label"])
                    load_need_item_button = gr.Button(need_form_spec["load_button_label"])
                    update_need_item_button = gr.Button(need_form_spec["update_button_label"])
                    delete_need_item_button = gr.Button(need_form_spec["delete_button_label"])
                need_items_display = gr.Textbox(
                    label=need_form_spec["list_label"],
                    lines=8,
                    interactive=False,
                )
                need_item_to_edit = gr.Dropdown(
                    label=need_form_spec["selected_item_label"],
                    choices=[],
                    interactive=True,
                )
            with gr.Group():
                process_need_items = gr.Button(
                    need_form_spec["submit_label"],
                    variant="primary",
                )
                need_output = gr.Textbox(
                    label=need_form_spec["output_label"],
                    lines=need_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_need_step = gr.Button(need_form_spec["previous_step_label"])
                    next_need_step = gr.Button(
                        need_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            previous_need_step.click(
                fn=lambda: gr.update(selected="business_value"),
                outputs=pvb_tabs,
            )
            add_need_item_button.click(
                fn=add_list_item,
                inputs=[need_item, need_items],
                outputs=[
                    need_items,
                    need_items_display,
                    need_item_to_edit,
                    need_item,
                ],
            )
            load_need_item_button.click(
                fn=load_selected_item,
                inputs=need_item_to_edit,
                outputs=need_item,
            )
            update_need_item_button.click(
                fn=update_list_item,
                inputs=[need_item_to_edit, need_item, need_items],
                outputs=[
                    need_items,
                    need_items_display,
                    need_item_to_edit,
                    need_item,
                ],
            )
            delete_need_item_button.click(
                fn=delete_list_item,
                inputs=[need_item_to_edit, need_items],
                outputs=[
                    need_items,
                    need_items_display,
                    need_item_to_edit,
                    need_item,
                ],
            )
            process_need_items.click(
                fn=process_need,
                inputs=[need_items, llm_model],
                outputs=[need_output, next_need_step],
            )
            next_need_step.click(
                fn=lambda: gr.update(selected="pps"),
                outputs=pvb_tabs,
            )

        with gr.Tab("5. Producto / Proceso / Servicio", id="pps"):
            pps_form_spec = PPS_SPEC["form"]
            pps_items = gr.State([])

            gr.Markdown(f"# {PPS_SPEC['title']}")
            gr.Markdown(PPS_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(PPS_SPEC)

            with gr.Group():
                pps_item = gr.Textbox(
                    label=pps_form_spec["entry_label"],
                    placeholder=pps_form_spec["entry_placeholder"],
                    lines=pps_form_spec["entry_lines"],
                )
                with gr.Row():
                    add_pps_item_button = gr.Button(pps_form_spec["add_button_label"])
                    load_pps_item_button = gr.Button(pps_form_spec["load_button_label"])
                    update_pps_item_button = gr.Button(pps_form_spec["update_button_label"])
                    delete_pps_item_button = gr.Button(pps_form_spec["delete_button_label"])
                pps_items_display = gr.Textbox(
                    label=pps_form_spec["list_label"],
                    lines=8,
                    interactive=False,
                )
                pps_item_to_edit = gr.Dropdown(
                    label=pps_form_spec["selected_item_label"],
                    choices=[],
                    interactive=True,
                )
            with gr.Group():
                process_pps_items = gr.Button(
                    pps_form_spec["submit_label"],
                    variant="primary",
                )
                pps_output = gr.Textbox(
                    label=pps_form_spec["output_label"],
                    lines=pps_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_pps_step = gr.Button(pps_form_spec["previous_step_label"])
                    next_pps_step = gr.Button(
                        pps_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            previous_pps_step.click(
                fn=lambda: gr.update(selected="need"),
                outputs=pvb_tabs,
            )
            add_pps_item_button.click(
                fn=add_list_item,
                inputs=[pps_item, pps_items],
                outputs=[
                    pps_items,
                    pps_items_display,
                    pps_item_to_edit,
                    pps_item,
                ],
            )
            load_pps_item_button.click(
                fn=load_selected_item,
                inputs=pps_item_to_edit,
                outputs=pps_item,
            )
            update_pps_item_button.click(
                fn=update_list_item,
                inputs=[pps_item_to_edit, pps_item, pps_items],
                outputs=[
                    pps_items,
                    pps_items_display,
                    pps_item_to_edit,
                    pps_item,
                ],
            )
            delete_pps_item_button.click(
                fn=delete_list_item,
                inputs=[pps_item_to_edit, pps_items],
                outputs=[
                    pps_items,
                    pps_items_display,
                    pps_item_to_edit,
                    pps_item,
                ],
            )
            process_pps_items.click(
                fn=process_pps,
                inputs=[pps_items, llm_model],
                outputs=[pps_output, next_pps_step],
            )
            next_pps_step.click(
                fn=lambda: gr.update(selected="competition"),
                outputs=pvb_tabs,
            )

        with gr.Tab("5.1. Soluciones Similares", id="competition"):
            competition_form_spec = COMPETITION_SPEC["form"]
            competition_default_items = competition_form_spec["default_items"]
            competition_items = gr.State(competition_default_items)

            gr.Markdown(f"# {COMPETITION_SPEC['title']}")
            gr.Markdown(COMPETITION_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(COMPETITION_SPEC)

            with gr.Group():
                competition_item = gr.Textbox(
                    label=competition_form_spec["entry_label"],
                    placeholder=competition_form_spec["entry_placeholder"],
                    lines=competition_form_spec["entry_lines"],
                )
                with gr.Row():
                    add_competition_item_button = gr.Button(competition_form_spec["add_button_label"])
                    load_competition_item_button = gr.Button(competition_form_spec["load_button_label"])
                    update_competition_item_button = gr.Button(competition_form_spec["update_button_label"])
                    delete_competition_item_button = gr.Button(competition_form_spec["delete_button_label"])
                competition_items_display = gr.Textbox(
                    label=competition_form_spec["list_label"],
                    value=format_items(competition_default_items),
                    lines=8,
                    interactive=False,
                )
                competition_item_to_edit = gr.Dropdown(
                    label=competition_form_spec["selected_item_label"],
                    choices=competition_default_items,
                    interactive=True,
                )
            with gr.Group():
                process_competition_items = gr.Button(
                    competition_form_spec["submit_label"],
                    variant="primary",
                )
                competition_output = gr.Textbox(
                    label=competition_form_spec["output_label"],
                    lines=competition_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_competition_step = gr.Button(competition_form_spec["previous_step_label"])
                    next_competition_step = gr.Button(
                        competition_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            previous_competition_step.click(
                fn=lambda: gr.update(selected="pps"),
                outputs=pvb_tabs,
            )
            add_competition_item_button.click(
                fn=add_list_item,
                inputs=[competition_item, competition_items],
                outputs=[
                    competition_items,
                    competition_items_display,
                    competition_item_to_edit,
                    competition_item,
                ],
            )
            load_competition_item_button.click(
                fn=load_selected_item,
                inputs=competition_item_to_edit,
                outputs=competition_item,
            )
            update_competition_item_button.click(
                fn=update_list_item,
                inputs=[competition_item_to_edit, competition_item, competition_items],
                outputs=[
                    competition_items,
                    competition_items_display,
                    competition_item_to_edit,
                    competition_item,
                ],
            )
            delete_competition_item_button.click(
                fn=delete_list_item,
                inputs=[competition_item_to_edit, competition_items],
                outputs=[
                    competition_items,
                    competition_items_display,
                    competition_item_to_edit,
                    competition_item,
                ],
            )
            process_competition_items.click(
                fn=process_competition,
                inputs=[competition_items, llm_model],
                outputs=[competition_output, next_competition_step],
            )
            next_competition_step.click(
                fn=lambda: gr.update(selected="channels"),
                outputs=pvb_tabs,
            )

        with gr.Tab("5.2. Canales y Medios", id="channels"):
            channels_form_spec = CHANNELS_SPEC["form"]
            channels_items = gr.State([])

            gr.Markdown(f"# {CHANNELS_SPEC['title']}")
            gr.Markdown(CHANNELS_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(CHANNELS_SPEC)

            with gr.Group():
                channels_item = gr.Textbox(
                    label=channels_form_spec["entry_label"],
                    placeholder=channels_form_spec["entry_placeholder"],
                    lines=channels_form_spec["entry_lines"],
                )
                with gr.Row():
                    add_channels_item_button = gr.Button(channels_form_spec["add_button_label"])
                    load_channels_item_button = gr.Button(channels_form_spec["load_button_label"])
                    update_channels_item_button = gr.Button(channels_form_spec["update_button_label"])
                    delete_channels_item_button = gr.Button(channels_form_spec["delete_button_label"])
                channels_items_display = gr.Textbox(
                    label=channels_form_spec["list_label"],
                    lines=8,
                    interactive=False,
                )
                channels_item_to_edit = gr.Dropdown(
                    label=channels_form_spec["selected_item_label"],
                    choices=[],
                    interactive=True,
                )
            with gr.Group():
                process_channels_items = gr.Button(
                    channels_form_spec["submit_label"],
                    variant="primary",
                )
                channels_output = gr.Textbox(
                    label=channels_form_spec["output_label"],
                    lines=channels_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_channels_step = gr.Button(channels_form_spec["previous_step_label"])
                    next_channels_step = gr.Button(
                        channels_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            previous_channels_step.click(
                fn=lambda: gr.update(selected="competition"),
                outputs=pvb_tabs,
            )
            add_channels_item_button.click(
                fn=add_list_item,
                inputs=[channels_item, channels_items],
                outputs=[
                    channels_items,
                    channels_items_display,
                    channels_item_to_edit,
                    channels_item,
                ],
            )
            load_channels_item_button.click(
                fn=load_selected_item,
                inputs=channels_item_to_edit,
                outputs=channels_item,
            )
            update_channels_item_button.click(
                fn=update_list_item,
                inputs=[channels_item_to_edit, channels_item, channels_items],
                outputs=[
                    channels_items,
                    channels_items_display,
                    channels_item_to_edit,
                    channels_item,
                ],
            )
            delete_channels_item_button.click(
                fn=delete_list_item,
                inputs=[channels_item_to_edit, channels_items],
                outputs=[
                    channels_items,
                    channels_items_display,
                    channels_item_to_edit,
                    channels_item,
                ],
            )
            process_channels_items.click(
                fn=process_channels,
                inputs=[channels_items, llm_model],
                outputs=[channels_output, next_channels_step],
            )
            next_channels_step.click(
                fn=lambda: gr.update(selected="investment"),
                outputs=pvb_tabs,
            )

        with gr.Tab("6. Inversion", id="investment"):
            investment_form_spec = INVESTMENT_SPEC["form"]
            investment_items = gr.State([])

            gr.Markdown(f"# {INVESTMENT_SPEC['title']}")
            gr.Markdown(INVESTMENT_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(INVESTMENT_SPEC)

            with gr.Group():
                with gr.Row():
                    investment_team = gr.Textbox(
                        label=investment_form_spec["team_label"],
                        placeholder=investment_form_spec["team_placeholder"],
                    )
                    investment_hours = gr.Number(
                        label=investment_form_spec["hours_label"],
                        precision=0,
                    )
                    investment_fte = gr.Textbox(
                        label=investment_form_spec["fte_label"],
                        interactive=False,
                    )
                investment_role = gr.Textbox(
                    label=investment_form_spec["role_label"],
                    placeholder=investment_form_spec["role_placeholder"],
                    lines=2,
                )
                with gr.Row():
                    add_investment_item_button = gr.Button(investment_form_spec["add_button_label"])
                    load_investment_item_button = gr.Button(investment_form_spec["load_button_label"])
                    update_investment_item_button = gr.Button(investment_form_spec["update_button_label"])
                    delete_investment_item_button = gr.Button(investment_form_spec["delete_button_label"])
                investment_items_display = gr.Textbox(
                    label=investment_form_spec["list_label"],
                    lines=8,
                    interactive=False,
                )
                investment_item_to_edit = gr.Dropdown(
                    label=investment_form_spec["selected_item_label"],
                    choices=[],
                    interactive=True,
                )
                investment_estimate = gr.Textbox(
                    label=investment_form_spec["estimate_label"],
                    value=format_investment_estimate([]),
                    lines=3,
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    investment_start_date = gr.Textbox(
                        label=investment_form_spec["start_date_label"],
                        placeholder=investment_form_spec["date_format"],
                    )
                    investment_end_date = gr.Textbox(
                        label=investment_form_spec["end_date_label"],
                        placeholder=investment_form_spec["date_format"],
                    )
                process_investment_items = gr.Button(
                    investment_form_spec["submit_label"],
                    variant="primary",
                )
                investment_output = gr.Textbox(
                    label=investment_form_spec["output_label"],
                    lines=investment_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_investment_step = gr.Button(investment_form_spec["previous_step_label"])
                    next_investment_step = gr.Button(
                        investment_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            investment_hours.change(
                fn=calculate_investment_fte_display,
                inputs=investment_hours,
                outputs=investment_fte,
            )
            previous_investment_step.click(
                fn=lambda: gr.update(selected="channels"),
                outputs=pvb_tabs,
            )
            add_investment_item_button.click(
                fn=add_investment_item,
                inputs=[
                    investment_team,
                    investment_hours,
                    investment_role,
                    investment_items,
                ],
                outputs=[
                    investment_items,
                    investment_items_display,
                    investment_item_to_edit,
                    investment_team,
                    investment_hours,
                    investment_role,
                    investment_fte,
                    investment_estimate,
                ],
            )
            load_investment_item_button.click(
                fn=load_selected_investment_item,
                inputs=[investment_item_to_edit, investment_items],
                outputs=[
                    investment_team,
                    investment_hours,
                    investment_role,
                    investment_fte,
                ],
            )
            update_investment_item_button.click(
                fn=update_investment_item,
                inputs=[
                    investment_item_to_edit,
                    investment_team,
                    investment_hours,
                    investment_role,
                    investment_items,
                ],
                outputs=[
                    investment_items,
                    investment_items_display,
                    investment_item_to_edit,
                    investment_team,
                    investment_hours,
                    investment_role,
                    investment_fte,
                    investment_estimate,
                ],
            )
            delete_investment_item_button.click(
                fn=delete_investment_item,
                inputs=[investment_item_to_edit, investment_items],
                outputs=[
                    investment_items,
                    investment_items_display,
                    investment_item_to_edit,
                    investment_team,
                    investment_hours,
                    investment_role,
                    investment_fte,
                    investment_estimate,
                ],
            )
            process_investment_items.click(
                fn=process_investment,
                inputs=[
                    investment_items,
                    investment_start_date,
                    investment_end_date,
                    llm_model,
                ],
                outputs=[investment_output, next_investment_step],
            )
            next_investment_step.click(
                fn=lambda: gr.update(selected="revenue_benefits"),
                outputs=pvb_tabs,
            )

        with gr.Tab("7. Flujos de Ingresos y/o Beneficios", id="revenue_benefits"):
            revenue_form_spec = REVENUE_BENEFITS_SPEC["form"]
            revenue_items = gr.State([])

            gr.Markdown(f"# {REVENUE_BENEFITS_SPEC['title']}")
            gr.Markdown(REVENUE_BENEFITS_SPEC["instructions"])

            with gr.Accordion("Especificacion del paso", open=False):
                gr.JSON(REVENUE_BENEFITS_SPEC)

            with gr.Group():
                revenue_item = gr.Textbox(
                    label=revenue_form_spec["entry_label"],
                    placeholder=revenue_form_spec["entry_placeholder"],
                    lines=revenue_form_spec["entry_lines"],
                )
                with gr.Row():
                    add_revenue_item_button = gr.Button(revenue_form_spec["add_button_label"])
                    load_revenue_item_button = gr.Button(revenue_form_spec["load_button_label"])
                    update_revenue_item_button = gr.Button(revenue_form_spec["update_button_label"])
                    delete_revenue_item_button = gr.Button(revenue_form_spec["delete_button_label"])
                revenue_items_display = gr.Textbox(
                    label=revenue_form_spec["list_label"],
                    lines=8,
                    interactive=False,
                )
                revenue_item_to_edit = gr.Dropdown(
                    label=revenue_form_spec["selected_item_label"],
                    choices=[],
                    interactive=True,
                )
            with gr.Group():
                process_revenue_items = gr.Button(
                    revenue_form_spec["submit_label"],
                    variant="primary",
                )
                revenue_output = gr.Textbox(
                    label=revenue_form_spec["output_label"],
                    lines=revenue_form_spec["output_lines"],
                    interactive=False,
                )
            with gr.Group():
                with gr.Row():
                    previous_revenue_step = gr.Button(revenue_form_spec["previous_step_label"])
                    next_revenue_step = gr.Button(
                        revenue_form_spec["next_step_label"],
                        variant="secondary",
                        visible=False,
                    )

            previous_revenue_step.click(
                fn=lambda: gr.update(selected="investment"),
                outputs=pvb_tabs,
            )
            add_revenue_item_button.click(
                fn=add_list_item,
                inputs=[revenue_item, revenue_items],
                outputs=[
                    revenue_items,
                    revenue_items_display,
                    revenue_item_to_edit,
                    revenue_item,
                ],
            )
            load_revenue_item_button.click(
                fn=load_selected_item,
                inputs=revenue_item_to_edit,
                outputs=revenue_item,
            )
            update_revenue_item_button.click(
                fn=update_list_item,
                inputs=[revenue_item_to_edit, revenue_item, revenue_items],
                outputs=[
                    revenue_items,
                    revenue_items_display,
                    revenue_item_to_edit,
                    revenue_item,
                ],
            )
            delete_revenue_item_button.click(
                fn=delete_list_item,
                inputs=[revenue_item_to_edit, revenue_items],
                outputs=[
                    revenue_items,
                    revenue_items_display,
                    revenue_item_to_edit,
                    revenue_item,
                ],
            )
            process_revenue_items.click(
                fn=process_revenue_benefits,
                inputs=[revenue_items, llm_model],
                outputs=[revenue_output, next_revenue_step],
            )
            next_revenue_step.click(
                fn=lambda: gr.update(selected="generate_document"),
                outputs=pvb_tabs,
            )

        with gr.Tab("Generar Documento", id="generate_document"):
            gr.Markdown("# Generar Documento")
            with gr.Accordion("Documento final", open=True):
                with gr.Group():
                    export_basename = gr.Textbox(
                        label="Nombre sugerido del archivo",
                        value=DEFAULT_EXPORT_BASENAME,
                    )
                    export_document_button = gr.Button(
                        "Generar documento Markdown",
                        variant="primary",
                    )
                    export_status = gr.Textbox(
                        label="Documento generado",
                        interactive=False,
                    )
                    with gr.Accordion("Detalle del documento", open=False):
                        export_path = gr.Textbox(
                            label="Ruta del archivo",
                            interactive=False,
                        )

            export_document_button.click(
                fn=generate_final_markdown_document,
                inputs=export_basename,
                outputs=[export_status, export_path],
            )

    session_save_inputs = [
        session_name,
        llm_model,
        comments,
        target_items,
        target_item,
        business_items,
        business_item,
        need_items,
        need_item,
        pps_items,
        pps_item,
        competition_items,
        competition_item,
        channels_items,
        channels_item,
        investment_items,
        investment_team,
        investment_hours,
        investment_role,
        investment_start_date,
        investment_end_date,
        revenue_items,
        revenue_item,
        output,
        target_output,
        business_output,
        need_output,
        pps_output,
        competition_output,
        channels_output,
        investment_output,
        revenue_output,
    ]
    save_session_button.click(
        fn=save_current_session,
        inputs=session_save_inputs,
        outputs=[session_status, session_path_output, session_file],
    )
    refresh_sessions_button.click(
        fn=refresh_session_file_choices,
        outputs=session_file,
    )
    load_session_button.click(
        fn=load_session_into_ui,
        inputs=session_file,
        outputs=[
            session_status,
            session_name,
            llm_model,
            comments,
            output,
            next_step,
            target_items,
            target_items_display,
            target_item_to_delete,
            target_item,
            target_output,
            next_target_step,
            business_items,
            business_items_display,
            business_item_to_delete,
            business_item,
            business_output,
            next_business_step,
            need_items,
            need_items_display,
            need_item_to_edit,
            need_item,
            need_output,
            next_need_step,
            pps_items,
            pps_items_display,
            pps_item_to_edit,
            pps_item,
            pps_output,
            next_pps_step,
            competition_items,
            competition_items_display,
            competition_item_to_edit,
            competition_item,
            competition_output,
            next_competition_step,
            channels_items,
            channels_items_display,
            channels_item_to_edit,
            channels_item,
            channels_output,
            next_channels_step,
            investment_items,
            investment_items_display,
            investment_item_to_edit,
            investment_team,
            investment_hours,
            investment_role,
            investment_fte,
            investment_estimate,
            investment_start_date,
            investment_end_date,
            investment_output,
            next_investment_step,
            revenue_items,
            revenue_items_display,
            revenue_item_to_edit,
            revenue_item,
            revenue_output,
            next_revenue_step,
        ],
    )


if __name__ == "__main__":
    demo.launch(share=False)
