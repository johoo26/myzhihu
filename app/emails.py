#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_mail import Message
from flask import current_app, render_template
from . import mail
from threading import Thread

def send_asyn_mail(app, msg):
    with app.app_context():
        mail.send(msg)

def send_mail(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(current_app.config['ZHIHU_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=current_app.config['ZHIHU_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_asyn_mail, args=[app, msg])
    thr.start()
    return thr
