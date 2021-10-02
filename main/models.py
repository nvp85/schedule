from django.db import models
from django.contrib.auth.models import User
import uuid, datetime
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import F
from django.template.defaultfilters import slugify
from django.utils import timezone
from main.utils import make_utc


class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    duration = models.DurationField(default=datetime.timedelta())
    margin_before = models.DurationField(default=datetime.timedelta())
    margin_after = models.DurationField(default=datetime.timedelta())
    slug = models.SlugField(null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        username = self.owner.username
        return reverse('events', kwargs={'username': username})

    def generate_slug(self):
        new_slug = slugify(self.title)
        suffix = ''
        counter = 0
        while Event.objects.filter(owner=self.owner, slug=new_slug + suffix).exists():
            counter += 1
            suffix = f"-{counter}"
        self.slug = new_slug + suffix

    def save(self, *args, **kwargs):
        if not self.slug:
            self.generate_slug()
        super().save( *args, **kwargs)

    class Meta:
        unique_together = ['slug', 'owner']


class Invitation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    uses_counter = models.IntegerField(default=0)
    max_number_of_uses = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    expiration_time = models.DateTimeField(default=make_utc(timezone.now())+datetime.timedelta(days=7))

    def get_absolute_url(self):
        username = self.event.owner.username
        event_slug = self.event.slug
        return reverse('invitation_create', kwargs={'username': username, 'event_slug': event_slug})

    def get_used(self):
        self.uses_counter += 1
        self.save()

    @property
    def is_active(self):
        now = make_utc(datetime.datetime.now())
        if make_utc(self.expiration_time) > now and self.uses_counter < self.max_number_of_uses:
            return True
        return False


class Schedule(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=make_utc(timezone.now()))
    notes = models.TextField(blank=True)
    invite_used = models.ForeignKey(Invitation, null=True, default=None, editable=False, on_delete=models.SET_NULL)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

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
        conflicting_events = Schedule.objects.filter(
            start_time__lt=end,
            start_time__gt=start-F('event__duration'),
            event__owner=self.event.owner,
        )
        if conflicting_events.exists():
            raise ValidationError('Events overlap in time!')
        return cleaned_data
