from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_account_city_postal_code')]
    operations = [
        migrations.AddField(model_name='account', name='email_verification_pending', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='account', name='email_verified_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.CreateModel(name='AccountRequestLimit', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('key', models.CharField(max_length=64, unique=True)),
            ('started_at', models.DateTimeField()),
            ('count', models.PositiveIntegerField(default=0)),
        ]),
    ]
