# schedule

## Introduction
Application for creating and managing a daily schedule. Also allows a user to create invitations for other people so they could book a meeting with the user.
## General info

## Technologies
Django 3.2+
Python 3.9
django-environ
pytz

## Launch
- Clone repository
- Set up and activate virtual environment
- Install requirements.txt
- Create a database schedule_db
- Create a role schedule_user, make the role an owner of the database 
- Generate a new django secret key
- Create a .env file (handled by django-environ) and put your postgres credentials and the django secret key into it
- Make migrations
- Run the development webserver