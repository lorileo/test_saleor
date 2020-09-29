#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
    os.environ.setdefault("SENDGRID_USERNAME", "mytinplate@163.com")
    os.environ.setdefault("SENDGRID_PASSWORD", "QTYEAWHIPLADFQNS")
    os.environ.setdefault("SECRET_KEY", "chuenshuen")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
