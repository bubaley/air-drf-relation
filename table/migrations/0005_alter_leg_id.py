# Generated by Django 4.2.23 on 2025-06-14 21:11

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('table', '0004_material_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leg',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
