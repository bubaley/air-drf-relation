# Generated by Django 3.2.4 on 2021-07-09 14:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0003_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='task',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='task.task'),
            preserve_default=False,
        ),
    ]
