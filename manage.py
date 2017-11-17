#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager, Shell
from app import create_app, db
from app.models import User, Role, Topic, Comment, Permission, \
    Question, Answer, Like, Follow

print '添加一行玩玩'
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

app = create_app(os.getenv('CONFIG_NAME') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_context_shell():
    return dict(app=app, db=db, User=User, Role=Role,Answer=Answer,Like=Like,Follow=Follow,
                Comment=Comment, Permission=Permission, Topic=Topic, Question=Question)
manager.add_command('shell', Shell(make_context=make_context_shell))
manager.add_command('db', MigrateCommand)

@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print ("Coverage Summary:")
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print ("HTML version: file://%s/index.html" % covdir)
        COV.erase()

@manager.command
def profile(length=25, profile_dir=None):
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()

@manager.command
def deploy():

    from flask_migrate import upgrade
    from app.models import Role

    upgrade()

    Role.insert_roles()


if __name__ == '__main__':
    manager.run()
