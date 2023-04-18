# Generated by Django 3.2.4 on 2023-04-18 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0006_bookmark'),
    ]

    operations = [
        migrations.AddField(
            model_name='magazine',
            name='available_cities',
            field=models.ManyToManyField(related_name='available_magazines', to='book.City'),
        ),
    ]
