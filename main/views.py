from typing import Any, Dict, Optional
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import ValidationError
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView, RedirectView, View
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
from main.utils import get_invite_or_403


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


class Home(RedirectView):
    permanent = False
    #template_name = 'home.html'

    def get_redirect_url(self, *args: Any, **kwargs: Any):
        if self.request.user.is_authenticated:
            now = timezone.now()
            year = f'{now.year:04d}'
            month = f'{now.month:02d}'
            day = f'{now.day:02d}'
            return reverse_lazy('schedule', kwargs=dict(username=self.request.user.username, year=year, month=month, day=day))
        return reverse_lazy('login')


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
    is_permanent = False

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
        month = int(kwargs['month'])
        year = int(kwargs['year'])
        context['calendar'] = calendar.Calendar(firstweekday=6).itermonthdays2(year, month)
        context['month_name'] = calendar.month_name[month]
        context['prev_month'] = f'{month-1:02d}' if month > 1 else '12'
        context['prev_year'] = f'{year:04d}' if month > 1 else f'{year-1:04d}'
        context['next_month'] = f'{month+1:02d}' if month < 12 else '01'
        context['next_year'] = f'{year:04d}' if month < 12 else f'{year+1:04d}'
        return context


class ScheduleView(TestOwnershipMixin, ListView):
    template_name = 'schedule.html'
    context_object_name = 'schedule_list'

    def get_queryset(self):
        day = date(int(self.kwargs['year']), int(self.kwargs['month']), int(self.kwargs['day']))
        # here timezone is current, from the session. transfer it to utc
        end_time = timezone.make_aware(datetime.combine(day, datetime.min.time())).astimezone(pytz.utc)
        start_time = timezone.make_aware(datetime.combine(day, datetime.max.time())).astimezone(pytz.utc)
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
        # this day is supposed to be in the current timezone, as user/guest chooses it
        context['date'] = day
        # current timezone to utc
        day_begins = timezone.make_aware(datetime.combine(day, datetime.min.time())).astimezone(pytz.utc)
        day_ends = timezone.make_aware(datetime.combine(day, datetime.max.time())).astimezone(pytz.utc)
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
            # max between event's start time and day's start time without minutes
            event_start_time = event.start_time.astimezone(pytz.utc)
            event_start_hour = timezone.make_aware(
                    datetime(
                        year=event_start_time.year,
                        month=event_start_time.month,
                        day=event_start_time.day,
                        hour=event_start_time.hour
                    ),
                    timezone=pytz.utc
                )
            begin = max(event_start_hour, day_begins)
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
            # this time in current user's tz
            initial['start_time'] = timezone.make_aware(datetime(
                year=year,
                month=month,
                day=day,
                hour=hours,
                minute=minutes
            ))
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
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


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
    

class InvitationListView(LoginRequiredMixin, ListView):
    model = Invitation
    context_object_name = 'invites_list'
    template_name = 'invitations_list.html'

    def get_queryset(self) -> QuerySet[Any]:
        return Invitation.objects.filter(event__owner=self.request.user, expiration_time__gte=timezone.now())


class ScheduleAsGuest(CreateView):
    model = Schedule
    fields = ['notes',]
    template_name = 'schedule_event.html'

    def get_invitation(self):
        uuid = self.kwargs.get("uuid")
        invite = get_invite_or_403(uuid)
        return invite

    def get_start_time(self):
        # in user's time zone
        year = int(self.kwargs.get('year'))
        month = int(self.kwargs.get('month'))
        day = int(self.kwargs.get('day'))
        hours, minutes = map(int, self.kwargs.get('time').split(':'))
        return timezone.make_aware(datetime(year=year, month=month, day=day, hour=hours, minute=minutes))

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
        form.instance.start_time = self.get_start_time()
        return form

    def form_valid(self, form):
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


class SetTimezoneGuestView(View):
    def get(self, request, **kwargs):
        context = {'timezones': pytz.common_timezones, 'uuid': kwargs.get('uuid')}
        return render(request, 'set_timezone.html', context)

    def post(self, request, **kwargs):
        request.session['django_timezone'] = request.POST['timezone']
        invite = get_invite_or_403(kwargs['uuid'])
        return redirect('guest_calendar_redirect', uuid=kwargs.get('uuid'))

class SetTimezoneView(View):
    def get(self, request, **kwargs):
        context = {'timezones': pytz.common_timezones}
        return render(request, 'set_timezone.html', context)

    def post(self, request, **kwargs):
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('home')