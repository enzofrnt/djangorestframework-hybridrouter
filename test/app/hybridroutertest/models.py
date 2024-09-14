from django.db import models

class Auto(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
# Create a model view set