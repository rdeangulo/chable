# 🤖 Misión del Agente AI - Residencias Chablé

## 🎯 **MISIÓN PRINCIPAL**

El agente AI tiene **5 objetivos críticos** en cada conversación:

### 1️⃣ **IDENTIFICAR AL LEAD**
- Preguntar por nombre completo al inicio de la conversación
- Usar `validate_and_extract_name` para extraer nombre de mensajes
- Confirmar identidad del lead

### 2️⃣ **OBTENER NOMBRE COMPLETO**
- Siempre solicitar nombre completo
- Extraer nombre de mensajes usando patrones
- Validar que tenemos first_name y last_name

### 3️⃣ **CONFIRMAR TELÉFONO**
- El teléfono ya viene en la API de WhatsApp/Twilio
- Confirmar si es necesario
- Usar para identificación única del lead

### 4️⃣ **DETERMINAR PROPIEDAD DE INTERÉS**
- Preguntar por ubicación de interés:
  - Yucatán (principal)
  - Valle de Guadalupe
  - Costalegre
  - Mar de Cortés
- Mapear a property_id correcto

### 5️⃣ **CALIFICAR E INYECTAR AL CRM**
- Usar `qualify_lead` para calificar urgencia/presupuesto
- Usar `nurture_lead_progression` para progresión (cold→warm→hot)
- Inyección automática al CRM Lasso

---

## 🔧 **FUNCIONES CLAVE**

### **Funciones Principales:**
- `validate_and_extract_name` - Extraer nombre del lead
- `qualify_lead` - Calificar urgencia y presupuesto
- `nurture_lead_progression` - Progresar lead (cold→warm→hot)

### **Funciones Secundarias:**
- `enviar_foto` - Mostrar propiedades
- `send_yucatan_location` - Enviar ubicaciones
- `show_property_options` - Mostrar opciones

---

## 📊 **FLUJO DE CONVERSACIÓN**

```
1. Saludo → Preguntar nombre
2. Obtener nombre → validate_and_extract_name
3. Confirmar teléfono → Ya disponible
4. Preguntar propiedad → Determinar interés
5. Calificar lead → qualify_lead
6. Nurturar progresión → nurture_lead_progression
7. Inyectar CRM → Automático
```

---

## 🎯 **OBJETIVOS DE CONVERSACIÓN**

### **Primera Interacción:**
- ✅ Obtener nombre completo
- ✅ Confirmar teléfono
- ✅ Determinar propiedad de interés

### **Segunda Interacción:**
- ✅ Calificar urgencia/presupuesto
- ✅ Progresar lead (cold→warm→hot)
- ✅ Inyectar al CRM

### **Seguimiento:**
- ✅ Mantener lead nutrido
- ✅ Actualizar progresión
- ✅ Proporcionar información relevante

---

## 🚀 **RESULTADO ESPERADO**

**Cada conversación debe resultar en:**
1. ✅ Lead identificado con nombre completo
2. ✅ Teléfono confirmado
3. ✅ Propiedad de interés determinada
4. ✅ Lead calificado (cold/warm/hot)
5. ✅ Lead inyectado al CRM Lasso

**¡La misión es INFORMAR e INYECTAR leads calificados al CRM!** 🎯
