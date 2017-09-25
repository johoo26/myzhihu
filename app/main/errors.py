#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import render_template
from . import main


@main.app_errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@main.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403
