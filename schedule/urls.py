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
from django.contrib import admin
from django.urls import path, include, re_path
from main.views import SignUp, Home, ScheduleView, EventView, CalendarRedirectView, CalendarView, \
    ScheduleCreate, EventCreate



urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/registration', SignUp.as_view(), name='signup'),
    re_path(r'^(?P<username>[\-\.\w]+)/events', EventView.as_view(), name='events'),
    re_path(r'^(?P<username>[\-\.\w]+)/$', CalendarRedirectView.as_view(), name='calendar_redirect'),
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})$',
        CalendarView.as_view(),
        name='calendar'
    ),
    re_path(
        r'^(?P<username>[\-\.\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})$',
        ScheduleView.as_view(),
        name='schedule'
    ),
    re_path(
        r'^(?P<username>[\-\.\w]+)/schedule_event',
        ScheduleCreate.as_view(),
        name='schedule_event'
    ),
    re_path(
        r'^(?P<username>[\-\.\w]+)/create_event',
        EventCreate.as_view(),
        name='create_event'
    ),
    path('', Home.as_view(), name='home'),
]
