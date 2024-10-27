# Generated by Django 5.1.2 on 2024-10-27 09:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0012_alter_poll_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='poll_type',
            field=models.CharField(choices=[('question', 'Question'), ('opinion', 'Opinion Poll'), ('educational', 'Educational'), ('sports', 'Sports')], default='opinion', max_length=12),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='poll_images/')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='polls.poll')),
            ],
        ),
    ]
