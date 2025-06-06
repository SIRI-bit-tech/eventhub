# Generated by Django 4.2.7 on 2025-05-23 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_fix_invalid_image_uuids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='category',
            field=models.CharField(choices=[('conference', 'Conference'), ('workshop', 'Workshop'), ('meetup', 'Meetup'), ('social', 'Social'), ('sports', 'Sports'), ('arts', 'Arts & Culture'), ('business', 'Business'), ('education', 'Education'), ('technology', 'Technology'), ('health', 'Health & Wellness'), ('other', 'Other')], default='other', max_length=20),
        ),
    ]
