#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """基本配置参数"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'thisishardto guess..'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    ZHIHU_MAIL_SUBJECT_PREFIX = u'【知乎】'
    ZHIHU_MAIL_SENDER = 'Zhihu Admin <nju_0913@163.com>'
    ZHIHU_ADMIN = os.environ.get('ZHIHU_ADMIN')
    ZHIHU_SLOW_DB_QUERY_TIME = 0.5


    @staticmethod
    def init_app(self):
        pass

class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'develop.sqlite')

class Production(Config):

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'produce.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.ZHIHU_MAIL_SENDER,
            toaddrs=[cls.ZHIHU_ADMIN],
            subject=cls.ZHIHU_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

class Testing(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'testing.sqlite')
    WTF_CSRF_ENABLED = False

class HerokuConfig(Production):
    @classmethod
    def init_app(cls, app):
        Production.init_app(app)

        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

config = {
    'development': Development,
    'production': Production,
    'testing': Testing,
    'heroku': HerokuConfig,
    'default': Development
}
