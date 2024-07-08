# Generated by Django 4.2.11 on 2024-07-08 10:41

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
                ('name', models.CharField(max_length=150, verbose_name='Название')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='URL')),
                ('date', models.DateField(max_length=10, verbose_name='Дата')),
                ('time_start', models.TimeField(verbose_name='Время начала')),
                ('time_end', models.TimeField(verbose_name='Время окончания')),
                ('description', models.TextField(verbose_name='Описание')),
                ('speakers', models.CharField(max_length=250, verbose_name='Спикеры')),
                ('member', models.TextField(verbose_name='Участники')),
                ('tags', models.CharField(max_length=100, verbose_name='Теги')),
                ('town', models.CharField(max_length=200, verbose_name='Город')),
                ('street', models.CharField(max_length=100, verbose_name='Улица')),
                ('cabinet', models.CharField(max_length=50, verbose_name='Кабинет')),
                ('link', models.URLField(blank=True, null=True, verbose_name='Ссылка')),
                ('qr', models.FileField(blank=True, null=True, upload_to='', verbose_name='QR-код')),
                ('image', models.ImageField(blank=True, null=True, upload_to='events_available_images/offline', verbose_name='Изображение')),
                ('events_admin', models.CharField(max_length=100, verbose_name='Администратор')),
                ('documents', models.FileField(blank=True, null=True, upload_to='', verbose_name='Документы')),
                ('category', models.CharField(default='Оффлайн', max_length=30, verbose_name='Тип мероприятия')),
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
                ('name', models.CharField(max_length=150, verbose_name='Название')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='URL')),
                ('date', models.DateField(max_length=10, verbose_name='Дата')),
                ('time_start', models.TimeField(verbose_name='Время начала')),
                ('time_end', models.TimeField(verbose_name='Время окончания')),
                ('description', models.TextField(verbose_name='Описание')),
                ('speakers', models.CharField(max_length=250, verbose_name='Спикеры')),
                ('member', models.TextField(verbose_name='Участники')),
                ('tags', models.CharField(max_length=100, verbose_name='Теги')),
                ('platform', models.CharField(max_length=50, verbose_name='Платформа')),
                ('link', models.URLField(verbose_name='Ссылка')),
                ('qr', models.FileField(blank=True, null=True, upload_to='', verbose_name='QR-код')),
                ('image', models.ImageField(blank=True, null=True, upload_to='events_available_images/online', verbose_name='Изображение')),
                ('events_admin', models.CharField(max_length=100, verbose_name='Администратор')),
                ('documents', models.FileField(blank=True, null=True, upload_to='', verbose_name='Документы')),
                ('category', models.CharField(default='Онлайн', max_length=30, verbose_name='Тип мероприятия')),
            ],
            options={
                'verbose_name': 'Онлайн мероприятие',
                'verbose_name_plural': 'Онлайн',
                'db_table': 'Events_online',
            },
        ),
    ]
