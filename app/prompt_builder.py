#!/usr/bin/env python3
"""
Prompt Builder for Chablé Residences AI Agent
=============================================

Builds the system prompt from a structured knowledge base and
standard guardrails. Centralizes persona, policies, and key facts.
"""

import json
import os
from typing import Dict, Any, Optional


def _load_kb() -> Dict[str, Any]:
    """Load the structured knowledge base bundled with the app."""
    kb_path = os.path.join(os.path.dirname(__file__), "kb", "knowledge_base.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _format_projects_section(kb: Dict[str, Any]) -> str:
    """Create a detailed projects section from KB."""
    projects = kb.get("projects", [])
    lines = ["PROYECTOS SOPORTADOS - RESIDENCIAS DE LUJO:"]
    for p in projects:
        name = p.get("name")
        short = p.get("short")
        loc = p.get("location", {})
        city = loc.get("city")
        state = loc.get("state")
        coords = loc.get("coords")
        highlights = p.get("highlights", [])
        units = p.get("units", "")
        materials = p.get("materials", "")
        culture = p.get("culture", "")
        
        lines.append(f"\n🏛️ {name} ({short})")
        lines.append(f"📍 Ubicación: {city}, {state} | GPS: {coords}")
        if culture:
            lines.append(f"🎨 Concepto: {culture}")
        if units:
            lines.append(f"🏠 Unidades: {units}")
        if materials:
            lines.append(f"✨ Acabados: {materials}")
        if highlights:
            lines.append("🌟 Puntos Clave:")
            for highlight in highlights[:3]:  # Top 3 highlights
                lines.append(f"   • {highlight}")
    return "\n".join(lines)


def _format_policies_section(kb: Dict[str, Any]) -> str:
    """Create the policy/guardrails section."""
    policies = kb.get("policies", {})
    lines = ["RESTRICCIONES Y POLÍTICAS:"]
    if policies.get("no_cross_development"):
        lines.append("- No mezclar información entre desarrollos; si preguntan de otro, redirige al sitio correspondiente para registrarse con el broker en sitio.")
    if policies.get("if_unknown_register"):
        lines.append("- Si no sabes una respuesta, invita a registrarse para contacto con el broker en sitio.")
    if policies.get("prices_by_registration"):
        lines.append("- No revelar precios de lista; dirige a registro para precios y disponibilidad actualizados.")
    if policies.get("legal_disclaimer"):
        lines.append("- Temas legales/fiscales: información de cortesía y sujeta a confirmación; sugiere consultar a asesores legales/fiscales.")
    if policies.get("media_archive_old_do_not_use"):
        lines.append("- No usar material marcado como ARCHIVE/‘viejo’.")
    return "\n".join(lines)


def _format_crm_section(kb: Dict[str, Any]) -> str:
    """Create the CRM instructions section (no credentials)."""
    crm = kb.get("crm", {})
    req_fields = crm.get("required_fields", [])
    fields_list = ", ".join(req_fields) if req_fields else "Nombre, Teléfono"
    lines = [
        "CRM ECI LASSO:",
        f"- Capturar al menos: {fields_list}.",
        "- Calificar interés y enviar notas relevantes.",
        "- Nunca revelar credenciales ni URLs internas del CRM.",
    ]
    return "\n".join(lines)


def _format_languages_section(kb: Dict[str, Any]) -> str:
    languages = kb.get("languages", ["es", "en"])
    return "Idiomas soportados: " + ", ".join(languages)


def _format_contacts_section(kb: Dict[str, Any]) -> str:
    contacts = kb.get("sales_contacts", {})
    lines = ["CONTACTO OFICIAL POR DESARROLLO (proveer solo si lo piden explícitamente):"]
    for key, info in contacts.items():
        name = info.get("name")
        phone = info.get("phone")
        email = info.get("email")
        lines.append(f"- {key}: {name} | {phone} | {email}")
    return "\n".join(lines)


def _format_target_clients_section(kb: Dict[str, Any]) -> str:
    """Create the target clients section."""
    clients = kb.get("target_clients", {})
    lines = ["CLIENTES OBJETIVO - PERFILES DE ALTO PATRIMONIO:"]
    for key, description in clients.items():
        lines.append(f"• {description}")
    return "\n".join(lines)


def _format_sales_process_section(kb: Dict[str, Any]) -> str:
    """Create the sales process section."""
    process = kb.get("sales_process", {})
    lines = ["PROCESO DE VENTA - PASO A PASO:"]
    lines.append(f"1️⃣ {process.get('step1', '')}")
    lines.append(f"2️⃣ {process.get('step2', '')}")
    lines.append(f"3️⃣ {process.get('step3', '')}")
    lines.append(f"4️⃣ {process.get('step4', '')}")
    lines.append(f"\n⚠️ {process.get('no_financing', '')}")
    lines.append(f"📊 {process.get('progress_reports', '')}")
    return "\n".join(lines)


def _format_foreign_buyers_section(kb: Dict[str, Any]) -> str:
    """Create the foreign buyers section."""
    foreign = kb.get("foreign_buyers", {})
    lines = ["COMPRADORES EXTRANJEROS - INFORMACIÓN LEGAL:"]
    lines.append(f"✅ {foreign.get('can_buy', '')}")
    lines.append(f"⏰ {foreign.get('trust_duration', '')}")
    lines.append(f"💰 {foreign.get('closing_costs', '')}")
    lines.append(f"🛡️ {foreign.get('legal_safety', '')}")
    lines.append(f"📋 {foreign.get('rights', '')}")
    return "\n".join(lines)


def _format_differentiators_section(kb: Dict[str, Any]) -> str:
    """Create the competitive differentiators section."""
    diffs = kb.get("differentiators", {})
    lines = ["DIFERENCIADORES COMPETITIVOS:"]
    for key, description in diffs.items():
        lines.append(f"• {description}")
    return "\n".join(lines)


def _format_chatbot_role_section(kb: Dict[str, Any]) -> str:
    """Create the chatbot role section."""
    role = kb.get("chatbot_role", {})
    lines = ["ROL DEL CHATBOT - ASISTENTE DIGITAL:"]
    lines.append(f"🎯 {role.get('primary_function', '')}")
    lines.append(f"📊 {role.get('capture_qualify', '')}")
    lines.append(f"🔍 {role.get('filter_leads', '')}")
    lines.append(f"ℹ️ {role.get('inform', '')}")
    lines.append(f"👆 {role.get('direct', '')}")
    lines.append(f"🚫 {role.get('no_cross_info', '')}")
    lines.append(f"🤝 {role.get('broker_handoff', '')}")
    return "\n".join(lines)


def build_system_prompt(store_id: str, site_context: Optional[str] = None) -> str:
    """Compose the full system prompt from KB and guardrails.

    Args:
        store_id: Vector store or tenant identifier used by the agent
        site_context: Optional development key to constrain responses to a single project
    """
    kb = _load_kb()

    persona = (
        "Eres un REPRESENTANTE DE VENTAS DE LUJO especializado en The Residences at Chablé - RESIDENCIAS DE LUJO PARA VENTA. "
        "Tu MISIÓN PRINCIPAL es: 1) Identificar al lead, 2) Obtener nombre completo, 3) Confirmar teléfono (ya disponible), "
        "4) Determinar propiedad de interés, 5) Calificar e inyectar lead al CRM. "
        "IMPORTANTE: Si ya tienes el nombre del cliente, NO lo pidas de nuevo. Usa la información que ya tienes. "
        "RECUERDA: Mantén contexto de la conversación. Si el cliente ya dio su nombre, úsalo en todas las respuestas. "
        "CONTEXTO CRÍTICO: Siempre revisa el historial de conversación antes de responder. "
        "NO repitas preguntas ya hechas. NO pidas información ya proporcionada. "
        "Mantén un registro mental de: nombre, teléfono, propiedad de interés, presupuesto, urgencia. "
        "MEMORIA PERSISTENTE: Recuerda TODA la información previa del cliente. "
        "RESUMIR INTERACCIONES: Al final de cada conversación, resume los puntos clave. "
        "ENTRENAMIENTO: SIEMPRE empieza preguntando por el nombre completo del cliente. "
        "FLUJO OBLIGATORIO: 1) Saludo + pregunta por nombre, 2) Confirmar teléfono, 3) Propiedad de interés, 4) Calificar lead. "
        "ACTÚA COMO REPRESENTANTE DE LUJO: Destaca la exclusividad, ubicaciones premium, amenidades de clase mundial, "
        "y la experiencia de vida única que ofrecemos. Menciona proyectos como Yucatán (Chablé Resort), Valle de Guadalupe (vinos), "
        "y Costalegre (playa privada). Sé sofisticado, elegante y diferenciado. "
        "WhatsApp-style: máximo 2 frases (~25 palabras) y una pregunta de seguimiento por turno."
    )

    focus_line = "Enfoque principal: Yucatán." if not site_context or site_context.lower() == "yucatan" else (
        f"Contexto del sitio: {site_context}. No mezcles información con otros desarrollos."
    )

    capabilities = (
        "CAPACIDADES PRINCIPALES: 1) Identificar leads, 2) Obtener nombre completo, 3) Confirmar teléfono, "
        "4) Determinar propiedad de interés, 5) Calificar e inyectar al CRM. "
        "DIFERENCIACIÓN DE PROYECTOS: Yucatán (Chablé Resort - spa de lujo), Valle de Guadalupe (vinos premium), "
        "Costalegre (playa privada), Valle de Bravo (lago exclusivo). "
        "Funciones secundarias: enviar fotos/ubicaciones, responder preguntas, mostrar opciones. "
        "USA LAS FUNCIONES DISPONIBLES para cada acción."
    )

    languages = _format_languages_section(kb)
    projects = _format_projects_section(kb)
    policies = _format_policies_section(kb)
    crm = _format_crm_section(kb)
    contacts = _format_contacts_section(kb)
    target_clients = _format_target_clients_section(kb)
    sales_process = _format_sales_process_section(kb)
    foreign_buyers = _format_foreign_buyers_section(kb)
    differentiators = _format_differentiators_section(kb)
    chatbot_role = _format_chatbot_role_section(kb)

    lead_capture = (
        "DATOS CRÍTICOS A CAPTURAR:\n"
        "1) NOMBRE COMPLETO: Siempre preguntar al inicio\n"
        "2) TELÉFONO: Ya disponible en WhatsApp\n"
        "3) PROPIEDAD DE INTERÉS: Yucatán, Valle de Guadalupe, Costalegre, etc.\n"
        "4) CALIFICACIÓN: Urgencia, presupuesto, motivación\n"
        "5) INYECCIÓN CRM: Automática con qualify_lead y nurture_lead_progression"
    )

    sales_strategy = (
        "ESTRATEGIA DE VENTAS DE LUJO - MISIÓN PRINCIPAL:\n"
        "1) IDENTIFICAR LEAD: Pregunta por nombre completo al inicio\n"
        "2) OBTENER NOMBRE: Usa validate_and_extract_name para extraer nombre\n"
        "3) CONFIRMAR TELÉFONO: Ya disponible en WhatsApp, confirma si es necesario\n"
        "4) DETERMINAR PROPIEDAD: Pregunta por ubicación de interés destacando exclusividad:\n"
        "   - Yucatán: Chablé Resort, spa de lujo, cenotes privados\n"
        "   - Valle de Guadalupe: Vinos premium, bodegas exclusivas\n"
        "   - Costalegre: Playa privada, acceso VIP\n"
        "   - Valle de Bravo: Lago exclusivo, montaña\n"
        "5) CALIFICAR E INYECTAR: Usa qualify_lead y nurture_lead_progression para CRM\n"
        "- Funciones clave: validate_and_extract_name, qualify_lead, nurture_lead_progression\n"
        "- Destaca exclusividad, amenidades premium, experiencia única"
    )

    websites = kb.get("websites", {})
    website_lines = ["Sitios oficiales:"]
    for key, url in websites.items():
        website_lines.append(f"- {key}: {url}")

    regional_rules = (
        "Si el usuario está en el sitio de un desarrollo y pregunta de otro, redirige al sitio correspondiente para registrarse."
    )

    prompt = f"""
STORE ID: {store_id}

{persona}
{focus_line}
{languages}

REGLAS DE CONVERSACIÓN:
- Estilo breve y claro; pregunta de seguimiento útil por turno.
- Emojis solo si el usuario los usa primero.
- No compartas información no confirmada.

{policies}

{capabilities}

{sales_strategy}

{projects}

{target_clients}

{sales_process}

{foreign_buyers}

{differentiators}

{chatbot_role}

{lead_capture}

{crm}

{contacts}

{regional_rules}

{os.linesep.join(website_lines)}
""".strip()

    return prompt

#test



