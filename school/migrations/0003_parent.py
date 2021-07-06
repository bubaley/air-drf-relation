# Generated by Django 3.2.4 on 2021-07-05 15:32

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0002_auto_20210704_1400'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=128)),
            ],
        ),
    ]