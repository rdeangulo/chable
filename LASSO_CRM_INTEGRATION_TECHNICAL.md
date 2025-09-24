# Lasso CRM Integration - Technical Documentation

## 📋 Información Técnica para el Ingeniero del CRM

### 🔗 **Endpoints Utilizados**

#### 1. **Crear Lead (POST)**
```
URL: https://api.lassocrm.com/v1/registrants
Method: POST
Headers:
  - Authorization: Bearer {API_KEY}
  - Content-Type: application/json
  - Accept: application/json
```

#### 2. **Buscar Lead Existente (POST)**
```
URL: https://api.lassocrm.com/v1/registrants/search
Method: POST
Headers:
  - Authorization: Bearer {API_KEY}
  - Content-Type: application/json
  - Accept: application/json
```

#### 3. **Actualizar Lead (PUT)**
```
URL: https://api.lassocrm.com/api/v1/leads/{lead_id}
Method: PUT
Headers:
  - Authorization: Bearer {API_KEY}
  - Content-Type: application/json
  - Accept: application/json
```

---

## 📄 **JSON Structure - Crear Lead**

### **Request Body para Crear Lead:**

```json
{
  "lasso_uid": "TU_LASSO_UID",
  "property_id": 24610,
  "property_name": "Yucatan",
  "contact": {
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan@email.com",
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
    "created_at": "2024-09-24T16:30:00Z",
    "platform": "WhatsApp",
    "thread_id": "thread_123",
    "conversation_summary": "Lead creado automáticamente - Rating: warm"
  }
}
```

### **Request Body para Buscar Lead:**

```json
{
  "lasso_uid": "TU_LASSO_UID",
  "phone": "+573162892694",
  "property_id": 24610,
  "email": "juan@email.com"
}
```

---

## 🏢 **Property Mapping**

### **Propiedades Configuradas:**

| Property Key | Property ID | Display Name | API Key Env Var |
|--------------|-------------|--------------|-----------------|
| `yucatan` | 24610 | Yucatan | `LASSO_API_KEY_YUCATAN` |
| `valle_de_guadalupe` | 24611 | Valle de Guadalupe | `LASSO_API_KEY_VALLE_DE_GUADALUPE` |
| `costalegre` | 24609 | Costalegre | `LASSO_API_KEY_COSTALEGRE` |
| `residencias` | 24608 | Residencias | `LASSO_API_KEY_RESIDENCIAS` |

---

## 🔧 **Variables de Entorno Requeridas**

```bash
# Lasso CRM Configuration
LASSO_UID=tu_lasso_uid_aqui
LASSO_API_KEY_YUCATAN=tu_api_key_yucatan
LASSO_API_KEY_VALLE_DE_GUADALUPE=tu_api_key_valle
LASSO_API_KEY_COSTALEGRE=tu_api_key_costalegre
LASSO_API_KEY_RESIDENCIAS=tu_api_key_residencias
```

---

## 📊 **Lead Rating System**

### **Progression Levels:**

1. **Cold/Initial** (1)
   - Keywords: "hola", "información", "precio"
   - Intent: Initial inquiry

2. **Warm** (2)
   - Keywords: "comprar", "invertir", "presupuesto"
   - Intent: Buying interest

3. **Hot** (3)
   - Keywords: "urgente", "inmediato", "visita", "llamada"
   - Intent: Immediate action

---

## 🚨 **Errores Comunes y Soluciones**

### **Error 400 - "First name cannot be null or empty"**
```json
{
  "errorCode": 400,
  "error": "Bad Request",
  "errorMessage": "First name cannot be null or empty"
}
```
**Solución:** Asegurar que `contact.first_name` y `contact.last_name` no estén vacíos.

### **Error 404 - Property not found**
**Solución:** Verificar que el `property_id` corresponda a una propiedad válida.

### **Error 401 - Unauthorized**
**Solución:** Verificar que el `API_KEY` sea correcto y tenga permisos.

---

## 🔄 **Flujo de Integración**

1. **Validar Datos**: Asegurar first_name, last_name, phone
2. **Buscar Lead Existente**: Por teléfono en la propiedad específica
3. **Crear o Actualizar**: Si no existe, crear; si existe, actualizar
4. **Manejar Respuesta**: Procesar success/error responses

---

## 📝 **Ejemplo de Uso**

```python
# Crear lead para Yucatan
lead_data = {
    "lasso_uid": "tu_uid",
    "property_id": 24610,
    "property_name": "Yucatan",
    "contact": {
        "first_name": "Juan",
        "last_name": "Pérez",
        "phone": "+573162892694",
        "source": "WhatsApp"
    }
}

# POST a https://api.lassocrm.com/v1/registrants
```

---

## 🛠️ **Archivos de Código Relevantes**

- `app/services/lasso_crm_service.py` - Servicio principal
- `app/crm_integration.py` - Integración con CRM
- `app/execute_functions.py` - Funciones de nurturing
- `app/main.py` - Procesamiento de mensajes

---

**Contacto Técnico:** Para dudas sobre la implementación, revisar los logs en `app/services/lasso_crm_service.py` línea 253-258.
