# schedule

## Introduction
This is an application for creating and managing a daily schedule. Also allows a user to create invitations for other people so they could book a meeting with the user.
An invitation is a link a user can create in their profile and send to another person, it will be generated using UUID. The person then will use the link to schedule a meeting with the user provided the link.    

## Technologies
Django 3.2+
Python 3.9
django-environ
pytz

## Launch
- Clone the repository
```
$ git clone https://github.com/nvp85/schedule
```
- Set up and activate virtual environment
```
$ python -m venv venv
$ . venv/Scripts/activate
```
- Install requirements.txt
```
$ pip install -r requirements.txt
```
- Create a role schedule_user 
```
postgres=# CREATE ROLE schedule_user;
```
- Create a database schedule_db, make the role schedule_user an owner of the database
```
postgres=# CREATE DATABASE schedule_db OWNER schedule_user;
```
- Generate a new django secret key
- Create a .env file (handled by django-environ) and put your postgres credentials and the django secret key into it
- Migrate
```
$ python manage.py migrate
```
- Run the development webserver
```
$ python manage.py runserver
```