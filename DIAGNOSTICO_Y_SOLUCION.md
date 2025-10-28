# 🔍 Diagnóstico y Solución: Imágenes 404 + Stock Fallido

## 📊 Problemas Identificados

1. **Imágenes 404**: Las imágenes no se están sirviendo desde Railway
2. **Stock Fallido**: No se puede modificar el stock desde el admin

## ✅ Análisis del Código

### 1. Imágenes (urls.py)
El código está CORRECTO:
```python
# En producción: usar serve() directamente
urlpatterns += [
    path(f'{settings.MEDIA_URL}<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]
```

### 2. Stock (views.py)
El código está CORRECTO:
```python
@action(detail=True, methods=["post"], url_path="set-stock", permission_classes=[IsAdminUser])
def set_stock(self, request, pk=None):
    # ... código correcto
```

## 🚨 Causa Real de los Problemas

### Problema 1: Imágenes 404
**Causa**: Los archivos físicos NO están en el volumen `/images`

**Evidencia**: Los logs muestran:
```
[BOOT] MEDIA_ROOT = /images
[BOOT] MEDIA_ROOT write test: OK
Not Found: /media/products/glaciar.jpg
```

**Solución**: Las imágenes necesitan estar físicamente en `/images/products/`

### Problema 2: Stock Fallido
**Causa Probable**: El endpoint tiene `permission_classes=[IsAdminUser]` que requiere que el usuario sea staff

**URL del endpoint**: `POST /main/model/products/{id}/set-stock/`

**Datos esperados**:
```json
{
  "stock": 25
}
```

## 🎯 Soluciones

### Solución 1: Imágenes - Re-subir (MÁS RÁPIDO)

1. **Ir al admin de Railway:**
   ```
   https://hidratarte-production.up.railway.app/admin/
   ```

2. **Para cada producto con imagen rota:**
   - Haz clic en "Editar"
   - En el campo "Image", haz clic en "Clear"
   - Sube la imagen de nuevo desde tu PC
   - Guarda

3. **Usa las imágenes de:** `media/products/` (localmente)

---

### Solución 2: Stock - Verificar Permisos

**Revisar en el admin**:
1. Ve a **Users**
2. Verifica que el usuario admin tiene `is_staff = True`

**Probar el endpoint manualmente**:
```bash
curl -X POST https://hidratarte-production.up.railway.app/main/model/products/1/set-stock/ \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"stock": 25}'
```

**Si falla por permisos**, la respuesta será:
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 🔧 Solución Alternativa para Imágenes

Si re-subir manualmente es mucho trabajo, puedo crear un script que:
1. Se conecte a Railway
2. Tome las imágenes de `media/products/` local
3. Las suba al volumen

¿Quieres que cree ese script?

---

## 📝 Checklist Inmediato

- [ ] Verificar que los cambios de `urls.py` se desplegaron
- [ ] Re-subir al menos 1 imagen como prueba
- [ ] Verificar que la imagen nueva funciona
- [ ] Verificar permisos del usuario admin
- [ ] Probar modificar stock de un producto

---

## 🆘 Si Aún Falla

Comparte:
1. El mensaje de error exacto al modificar stock
2. Una captura de los logs de Railway al intentar ver una imagen
3. El estado de git (`git status`)

