# 📸 Guía de Subida de Fotos a Cloudinary

## 🎯 Formato de URLs para Cloudinary

### Estructura de URL Base
```
https://res.cloudinary.com/TU_CLOUD_NAME/image/upload/vTIMESTAMP/residencias/RESIDENCIA/TIPO/archivo.jpg
```

### Ejemplo Real
```
https://res.cloudinary.com/chable_residencias/image/upload/v1704067200/residencias/kin/exterior/kin_exterior_01.jpg
```

## 📁 Estructura de Carpetas Recomendada

```
residencias/
├── kin/
│   ├── exterior/
│   │   ├── kin_exterior_01.jpg
│   │   ├── kin_exterior_02.jpg
│   │   └── kin_exterior_03.jpg
│   ├── interior/
│   │   ├── kin_sala_01.jpg
│   │   ├── kin_cocina_01.jpg
│   │   ├── kin_recamara_01.jpg
│   │   └── kin_baño_01.jpg
│   ├── amenidades/
│   │   ├── kin_piscina_01.jpg
│   │   ├── kin_cine_01.jpg
│   │   ├── kin_spa_01.jpg
│   │   └── kin_gimnasio_01.jpg
│   └── planos/
│       ├── kin_plano_01.jpg
│       └── kin_plano_02.jpg
├── kuxtal/
│   ├── exterior/
│   ├── interior/
│   ├── amenidades/
│   └── planos/
├── ool/
│   ├── exterior/
│   ├── interior/
│   ├── amenidades/
│   └── planos/
└── ool_torre/
    ├── exterior/
    ├── interior/
    ├── amenidades/
    └── planos/
```

## 🚀 Configuración de Cloudinary para WhatsApp

### Transformaciones Automáticas
El sistema aplicará automáticamente estas transformaciones para WhatsApp:

```javascript
// Para fotos normales
f_auto,q_auto,w_800,h_600,c_fill

// Para planos (más grandes)
f_auto,q_auto,w_1200,h_800,c_fill

// Para fotos de alta calidad
f_auto,q_auto,w_1024,h_768,c_fill
```

### Parámetros de Optimización
- **f_auto**: Formato automático (WebP si es compatible)
- **q_auto**: Calidad automática optimizada
- **w_800**: Ancho máximo 800px
- **h_600**: Alto máximo 600px
- **c_fill**: Recorte inteligente para mantener proporciones

## 📋 Checklist de Subida

### Para cada residencia (KIN, KUXTAL, ÓOL, ÓOL TORRE):

#### ✅ Exterior (mínimo 2-3 fotos)
- [ ] Vista frontal
- [ ] Vista lateral
- [ ] Vista desde el jardín
- [ ] Vista nocturna (opcional)

#### ✅ Interior (mínimo 4-5 fotos)
- [ ] Sala principal
- [ ] Cocina
- [ ] Recámara principal
- [ ] Baño principal
- [ ] Recámara secundaria

#### ✅ Amenidades (según disponibilidad)
- [ ] Piscina
- [ ] Terraza con ka'anche'
- [ ] Gimnasio (solo KIN)
- [ ] Cine (solo KIN)
- [ ] Spa (solo KIN)
- [ ] Jardín en azotea (solo KIN)

#### ✅ Planos (mínimo 1-2)
- [ ] Plano general
- [ ] Plano de distribución
- [ ] Plano de la torre (solo ÓOL TORRE)

## 🎨 Especificaciones Técnicas

### Formato de Archivo
- **Formato**: JPG o PNG
- **Resolución**: Mínimo 1920x1080px
- **Calidad**: Alta (para permitir optimización automática)
- **Peso**: Máximo 10MB por archivo

### Nomenclatura de Archivos
```
{residencia}_{tipo}_{numero}.jpg

Ejemplos:
- kin_exterior_01.jpg
- kuxtal_sala_01.jpg
- ool_piscina_01.jpg
- ool_torre_torre_01.jpg
```

## 🔧 Comandos de Subida (Cloudinary CLI)

### Instalación
```bash
npm install -g cloudinary-cli
```

### Configuración
```bash
cloudinary config
# Ingresa tu Cloud Name, API Key y API Secret
```

### Subida por Lotes
```bash
# Subir todas las fotos de KIN
cloudinary uploader upload "fotos/kin/*" --folder "residencias/kin" --use-filename

# Subir todas las fotos de KUXTAL
cloudinary uploader upload "fotos/kuxtal/*" --folder "residencias/kuxtal" --use-filename

# Subir todas las fotos de ÓOL
cloudinary uploader upload "fotos/ool/*" --folder "residencias/ool" --use-filename

# Subir todas las fotos de ÓOL TORRE
cloudinary uploader upload "fotos/ool_torre/*" --folder "residencias/ool_torre" --use-filename
```

## 📝 Actualización del JSON

Después de subir las fotos, actualiza el archivo `assets/fotos.json` con las URLs reales:

1. Reemplaza `tu_cloud_name` con tu Cloud Name real
2. Reemplaza `v1234567890` con el timestamp real
3. Ajusta las descripciones según las fotos reales
4. Agrega o quita fotos según lo que tengas disponible

## 🎯 Ejemplo de URL Final

```
https://res.cloudinary.com/chable_residencias/image/upload/v1704067200/residencias/kin/exterior/kin_exterior_01.jpg
```

## ⚡ Optimización Automática para WhatsApp

El sistema automáticamente convertirá las URLs a formato optimizado:

```
URL Original:
https://res.cloudinary.com/chable_residencias/image/upload/v1704067200/residencias/kin/exterior/kin_exterior_01.jpg

URL Optimizada para WhatsApp:
https://res.cloudinary.com/chable_residencias/image/upload/f_auto,q_auto,w_800,h_600,c_fill/v1704067200/residencias/kin/exterior/kin_exterior_01.jpg
```

## 🚨 Notas Importantes

1. **Backup**: Siempre mantén copias de las fotos originales
2. **Calidad**: Sube fotos en alta resolución, Cloudinary las optimizará automáticamente
3. **Nombres**: Usa nombres descriptivos y consistentes
4. **Organización**: Mantén la estructura de carpetas organizada
5. **Testing**: Prueba las URLs después de subir para asegurar que funcionan
