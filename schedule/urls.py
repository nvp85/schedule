"""schedule URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.contrib import admin
from django.urls import path, include, re_path
from main.views import SignUp, Home, ScheduleView, EventView, CalendarRedirectView, CalendarView, \
    ScheduleCreate, EventCreate, EventDelete, EventUpdate, InvitationCreate, ScheduleAsGuest, ScheduleAsGuestSuccess,\
    SetTimezoneGuestView, SetTimezoneView


urlpatterns = [
    path('admin/', admin.site.urls),
    # Authorization
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/registration', SignUp.as_view(), name='signup'),

    # choosing timezone
    re_path(
        r'^timezone$',
        SetTimezoneView.as_view(),
        name='set_timezone'
    ),

    # Schedule as a guest with an invitation link
    re_path(
        r'^invite/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12})$',
        CalendarRedirectView.as_view(),
        name='guest_calendar_redirect'
    ),

    # choosing timezone link for a guest
    re_path(
        r'^invite/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12})/timezone$',
        SetTimezoneGuestView.as_view(),
        name='set_timezone_guest'
    ),

    re_path(
        r'^invite/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12})/'
        r'(?P<year>[0-9]{4})/(?P<month>[0-9]{2})$',
        CalendarView.as_view(),
        name='guest_calendar'
    ),

    re_path(
        r'^invite/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12})/'
        r'(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})$',
        ScheduleView.as_view(),
        name='schedule_as_guest'
    ),

    re_path(
        r'^invite/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12})/'
        r'(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<time>[0-5][0-9]:[0-5][0-9])$',
        ScheduleAsGuest.as_view(),
        name='schedule_as_guest_form'
    ),

    re_path(
        r'^invite/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12})/success$',
        ScheduleAsGuestSuccess.as_view(),
        name='schedule_as_guest_success'
    ),

    # Calendar view
    re_path(r'^(?P<username>[\-\.\w]+)/$', CalendarRedirectView.as_view(), name='calendar_redirect'),
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})$',
        CalendarView.as_view(),
        name='calendar'
    ),

    # List of scheduled events
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})$',
        ScheduleView.as_view(),
        name='schedule'
    ),

    # List of Events
    re_path(r'^(?P<username>[\-\.\w]+)/events$', EventView.as_view(), name='events'),

    # Creating a new Event
    re_path(
        r'^(?P<username>[\-\.\w]+)/create_event$',
        EventCreate.as_view(),
        name='create_event'
    ),

    # Schedule an Event without prepopulated fields
    re_path(
        r'^(?P<username>[\-\.\w]+)/schedule_event$',
        ScheduleCreate.as_view(),
        name='schedule_event'
    ),
    re_path(
        r'^(?P<username>[\-\.\w]+)/schedule_event/'
        r'(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<time>[0-5][0-9]:[0-5][0-9])$',
        ScheduleCreate.as_view(),
        name='schedule_event_form'
    ),

    # Individual Event edit/delete/schedule/create an Invitation link
    # Delete an Event
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<event_slug>[\-\.\w]+)/delete$',
        EventDelete.as_view(),
        name='event_delete'
    ),

    # Update an Event
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<event_slug>[\-\.\w]+)/update$',
        EventUpdate.as_view(),
        name='event_update'
    ),

    # Schedule an Event from event list
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<event_slug>[\-\.\w]+)$',
        CalendarRedirectView.as_view(),
        name='event_calendar_redirect'),
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<event_slug>[\-\.\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})$',
        ScheduleView.as_view(),
        name='event_schedule'
    ),
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<event_slug>[\-\.\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})$',
        CalendarView.as_view(),
        name="event_calendar"
    ),
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<event_slug>[\-\.\w]+)/'
        r'(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<time>[0-5][0-9]:[0-5][0-9])$',
        ScheduleCreate.as_view(),
        name='event_schedule_form'
    ),

    # Create an invitation link
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<event_slug>[\-\.\w]+)/create_invites$',
        InvitationCreate.as_view(),
        name='invitation_create'
    ),



    path('', Home.as_view(), name='home'),
    path('__debug__/', include(debug_toolbar.urls)),
]
