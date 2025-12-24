from django.db import models
from django.contrib.auth.models import User

class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review')
    evaluation = models.IntegerField()
    feedback = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False, verbose_name="Опубликовано")

    def __str__(self):
        return f"Отзыв от {self.author.username} ({self.evaluation}/10)"
