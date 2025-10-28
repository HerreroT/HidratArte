"""
Script para copiar imágenes locales al volumen de Railway.

NOTA: Este script está diseñado para ejecutarse LOCALMENTE
para luego copiar las imágenes usando Railway CLI.

Pasos:
1. Ejecutar este script localmente para listar las imágenes
2. Usar Railway CLI para copiar los archivos
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media" / "products"

print("📸 Imágenes encontradas en media/products/:\n")

if MEDIA_DIR.exists():
    images = list(MEDIA_DIR.glob("*"))
    for img in images:
        print(f"  ✓ {img.name}")
    
    print(f"\n📋 Total: {len(images)} archivos")
    print("\n")
    print("=" * 60)
    print("SIGUIENTE PASO: Copiar estas imágenes a Railway")
    print("=" * 60)
    print("\nOpción 1: Manual desde Admin Django")
    print("  1. Ve a https://hidratarte-production.up.railway.app/admin/")
    print("  2. Edita cada producto y sube su imagen")
    print("\nOpción 2: Usar Railway CLI (requiere instalación)")
    print("  1. Instalar: npm i -g @railway/cli")
    print("  2. Login: railway login")
    print("  3. Link: railway link")
    print("  4. Copiar: railway run bash")
    print("     Luego copiar archivos manualmente")
    print("\nOpción 3: Script Python en Railway")
    print("  Ver script en migrate_images_to_volume.py")
else:
    print("❌ No se encontró el directorio media/products/")

