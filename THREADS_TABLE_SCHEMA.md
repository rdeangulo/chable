# Threads Table Schema

## 📋 **Campos de la Tabla `threads`**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Primary Key | ID único del thread |
| `sender` | String | Número de teléfono del remitente |
| `sender_platform` | String | Plataforma del remitente (WhatsApp, etc.) |
| `sender_display_name` | String | Nombre mostrado del remitente |
| `thread_id` | String | ID único del hilo de conversación |
| `created_at` | DateTime | Fecha de creación |
| `last_conversation_at` | DateTime | Última actividad en la conversación |
| `follow_up_need_sent` | Boolean | Si se necesita seguimiento |
| `follow_up_sent_at` | DateTime | Cuándo se envió el seguimiento |
| `is_paused` | Boolean | Si el thread está pausado |
| `referral_source_type` | String | Tipo de fuente de referencia |
| `referral_source_id` | String | ID de la fuente de referencia |
| `referral_source_url` | String | URL de la fuente de referencia |
| `referral_header` | String | Encabezado de referencia |
| `referral_body` | String | Cuerpo de referencia |
| `ctwa_clid` | String | ID de CTWA |
| `button_text` | String | Texto del botón |
| `button_payload` | String | Payload del botón |

## 🔍 **Consultas Comunes**

### **Buscar Thread por Sender:**
```python
thread_record = db.query(Thread).filter_by(sender=phone_number).first()
```

### **Buscar Thread por Thread ID:**
```python
thread_record = db.query(Thread).filter_by(thread_id=thread_id).first()
```

### **Obtener Conversación:**
```python
if thread_record and thread_record.conversation_data:
    conversation_data = json.loads(thread_record.conversation_data)
    messages = conversation_data.get("messages", [])
```

## ✅ **Corrección Aplicada**

**Antes (Incorrecto):**
```python
thread_record = db.query(Thread).filter_by(telefono=phone_number).first()
```

**Después (Correcto):**
```python
thread_record = db.query(Thread).filter_by(sender=phone_number).first()
```

## 🎯 **Uso en Lead Nurturing**

El campo `sender` se usa para:
- ✅ Recuperar historial de conversación
- ✅ Analizar progresión del lead
- ✅ Contextualizar respuestas del AI
- ✅ Determinar nivel de nurturing (cold/warm/hot)
