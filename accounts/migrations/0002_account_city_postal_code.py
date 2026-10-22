from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='account',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='account',
            name='postal_code',
            field=models.CharField(blank=True, max_length=6),
        ),
    ]
