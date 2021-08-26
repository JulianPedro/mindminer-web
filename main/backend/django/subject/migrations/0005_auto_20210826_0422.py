# Generated by Django 3.2.3 on 2021-08-26 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subject', '0004_alter_subject_publication_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='history',
            options={'ordering': ['-date'], 'verbose_name': 'History', 'verbose_name_plural': 'Histories'},
        ),
        migrations.AlterModelOptions(
            name='subject',
            options={'ordering': ['-popularity', '-interaction'], 'verbose_name': 'Subject', 'verbose_name_plural': 'Subjects'},
        ),
        migrations.AlterField(
            model_name='history',
            name='date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Date'),
        ),
    ]
