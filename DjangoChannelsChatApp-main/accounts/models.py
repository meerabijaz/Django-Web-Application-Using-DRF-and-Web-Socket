from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    SECURITY_QUESTIONS = [
        ('pet_name', 'What was the name of your first pet?'),
        ('birth_city', 'In which city were you born?'),
        ('favorite_color', 'What is your favorite color?'),
        ('mother_maiden', 'What is your mother\'s maiden name?'),
        ('first_car', 'What was your first car?'),
        ('childhood_street', 'What street did you grow up on?'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    security_question = models.CharField(max_length=20, choices=SECURITY_QUESTIONS, default='pet_name', blank=True)
    security_answer = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
