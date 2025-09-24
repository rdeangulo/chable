# Ejemplos de JSON para Lasso CRM

## 📤 **JSON Real que Estamos Enviando**

### **Ejemplo 1: Lead Nuevo para Yucatan**

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

### **Ejemplo 2: Lead con Nombre Real**

```json
{
  "lasso_uid": "TU_LASSO_UID",
  "property_id": 24610,
  "property_name": "Yucatan",
  "contact": {
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "",
    "phone": "+573162892694",
    "source": "WhatsApp",
    "lead_source": "WhatsApp Bot",
    "notes": "Lead from WhatsApp Bot - General inquiry"
  },
  "lead_details": {
    "interest_level": "high",
    "budget_min": null,
    "budget_max": null,
    "property_type": "",
    "city_interest": "yucatan",
    "visit_requested": true,
    "call_requested": true,
    "information_requested": true
  },
  "metadata": {
    "created_at": "2024-09-24T16:30:00.000Z",
    "platform": "WhatsApp",
    "thread_id": "thread_123",
    "conversation_summary": "Lead nurtured: cold → hot - Immediate action indicators: ['urgente', 'visita']"
  }
}
```

### **Ejemplo 3: Lead para Valle de Guadalupe**

```json
{
  "lasso_uid": "TU_LASSO_UID",
  "property_id": 24611,
  "property_name": "Valle de Guadalupe",
  "contact": {
    "first_name": "María",
    "last_name": "González",
    "email": "maria@email.com",
    "phone": "+525512345678",
    "source": "WhatsApp",
    "lead_source": "WhatsApp Bot",
    "notes": "Lead from WhatsApp Bot - Buying interest"
  },
  "lead_details": {
    "interest_level": "high",
    "budget_min": 500000,
    "budget_max": 1000000,
    "property_type": "residential",
    "city_interest": "valle_de_guadalupe",
    "visit_requested": true,
    "call_requested": false,
    "information_requested": true
  },
  "metadata": {
    "created_at": "2024-09-24T16:30:00.000Z",
    "platform": "WhatsApp",
    "thread_id": "thread_456",
    "conversation_summary": "Lead nurtured: warm → hot - Multiple buying signals detected"
  }
}
```

---

## 🔍 **JSON para Buscar Lead Existente**

```json
{
  "lasso_uid": "TU_LASSO_UID",
  "phone": "+573162892694",
  "property_id": 24610
}
```

---

## 📊 **Mapeo de Interest Levels**

| Valor | Descripción |
|-------|-------------|
| `"low"` | Bajo interés |
| `"medium"` | Interés medio (default) |
| `"high"` | Alto interés |

---

## 🏢 **Property IDs por Región**

| Región | Property ID | Property Name |
|--------|-------------|---------------|
| Yucatán | 24610 | Yucatan |
| Valle de Guadalupe | 24611 | Valle de Guadalupe |
| Costalegre | 24609 | Costalegre |
| Residencias | 24608 | Residencias |

---

## ⚠️ **Campos Críticos**

### **Requeridos por Lasso CRM:**
- ✅ `contact.first_name` - NO puede estar vacío
- ✅ `contact.last_name` - NO puede estar vacío  
- ✅ `contact.phone` - Formato internacional
- ✅ `property_id` - ID válido de propiedad

### **Opcionales pero Recomendados:**
- `contact.email`
- `lead_details.budget_min/max`
- `lead_details.visit_requested`
- `metadata.conversation_summary`

---

## 🚨 **Errores Actuales**

### **Error 400 - First name cannot be null or empty**
**Causa:** `contact.first_name` está vacío
**Solución:** Siempre enviar al menos "Cliente" como fallback

### **Error 404 - Property not found**  
**Causa:** `property_id` incorrecto
**Solución:** Verificar mapeo de propiedades

### **Error 401 - Unauthorized**
**Causa:** API Key incorrecto o expirado
**Solución:** Verificar `LASSO_API_KEY_*` en variables de entorno
