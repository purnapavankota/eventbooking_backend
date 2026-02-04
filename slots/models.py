from django.db import models
from django.contrib.auth.models import User


class EventCategory(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    booked_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.category.name} | {self.date}"
