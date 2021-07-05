# Generated by Django 3.2.4 on 2021-07-04 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0002_alter_city_uuid'),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.AddField(
            model_name='book',
            name='genres',
            field=models.ManyToManyField(related_name='books', to='book.Genre'),
        ),
    ]