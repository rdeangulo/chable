# Sistema de Autoinyección de Leads

## Descripción

El sistema de autoinyección de leads está diseñado para capturar automáticamente leads valiosos que podrían perderse durante las conversaciones de WhatsApp. Utiliza análisis de IA para detectar interés en compra, información o visitas, y crea automáticamente leads calificados en el CRM.

## Características

### 🔍 Detección Automática de Interés
- **Análisis en tiempo real**: Cada mensaje se analiza para detectar indicadores de interés
- **Múltiples indicadores**: Detecta solicitudes de información, presupuesto, visitas, contacto, etc.
- **Puntuación de confianza**: Asigna una puntuación del 0-100 para determinar la calidad del lead
- **Extracción de información**: Extrae automáticamente presupuesto, ubicación, tipo de propiedad

### 🚀 Autoinyección Inteligente
- **Verificación previa**: No crea leads duplicados
- **Umbrales configurables**: Solo crea leads con confianza suficiente
- **Análisis de conversación completa**: Si un mensaje individual no detecta interés, analiza toda la conversación
- **Integración con HubSpot**: Exporta automáticamente los leads al CRM

### 📊 Monitoreo y Corrección
- **Análisis de cobertura**: Muestra estadísticas de leads capturados vs. perdidos
- **Corrección histórica**: Permite corregir leads perdidos históricamente
- **Scripts de mantenimiento**: Herramientas para verificar y corregir la base de datos

## Cómo Funciona

### 1. Detección en Tiempo Real
```python
# Cada mensaje se analiza automáticamente
interest_analysis = await detect_lead_interest(client, message_text)

# Si se detecta interés con confianza > 50%
if interest_analysis.get("shows_interest") and confidence_score >= 50:
    # Se autoinyecta el lead
    await auto_inject_missing_lead(client, db, thread_record, message_text)
```

### 2. Verificación Post-Conversación
```python
# Si no se detectó interés en el mensaje individual
if not lead_injected:
    # Se analiza toda la conversación
    lead_fixed = await verify_and_fix_missing_leads(client, db, thread_record)
```

### 3. Indicadores de Interés Detectados
- ✅ Solicita información sobre propiedades
- ✅ Menciona presupuesto o capacidad de pago
- ✅ Pregunta por visitas o citas
- ✅ Solicita contacto de asesor
- ✅ Menciona interés en comprar
- ✅ Pregunta por ubicación o características
- ✅ Solicita folletos o catálogos
- ✅ Menciona urgencia o tiempo específico

## API Endpoints

### Verificar Cobertura de Leads
```bash
GET /api/leads/coverage
```

**Respuesta:**
```json
{
  "success": true,
  "coverage": {
    "total_threads": 150,
    "threads_with_qualified_leads": 120,
    "threads_with_conversations": 140,
    "threads_with_conversations_no_leads": 20,
    "lead_coverage_percentage": 80.0,
    "missing_leads_from_conversations": 20
  }
}
```

### Corregir Leads Perdidos
```bash
POST /api/leads/fix-missing?mode=recent&days=7
```

**Parámetros:**
- `mode`: "recent" (últimos N días) o "historical" (todo el tiempo)
- `days`: Número de días para el modo "recent"

**Respuesta:**
```json
{
  "success": true,
  "message": "Fixed 15 missing leads",
  "results": {
    "total_threads_processed": 25,
    "leads_fixed": 15,
    "errors": 2,
    "mode": "recent",
    "days": 7
  }
}
```

## Scripts de Mantenimiento

### Análisis de Cobertura
```bash
python scripts/fix_missing_leads.py --mode analyze
```

### Corregir Leads Recientes
```bash
python scripts/fix_missing_leads.py --mode recent --days 7
```

### Corregir Leads Históricos
```bash
python scripts/fix_missing_leads.py --mode historical
```

## Configuración

### Umbrales de Confianza
- **Mensaje individual**: 50% (umbral mínimo para autoinyección)
- **Conversación completa**: 60% (umbral más alto para análisis completo)

### Configuración en Código
```python
# En app/utils.py
confidence_score = interest_analysis.get("confidence_score", 0)
if confidence_score < 50:  # Umbral para mensajes individuales
    return False

# Para conversaciones completas
if confidence_score < 60:  # Umbral más alto
    return False
```

## Monitoreo

### Logs Importantes
- `Auto-injected lead for {number} with confidence {score}`
- `Fixed missing lead for {number} through conversation analysis`
- `No interest detected in message from {number}`

### Métricas a Seguir
- **Cobertura de leads**: Porcentaje de conversaciones con leads calificados
- **Tasa de éxito**: Porcentaje de leads autoinyectados exitosamente
- **Leads perdidos**: Número de conversaciones sin leads calificados

## Solución de Problemas

### Leads No Detectados
1. Verificar logs para ver si se detectó interés
2. Revisar umbrales de confianza
3. Ejecutar script de corrección histórica
4. Verificar que el análisis de IA esté funcionando

### Errores de Autoinyección
1. Verificar conexión con base de datos
2. Revisar permisos de escritura
3. Verificar configuración de HubSpot
4. Revisar logs de errores específicos

### Optimización de Rendimiento
1. Ajustar umbrales de confianza según necesidades
2. Configurar análisis solo para conversaciones con múltiples mensajes
3. Implementar cache para análisis repetitivos
4. Optimizar consultas de base de datos

## Próximas Mejoras

- [ ] Análisis de sentimiento para mejor detección
- [ ] Aprendizaje automático para mejorar precisión
- [ ] Integración con más CRMs
- [ ] Dashboard de métricas en tiempo real
- [ ] Notificaciones automáticas de leads perdidos
- [ ] Análisis de patrones de conversación exitosa
