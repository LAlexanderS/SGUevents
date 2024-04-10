# Generated by Django 4.2.11 on 2024-04-10 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Events_offline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='Название')),
                ('slug', models.SlugField(blank=True, max_length=200, null=True, unique=True, verbose_name='URL')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('place', models.TextField(blank=True, null=True, verbose_name='Место')),
                ('speakers', models.TextField(blank=True, null=True, verbose_name='Спикеры')),
                ('image', models.ImageField(blank=True, null=True, upload_to='#', verbose_name='Изображение')),
            ],
            options={
                'verbose_name': 'Оффлайн мероприятие',
                'verbose_name_plural': 'Оффлайн',
                'db_table': 'Events_offline',
            },
        ),
        migrations.CreateModel(
            name='Events_online',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='Название')),
                ('slug', models.SlugField(blank=True, max_length=200, null=True, unique=True, verbose_name='URL')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('place', models.TextField(blank=True, null=True, verbose_name='Место')),
                ('speakers', models.TextField(blank=True, null=True, verbose_name='Спикеры')),
                ('image', models.ImageField(blank=True, null=True, upload_to='#', verbose_name='Изображение')),
            ],
            options={
                'verbose_name': 'Онлайн мероприятие',
                'verbose_name_plural': 'Онлайн',
                'db_table': 'Events_online',
            },
        ),
    ]
