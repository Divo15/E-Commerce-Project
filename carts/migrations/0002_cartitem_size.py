from django.db import migrations, models


def assign_unambiguous_sizes(apps, schema_editor):
    CartItem = apps.get_model('carts', 'CartItem')
    cart_items = CartItem.objects.using(schema_editor.connection.alias)
    cart_items.filter(product__size_type='free_size').update(size='free_size')
    cart_items.filter(product__size_type='no_size').update(size='no_size')


class Migration(migrations.Migration):
    dependencies = [
        ('carts', '0001_initial'),
        ('store', '0008_alter_product_size_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='size',
            field=models.CharField(
                blank=True,
                choices=[
                    ('no_size', 'No size'),
                    ('s', 'S'),
                    ('xl', 'XL'),
                    ('xxl', 'XXL'),
                    ('free_size', 'Free Size'),
                ],
                default='',
                max_length=20,
            ),
        ),
        migrations.RunPython(assign_unambiguous_sizes, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='cartitem',
            name='unique_product_per_cart',
        ),
        migrations.AddConstraint(
            model_name='cartitem',
            constraint=models.UniqueConstraint(
                fields=('cart', 'product', 'size'),
                name='unique_product_size_per_cart',
            ),
        ),
    ]
