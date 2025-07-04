# Generated by Django 3.2.4 on 2023-02-08 22:30

from django.db import migrations, models

import air_drf_relation.fields
import film.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Actor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Film',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('release_date', models.DateField()),
                (
                    'information',
                    air_drf_relation.model_fields.AirDataclassField(data_class=film.models.FilmInformation),
                ),
                ('actors', models.ManyToManyField(related_name='films', to='film.Actor')),
            ],
        ),
    ]
