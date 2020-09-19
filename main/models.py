from django.db import models
from django.contrib.auth.models import User
import uuid, datetime
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.models import F


class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    duration = models.DurationField(default=datetime.timedelta())
    margin_before = models.DurationField(default=datetime.timedelta())
    margin_after = models.DurationField(default=datetime.timedelta())

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        username = self.owner.username
        return reverse('events', kwargs={'username': username})


class Invitation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)


class Schedule(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=datetime.datetime.now())
    notes = models.TextField(blank=True)

    @property
    def end_time(self):
        end_time = self.start_time + self.event.duration
        return end_time

    def __str__(self):
        return self.event.title

    def get_absolute_url(self):
        username = self.event.owner.username
        year = f'{self.start_time.year:04d}'
        month = f'{self.start_time.month:02d}'
        day = f'{self.start_time.day:02d}'
        return reverse('schedule', kwargs={'username': username, 'year': year, 'month': month, 'day': day})

    def clean(self):
        cleaned_data = super().clean()
        start = self.start_time
        end = self.end_time
        conflicting_events = Schedule.objects.filter(start_time__lt=end, start_time__gt=start-F('event__duration'))
        if conflicting_events.exists():
            raise ValidationError('Events overlap in time!')
        return cleaned_data
