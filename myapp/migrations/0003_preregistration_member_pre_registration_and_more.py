# Generated by Django 4.2.20 on 2025-03-31 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_contact_alter_payment_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.CharField(max_length=8, unique=True)),
                ('role', models.CharField(choices=[('trainer', 'Trainer'), ('member', 'Member')], max_length=10)),
                ('email', models.EmailField(max_length=254)),
                ('full_name', models.CharField(max_length=100)),
                ('is_registered', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('registered_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='member',
            name='pre_registration',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.preregistration'),
        ),
        migrations.AddField(
            model_name='trainer',
            name='pre_registration',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.preregistration'),
        ),
    ]
