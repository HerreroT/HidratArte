# 🚀 Configuración de Volumen en Railway para Imágenes

## 📋 Resumen de Cambios Realizados

El código ya ha sido actualizado en `HIDRATARTE/settings.py` para detectar y usar el volumen de Railway automáticamente.

---

## ✅ Pasos en Railway

### 1. Crear y Configurar el Volumen

1. Ve a tu proyecto en [Railway](https://railway.app)
2. Busca el servicio de Django (tu backend)
3. Haz clic en **"Add Volume"** (o **"Add Service"** > **"Volume"**)
4. Configura el volumen:
   - **Nombre**: `media-storage` (o cualquier nombre)
   - **Mount Path**: `/images` ⚠️ **IMPORTANTE**: Especifica exactamente `/images`
   - **Size**: 10GB (ajusta según necesites)
5. Adjunta el volumen a tu servicio Django

### 2. Verificar la Variable de Entorno

Railway automáticamente crea una variable de entorno `RAILWAY_VOLUME_MOUNT_PATH` que apunta al mount path que configuraste.

**NO NECESITAS** configurar manualmente `MEDIA_ROOT` en Railway. El código detectará automáticamente el volumen.

### 3. Desplegar los Cambios

1. Haz commit de los cambios:
   ```bash
   git add HIDRATARTE/settings.py
   git commit -m "feat: configurar MEDIA_ROOT para volumen de Railway"
   git push origin release
   ```

2. Railway desplegará automáticamente los cambios

### 4. Verificar que Funciona

Después del deployment, verifica los logs de Railway:

1. Ve a **Logs** en tu servicio de Railway
2. Busca estas líneas:
   ```
   [BOOT] MEDIA_ROOT = /images
   [BOOT] MEDIA_ROOT exists: True
   [BOOT] MEDIA_ROOT is writable: True
   [BOOT] MEDIA_ROOT write test: OK
   ```

Si ves estos mensajes, **¡funciona correctamente!** ✅

---

## 🔍 Troubleshooting

### Las imágenes no se suben

**Solución:**
1. Verifica en logs que `MEDIA_ROOT = /images`
2. Verifica que el volumen esté montado correctamente en Railway
3. Revisa los logs por errores de permisos

### Error: "Permission denied"

**Solución:**
El código automáticamente crea el directorio y setea permisos. Si persiste:
1. Verifica que el volumen tenga suficiente espacio
2. Revisa los logs por errores específicos

### Las imágenes no se ven en producción

**Solución:**
1. Verifica que la URL de la imagen sea: `https://tu-dominio.com/media/products/imagen.jpg`
2. Verifica CORS está configurado (ya está en tu settings.py)
3. Abre las DevTools del navegador y revisa errores en la consola

---

## 📁 Estructura del Volumen

Dentro del volumen `/images`, se creará automáticamente:

```
/images/
├── _write_test.txt           (archivo de prueba)
└── products/                  (subcarpeta para productos)
    └── [archivos de imagen]
```

---

## 🔐 Notas de Seguridad

- ✅ Los archivos se guardan de forma persistente en el volumen
- ✅ Los volúmenes no se eliminan al hacer redeploy
- ✅ Los volúmenes solo son accesibles desde el servicio que los monta

---

## 📝 Próximos Pasos

1. ✅ Código actualizado
2. ⏳ Crear volumen en Railway
3. ⏳ Hacer push de los cambios
4. ⏳ Verificar logs
5. ⏳ Probar subir una imagen desde el admin

---

## 🆘 ¿Necesitas Ayuda?

Si algo no funciona:

1. Revisa los logs en Railway (Menú de tu servicio → Logs)
2. Verifica que `RAILWAY_VOLUME_MOUNT_PATH` esté configurado
3. Hazme saber y te ayudo a debuggear

