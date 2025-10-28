"""
Script para subir todas las imágenes locales a Railway via API.

Este script:
1. Lee todas las imágenes de media/products/
2. Obtiene la lista de productos de la API
3. Para cada producto, actualiza su imagen

USO:
    python migrate_images.py
"""

import requests
import os
from pathlib import Path

# Configuración
API_BASE = "https://hidratarte-production.up.railway.app"
MEDIA_DIR = Path("media/products")

# Tu token de admin (reemplázalo)
ADMIN_TOKEN = "TU_TOKEN_AQUI"

def get_products():
    """Obtener todos los productos de la API."""
    url = f"{API_BASE}/main/model/products/"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

def update_product_image(product_id, image_path):
    """Actualizar la imagen de un producto."""
    url = f"{API_BASE}/main/model/products/{product_id}/"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Leer archivo
    with open(image_path, 'rb') as f:
        files = {'image_upload': f}
        data = {}  # No enviar otros datos
        
        response = requests.patch(url, headers=headers, files=files, data=data)
        return response.status_code == 200, response.json()

def main():
    print("📸 Migrando imágenes a Railway...\n")
    
    # Obtener productos
    products = get_products()
    print(f"✓ Encontrados {len(products)} productos\n")
    
    # Mapear por nombre de imagen
    image_map = {}
    if MEDIA_DIR.exists():
        for img_file in MEDIA_DIR.glob("*"):
            if img_file.is_file():
                image_map[img_file.name] = img_file
                print(f"  📁 {img_file.name}")
    
    print(f"\n✓ {len(image_map)} imágenes disponibles\n")
    
    # Actualizar productos
    updated = 0
    for product in products:
        prod_name = product.get('name', '').lower().replace(' ', '_')
        # Buscar imagen aproximada
        for img_name, img_path in image_map.items():
            if prod_name in img_name.lower() or img_name in product.get('name', '').lower():
                print(f"Actualizando {product['name']} con {img_name}...")
                success, result = update_product_image(product['id'], img_path)
                if success:
                    print(f"  ✓ Actualizado correctamente")
                    updated += 1
                else:
                    print(f"  ✗ Error: {result}")
                break
    
    print(f"\n✅ Proceso completado: {updated}/{len(products)} productos actualizados")

if __name__ == "__main__":
    print("""
    ⚠️  IMPORTANTE: 
    1. Reemplaza ADMIN_TOKEN con tu token JWT
    2. Para obtener tu token, inicia sesión en el frontend
    3. Abre DevTools > Application > Local Storage
    4. Busca 'access' o 'token'
    """)
    # main()  # Descomentar cuando tengas el token

