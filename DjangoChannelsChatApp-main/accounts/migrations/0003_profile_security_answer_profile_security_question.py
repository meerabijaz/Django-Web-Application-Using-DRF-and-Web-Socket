# Generated by Django 5.2.4 on 2025-07-18 04:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_is_online_profile_last_seen'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='security_answer',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='security_question',
            field=models.CharField(blank=True, choices=[('pet_name', 'What was the name of your first pet?'), ('birth_city', 'In which city were you born?'), ('favorite_color', 'What is your favorite color?'), ('mother_maiden', "What is your mother's maiden name?"), ('first_car', 'What was your first car?'), ('childhood_street', 'What street did you grow up on?')], default='pet_name', max_length=20),
        ),
    ]
