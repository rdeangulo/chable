# 📋 Resumen Técnico para Ingeniero del CRM

## 🎯 **Pregunta del Cliente**
> "Oye me preguntaba Miguel si tienes el endpoint al que estás apuntando y el JSON que estás insertando"

## ✅ **Respuesta Completa**

### 🔗 **Endpoint Principal**
```
POST https://api.lassocrm.com/v1/registrants
```

### 📄 **JSON Exacto que Enviamos**

```json
{
  "lasso_uid": "TU_LASSO_UID",
  "property_id": 24610,
  "property_name": "Yucatan",
  "contact": {
    "first_name": "Cliente",
    "last_name": "WhatsApp", 
    "email": "",
    "phone": "+573162892694",
    "source": "WhatsApp",
    "lead_source": "WhatsApp Bot",
    "notes": "Lead from WhatsApp Bot - General inquiry"
  },
  "lead_details": {
    "interest_level": "medium",
    "budget_min": null,
    "budget_max": null,
    "property_type": "",
    "city_interest": "yucatan",
    "visit_requested": false,
    "call_requested": false,
    "information_requested": true
  },
  "metadata": {
    "created_at": "2024-09-24T16:30:00.000Z",
    "platform": "WhatsApp",
    "thread_id": null,
    "conversation_summary": "Lead creado automáticamente - Rating: initial"
  }
}
```

---

## 🏢 **Property IDs que Usamos**

| Región | Property ID | Nombre |
|--------|-------------|--------|
| Yucatán | 24610 | Yucatan |
| Valle de Guadalupe | 24611 | Valle de Guadalupe |
| Costalegre | 24609 | Costalegre |
| Residencias | 24608 | Residencias |

---

## 🔧 **Headers que Enviamos**

```http
Authorization: Bearer {API_KEY}
Content-Type: application/json
Accept: application/json
```

---

## 🚨 **Error Actual que Estamos Recibiendo**

```json
{
  "errorCode": 400,
  "error": "Bad Request", 
  "errorMessage": "First name cannot be null or empty"
}
```

**Solución Implementada:** Ahora siempre enviamos `first_name` y `last_name` con valores por defecto.

---

## 📁 **Archivos de Código**

- **Servicio Principal:** `app/services/lasso_crm_service.py` (líneas 190-220)
- **Integración:** `app/crm_integration.py`
- **Procesamiento:** `app/main.py`

---

## 🔍 **Para Debugging**

### **Logs Relevantes:**
```python
logger.info(f"Lasso CRM lead data - first_name: '{first_name}', last_name: '{last_name}', phone: '{phone}'")
```

### **Validación de Datos:**
```python
# Líneas 183-186 en lasso_crm_service.py
if not first_name or not last_name:
    first_name = "Cliente"
    last_name = "WhatsApp"
```

---

## ✅ **Estado Actual**

- ✅ Endpoint: `https://api.lassocrm.com/v1/registrants`
- ✅ JSON: Estructura completa documentada
- ✅ Headers: Authorization + Content-Type
- ✅ Validación: first_name/last_name siempre presentes
- ✅ Property IDs: Mapeo completo de regiones

**¿Necesitas algún detalle específico adicional?**
