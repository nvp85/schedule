from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ValidationError
from django.views.generic.edit import CreateView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import F
from datetime import date
from datetime import datetime, timedelta
import calendar
from main.utils import make_utc
import pytz
from .models import Schedule, Event


class Home(TemplateView):
    template_name = 'home.html'


class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


class EventView(ListView):
    template_name = 'events.html'
    context_object_name = 'event_list'

    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)


class CalendarRedirectView(RedirectView):
    is_permanent = True

    def get_redirect_url(self, *args, **kwargs):
        now = timezone.now()
        year = f'{now.year:04d}'
        month = f'{now.month:02d}'
        return reverse_lazy('calendar', kwargs=dict(username=kwargs['username'], year=year, month=month))


class CalendarView(TemplateView):
    template_name = "calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, username=kwargs['username'])
        context['user'] = user
        context['calendar'] = calendar.Calendar(firstweekday=6).itermonthdays2(int(kwargs['year']), int(kwargs['month']))
        context['month_name'] = calendar.month_name[int(kwargs['month'])]
        return context


class ScheduleView(ListView):
    template_name = 'schedule.html'
    context_object_name = 'schedule_list'

    def get_queryset(self):
        day = date(int(self.kwargs['year']), int(self.kwargs['month']), int(self.kwargs['day']))
        end_time = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        start_time = timezone.make_aware(datetime.combine(day, datetime.max.time()))
        q = Schedule.objects.filter(
            event__owner=get_object_or_404(User, username=self.kwargs['username']),
            start_time__gte=end_time - F('event__duration'),
            start_time__lte=start_time
        ).order_by('start_time')
        return q

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        day = date(int(self.kwargs['year']), int(self.kwargs['month']), int(self.kwargs['day']))
        context['date'] = day
        day_begins = make_utc(datetime.combine(day, datetime.min.time()))
        day_ends = make_utc(datetime.combine(day, datetime.max.time()))
        context['username'] = self.kwargs['username']
        time_delta = timedelta(seconds=1800) # 30 min
        context['time_delta'] = time_delta
        context['time_list'] = [day_begins + i * time_delta for i in range(48)]
        q = context['schedule_list']
        context['schedule_dict'] = {}
        for event in q:
            begin = max(
                timezone.make_aware(
                    datetime(
                        year=event.start_time.year,
                        month=event.start_time.month,
                        day=event.start_time.day,
                        hour=event.start_time.hour
                    ),
                    timezone=pytz.utc
                ),
                day_begins
            )
            delta = timedelta(
                minutes=event.start_time.minute,
                seconds=event.start_time.second,
                microseconds=event.start_time.microsecond
            )
            if delta >= timedelta(minutes=30):
                begin = begin + timedelta(minutes=30)
            current = begin
            while min(event.end_time, day_ends) > current:
                context['schedule_dict'][current] = event.event.title
                current = current + timedelta(minutes=30)
        return context


class ScheduleCreate(CreateView):
    model = Schedule
    fields = ['event', 'start_time', 'notes']
    template_name = 'schedule_event.html'


class EventCreate(CreateView):
    model = Event
    fields = ['title', 'duration']
    template_name = 'event_template.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

