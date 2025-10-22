from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    CartItem = apps.get_model("main", "CartItem")
    Product = apps.get_model("main", "Product")
    for item in CartItem.objects.all():
        legacy_value = getattr(item, "product_id", None)
        if legacy_value is None:
            continue
        product = None
        for candidate in (legacy_value, str(legacy_value)):
            try:
                product = Product.objects.get(pk=candidate)
                break
            except Product.DoesNotExist:
                try:
                    product = Product.objects.get(pk=int(candidate))
                    break
                except (ValueError, Product.DoesNotExist):
                    continue
        if product is not None:
            item.product_temp = product
            item.save(update_fields=["product_temp"])
        else:
            # CartItem sin producto válido, se remueve para evitar inconsistencia.
            item.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_notification'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='product_temp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='migrating_cart_items', to='main.product'),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='cartitem',
            name='product_id',
        ),
        migrations.RenameField(
            model_name='cartitem',
            old_name='product_temp',
            new_name='product',
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cart_items', to='main.product'),
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'product')},
        ),
    ]

