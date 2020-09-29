# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-27 13:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("product", "0032_auto_20170216_0438")]

    operations = [
        migrations.AlterModelOptions(
            name="productattribute",
            options={
                "ordering": ("slug",),
                "verbose_name": "product attribute",
                "verbose_name_plural": "product attributes",
            },
        ),
        migrations.RenameField(
            model_name="attributechoicevalue", old_name="display", new_name="name"
        ),
        migrations.RenameField(
            model_name="productattribute", old_name="name", new_name="slug"
        ),
        migrations.RenameField(
            model_name="productattribute", old_name="display", new_name="name"
        ),
        migrations.AlterUniqueTogether(
            name="attributechoicevalue", unique_together=set([("name", "attribute")])
        ),
    ]
