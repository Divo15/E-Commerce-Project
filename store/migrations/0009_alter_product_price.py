from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0008_alter_product_size_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.PositiveIntegerField(),
        ),
    ]
