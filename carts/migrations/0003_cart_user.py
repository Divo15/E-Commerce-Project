from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('carts', '0002_cartitem_size'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.AddField(
        model_name='cart', name='user',
        field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saved_cart', to=settings.AUTH_USER_MODEL),
    )]
