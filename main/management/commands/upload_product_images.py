"""
Management command para subir imágenes de productos desde carpeta local al servidor.

Uso:
    python manage.py upload_product_images
"""
from django.core.management.base import BaseCommand
from django.core.files import File
from main.models import Product
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Sube imágenes de productos desde media/products/ local al volumen de Railway'

    def handle(self, *args, **options):
        # Directorio local de imágenes
        local_media = Path(__file__).resolve().parent.parent.parent.parent / 'media' / 'products'
        
        if not local_media.exists():
            self.stdout.write(self.style.ERROR(f'❌ No existe el directorio: {local_media}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'📁 Buscando imágenes en: {local_media}'))
        
        # Obtener todas las imágenes disponibles
        available_images = {}
        for img_file in local_media.glob('*'):
            if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                # Guardar nombre base sin extensión para matching
                base_name = img_file.stem.lower()
                available_images[base_name] = img_file
                self.stdout.write(f'  ✓ Encontrada: {img_file.name}')
        
        if not available_images:
            self.stdout.write(self.style.WARNING('⚠️  No se encontraron imágenes'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n📦 Total de imágenes: {len(available_images)}\n'))
        
        # Procesar productos
        products = Product.objects.all()
        updated = 0
        skipped = 0
        errors = 0
        
        for product in products:
            try:
                # Normalizar nombre del producto para buscar imagen
                product_name = product.name.lower().replace(' ', '_').replace('-', '_')
                
                # Buscar imagen que coincida
                matched_image = None
                for base_name, img_path in available_images.items():
                    if product_name in base_name or base_name in product_name:
                        matched_image = img_path
                        break
                
                if not matched_image:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  {product.name} (ID: {product.id}) - No se encontró imagen'
                    ))
                    skipped += 1
                    continue
                
                # Subir imagen
                with open(matched_image, 'rb') as f:
                    product.image.save(
                        matched_image.name,
                        File(f),
                        save=True
                    )
                
                self.stdout.write(self.style.SUCCESS(
                    f'✅ {product.name} (ID: {product.id}) - Subida: {matched_image.name}'
                ))
                updated += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'❌ Error en {product.name} (ID: {product.id}): {e}'
                ))
                errors += 1
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Actualizados: {updated}'))
        self.stdout.write(self.style.WARNING(f'⚠️  Sin imagen: {skipped}'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errores: {errors}'))
        self.stdout.write('='*60)

