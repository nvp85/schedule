from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ValidationError
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import F
from datetime import date
from datetime import datetime, timedelta
import calendar
import pytz
from .models import Schedule, Event, Invitation
from main.utils import make_utc, get_invite_or_403


class TestOwnershipMixin(UserPassesTestMixin):

    def test_func(self):
        username = self.kwargs.get('username')
        uuid = self.kwargs.get('uuid')
        if username:
            if self.request.user.is_authenticated and self.request.user.username == self.kwargs.get("username"):
                return True
        elif uuid:
            return True
        return False


class Home(TemplateView):
    template_name = 'home.html'


class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


class EventView(LoginRequiredMixin, ListView):
    template_name = 'events.html'
    context_object_name = 'event_list'

    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)


class CalendarRedirectView(TestOwnershipMixin, RedirectView):
    is_permanent = True

    def get_redirect_url(self, *args, **kwargs):
        now = timezone.now()
        year = f'{now.year:04d}'
        month = f'{now.month:02d}'
        if kwargs.get('event_slug'):
            return reverse_lazy('event_calendar',
                                kwargs=dict(username=kwargs['username'], event_slug=kwargs['event_slug'], year=year,
                                            month=month))
        if kwargs.get('uuid'):
            invite = get_invite_or_403(kwargs['uuid'])
            return reverse_lazy('guest_calendar',
                                kwargs=dict(uuid=kwargs['uuid'], year=year, month=month))
        return reverse_lazy('calendar', kwargs=dict(username=kwargs['username'], year=year, month=month))


class CalendarView(TestOwnershipMixin, TemplateView):
    template_name = "calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs.get('username'):
            user = get_object_or_404(User, username=kwargs['username'])
            context['user'] = user
            context['event_slug'] = kwargs.get('event_slug')
        if kwargs.get('uuid'):
            context['invite'] = get_invite_or_403(kwargs['uuid'])
        context['calendar'] = calendar.Calendar(firstweekday=6).itermonthdays2(int(kwargs['year']), int(kwargs['month']))
        context['month_name'] = calendar.month_name[int(kwargs['month'])]
        return context


class ScheduleView(TestOwnershipMixin, ListView):
    template_name = 'schedule.html'
    context_object_name = 'schedule_list'

    def get_queryset(self):
        day = date(int(self.kwargs['year']), int(self.kwargs['month']), int(self.kwargs['day']))
        end_time = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        start_time = timezone.make_aware(datetime.combine(day, datetime.max.time()))
        q = []
        if self.kwargs.get('uuid'):
            invite = get_invite_or_403(self.kwargs['uuid'])
            q = Schedule.objects.filter(
                event__owner=invite.event.owner,
                start_time__gte=end_time - F('event__duration'),
                start_time__lte=start_time
            ).order_by('start_time')
        elif self.kwargs.get('username'):
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
        if self.kwargs.get("username"):
            context['username'] = self.kwargs['username']
            context['event_slug'] = self.kwargs.get('event_slug')
        elif self.kwargs.get('uuid'):
            context['invite'] = get_object_or_404(Invitation, uuid=self.kwargs['uuid'])
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


class ScheduleCreate(LoginRequiredMixin, TestOwnershipMixin, CreateView):
    model = Schedule
    fields = ['event', 'start_time', 'notes']
    template_name = 'schedule_event.html'

    def get_initial(self):
        initial = super().get_initial()
        if self.kwargs.get('year'):
            year = int(self.kwargs.get('year'))
            month = int(self.kwargs.get('month'))
            day = int(self.kwargs.get('day'))
            hours, minutes = map(int, self.kwargs.get('time').split(':'))
            initial['start_time'] = datetime(
                year=year,
                month=month,
                day=day,
                hour=hours,
                minute=minutes
            )
        slug = self.kwargs.get('event_slug')
        if slug:
            initial['event'] = get_object_or_404(Event, slug=slug)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['event'].queryset = Event.objects.filter(owner=self.request.user)
        return context


class EventCreate(LoginRequiredMixin, TestOwnershipMixin, CreateView):
    model = Event
    fields = ['title', 'duration']
    template_name = 'event_template.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class GetEventMixin:

    def get_queryset(self):
        owner = self.request.user
        q = Event.objects.filter(owner=owner)
        return q

    def get_object(self, queryset=None):
        slug = self.kwargs.get('event_slug')
        if not queryset:
            queryset = self.get_queryset()
        obj = get_object_or_404(queryset, slug=slug)
        return obj

    def get_success_url(self):
        return reverse_lazy('events', kwargs=dict(username=self.request.user.username))


class EventDelete(LoginRequiredMixin, GetEventMixin, TestOwnershipMixin, DeleteView):
    model = Event
    template_name = 'event_delete.html'


class EventUpdate(LoginRequiredMixin, GetEventMixin, TestOwnershipMixin, UpdateView):
    model = Event
    fields = ['title', 'duration']
    template_name = 'event_template.html'


class InvitationCreate(LoginRequiredMixin, TestOwnershipMixin, CreateView):
    model = Invitation
    fields = ['max_number_of_uses', 'expiration_time']
    template_name = 'invitation_create.html'

    def get_event(self):
        slug = self.kwargs.get('event_slug')
        event = get_object_or_404(Event, slug=slug)
        return event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_event()
        context['list_of_links'] = Invitation.objects.filter(event__owner=self.request.user, event=event)
        context["event"] = event
        return context

    def form_valid(self, form):
        form.instance.event = self.get_event()
        return super().form_valid(form)


class ScheduleAsGuest(CreateView):
    model = Schedule
    fields = ['notes',]
    template_name = 'schedule_event.html'

    def get_invitation(self):
        uuid = self.kwargs.get("uuid")
        invite = get_invite_or_403(uuid)
        return invite

    def get_start_time(self):
        year = int(self.kwargs.get('year'))
        month = int(self.kwargs.get('month'))
        day = int(self.kwargs.get('day'))
        hours, minutes = map(int, self.kwargs.get('time').split(':'))
        return datetime(year=year, month=month, day=day, hour=hours, minute=minutes)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uuid = self.kwargs.get("uuid")
        event = self.get_invitation().event
        context['event'] = event
        context['user'] = event.owner
        context['uuid'] = uuid
        context['start_time'] = self.get_start_time()
        return context

    def get_form(self, form_class=None):
        form = super().get_form()
        form.instance.event = self.get_invitation().event
        return form

    def form_valid(self, form):
        form.instance.start_time = self.get_start_time()
        invite = self.get_invitation()
        invite.get_used()
        form.instance.invite_used = invite
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("schedule_as_guest_success", kwargs=dict(uuid=self.object.uuid))


class ScheduleAsGuestSuccess(TemplateView):
    template_name = 'schedule_as_guest_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['scheduled_event'] = get_object_or_404(Schedule, uuid=kwargs.get('uuid'))
        return context


