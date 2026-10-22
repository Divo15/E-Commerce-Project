from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0003_account_verification_and_limits')]
    operations = [migrations.AddField(model_name='account', name='google_subject', field=models.CharField(max_length=255, unique=True, null=True, blank=True))]
