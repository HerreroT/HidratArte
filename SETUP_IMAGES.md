# 📸 Configuración de Imágenes para Productos - HidratArte

## ✅ Cambios Realizados

### Backend (Django)
1. ✅ Agregado campo `image` al modelo `Product`
2. ✅ Actualizado `ProductSerializer` para incluir imagen con URL completa
3. ✅ Configurado `MEDIA_URL` y `MEDIA_ROOT` en settings.py
4. ✅ Agregado soporte para servir archivos media en urls.py
5. ✅ Mejorado admin de productos para gestionar imágenes

### Frontend (React)
6. ✅ Actualizado `CategoryList.js` para usar imágenes de la API

---

## 🚀 Pasos para Implementar

### 1️⃣ Instalar Pillow (Librería de imágenes de Python)

```bash
cd "c:\Users\Tomás Nasif Herrero\Desktop\HidratArte"
pip install Pillow
```

### 2️⃣ Crear las Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3️⃣ Crear la Carpeta Media

```bash
mkdir media
mkdir media\products
```

### 4️⃣ Reiniciar el Servidor Django

```bash
python manage.py runserver
```

---

## 📝 Cómo Subir Imágenes a los Productos

### Opción A: Desde el Admin de Django

1. Ve a `http://localhost:8000/admin/`
2. Inicia sesión con tu usuario admin
3. Ve a **Main > Products**
4. Selecciona un producto o crea uno nuevo
5. En el campo **Image**, haz clic en "Elegir archivo"
6. Sube una imagen (PNG, JPG, WEBP)
7. Guarda el producto

### Opción B: Desde la API (Postman o código)

```python
import requests

url = "http://localhost:8000/main/model/products/"
files = {'image': open('ruta/a/imagen.jpg', 'rb')}
data = {
    'name': 'Agua Mineral',
    'description': 'Agua pura de manantial',
    'price': 2.50,
    'stock': 100,
    'category': 'agua'
}

response = requests.post(url, data=data, files=files)
print(response.json())
```

---

## 🖼️ Formatos de Imagen Recomendados

- **Formato**: JPG, PNG, WEBP
- **Tamaño**: 800x800px (cuadradas)
- **Peso**: < 500KB
- **Relación de aspecto**: 1:1 (cuadrada) preferiblemente

---

## 📂 Estructura de Archivos

```
HidratArte/
├── media/                    ← NUEVA CARPETA
│   └── products/             ← Imágenes de productos
│       ├── imagen1.jpg
│       ├── imagen2.png
│       └── ...
├── main/
│   ├── models.py            ← MODIFICADO (campo image)
│   ├── serializer.py        ← MODIFICADO (incluye image)
│   └── admin.py             ← MODIFICADO (admin mejorado)
├── HIDRATARTE/
│   ├── settings.py          ← MODIFICADO (MEDIA_URL, MEDIA_ROOT)
│   └── urls.py              ← MODIFICADO (servir media)
└── manage.py
```

---

## 🔍 Verificar que Funciona

### 1. Crear un producto con imagen desde admin
1. Ve a admin de Django
2. Crea/edita un producto
3. Sube una imagen
4. Guarda

### 2. Verificar la URL de la imagen
La API debería devolver:
```json
{
  "id": 1,
  "name": "Agua Mineral",
  "description": "Agua pura",
  "price": "2.50",
  "stock": 100,
  "category": "agua",
  "image": "http://localhost:8000/media/products/agua_mineral.jpg"
}
```

### 3. Ver en el frontend
- Abre `http://localhost:3000`
- Ve a cualquier categoría (Agua, Jugo, Gaseosa, Alcohol)
- Los productos deberían mostrar sus imágenes
- Si no tienen imagen, se muestra `/images/default.png`

---

## 🐛 Troubleshooting

### Error: "No module named 'PIL'"
**Solución:**
```bash
pip install Pillow
```

### Error: "ERRORS: main.Product.image: (fields.E210)"
**Solución:** Asegúrate de tener Pillow instalado antes de hacer las migraciones.

### Las imágenes no se ven en el frontend
**Verificar:**
1. ¿El servidor Django está corriendo?
2. ¿La URL de la imagen es correcta? (debe ser `http://localhost:8000/media/...`)
3. ¿Hay CORS habilitado? (ya está configurado en settings.py)
4. Abre la consola del navegador (F12) y verifica errores

### Error 404 al acceder a /media/...
**Solución:**
1. Verifica que `DEBUG = True` en settings.py
2. Verifica que agregaste el código en urls.py para servir media

---

## 📸 Recomendaciones de Imágenes

### Agua
- Botellas de agua clara
- Fondo blanco o transparente
- Vista frontal

### Jugo
- Vasos con jugo o cajas
- Colores vibrantes
- Incluir frutas si es posible

### Gaseosa
- Botellas o latas
- Vista frontal con etiqueta visible
- Fondo neutro

### Alcohol
- Botellas de vino, cerveza, etc.
- Etiquetas visibles
- Fondo oscuro o neutro

---

## 🎨 Optimización de Imágenes (Opcional)

Para mejorar el rendimiento, puedes usar herramientas para optimizar imágenes:

### Online:
- TinyPNG: https://tinypng.com/
- Squoosh: https://squoosh.app/

### Python (automático):
```python
# Instalar
pip install pillow

# Crear script para optimizar
from PIL import Image
import os

def optimize_image(input_path, output_path, quality=85):
    img = Image.open(input_path)
    img = img.convert('RGB')
    img.thumbnail((800, 800))
    img.save(output_path, 'JPEG', quality=quality, optimize=True)
```

---

## 🔐 Seguridad para Producción

Cuando despliegues a producción:

1. **Usar S3 o servicio de almacenamiento**
```python
# Instalar
pip install django-storages boto3

# Configurar en settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

2. **Validar tipos de archivo**
```python
# En models.py
from django.core.validators import FileExtensionValidator

image = models.ImageField(
    upload_to='products/',
    validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
    null=True,
    blank=True
)
```

3. **Limitar tamaño de archivo**
```python
# Crear validators.py
from django.core.exceptions import ValidationError

def validate_file_size(file):
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'El archivo no puede ser mayor a {max_size_mb}MB')
```

---

## ✅ Checklist Final

- [ ] Pillow instalado
- [ ] Migraciones creadas y ejecutadas
- [ ] Carpeta `media/products/` creada
- [ ] Servidor Django reiniciado
- [ ] Admin de Django funciona para subir imágenes
- [ ] API devuelve URLs de imágenes correctamente
- [ ] Frontend muestra las imágenes
- [ ] Imagen por defecto funciona cuando no hay imagen

---

## 🎉 ¡Listo!

Ahora puedes agregar imágenes a tus productos y se mostrarán automáticamente en el frontend.

**Próximos pasos:**
1. Sube imágenes para todos tus productos
2. Considera usar miniaturas (thumbnails) para mejor rendimiento
3. Agrega validación de tamaño y tipo de archivo
4. Implementa carga de imágenes desde el frontend (upload de imágenes)
