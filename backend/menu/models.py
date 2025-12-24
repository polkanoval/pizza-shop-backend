from django.db import models

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=6, decimal_places=0)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='menu_images/')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name