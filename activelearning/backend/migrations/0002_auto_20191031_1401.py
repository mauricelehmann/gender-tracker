# Generated by Django 2.2.5 on 2019-10-31 14:01

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.IntegerField()),
                ('labels', django.contrib.postgres.fields.jsonb.JSONField()),
                ('sentence_index', models.IntegerField()),
                ('author_index', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
        ),
        migrations.RenameModel(
            old_name='Articles',
            new_name='Article',
        ),
        migrations.DeleteModel(
            name='UserLabels',
        ),
        migrations.AddField(
            model_name='userlabel',
            name='article',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Article'),
        ),
    ]
