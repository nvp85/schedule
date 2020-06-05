from django.db import models
from django.contrib.auth.models import User
import uuid, datetime


class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    duration = models.DurationField()
    margin_before = models.DurationField(default=datetime.timedelta())
    margin_after = models.DurationField(default=datetime.timedelta())


class Invitation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)


class Schedule(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    notes = models.TextField(blank=True)

    @property
    def end_time(self):
        end_time = self.start_time + self.event.duration
        return end_time
