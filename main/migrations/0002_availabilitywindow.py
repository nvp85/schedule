# Generated by Django 4.1.7 on 2023-08-14 05:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailabilityWindow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_day', models.CharField(choices=[('Mo', 'Monday'), ('Tu', 'Tuesday'), ('We', 'Wednesday'), ('Th', 'Thursday'), ('Fr', 'Friday'), ('Sa', 'Saturday'), ('Su', 'Sunday')], max_length=2)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True))
            ],
        ),
    ]