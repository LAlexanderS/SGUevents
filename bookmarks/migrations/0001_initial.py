# Generated by Django 4.2.11 on 2024-07-01 11:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events_available', '0001_initial'),
        ('events_cultural', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
            ],
            options={
                'verbose_name': 'Избранные',
                'verbose_name_plural': 'Избранные',
            },
        ),
        migrations.CreateModel(
            name='Registered',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
                ('attractions', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='events_cultural.attractions', verbose_name='Достопримечательности')),
                ('for_visiting', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='events_cultural.events_for_visiting', verbose_name='Доступные для посещения')),
                ('offline', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='events_available.events_offline', verbose_name='Оффлайн')),
                ('online', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='events_available.events_online', verbose_name='Онлайн')),
            ],
            options={
                'verbose_name': 'Зарегистрированные',
                'verbose_name_plural': 'Зарегистрированные',
            },
        ),
    ]

