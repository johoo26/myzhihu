#!/usr/bin/env python
# -*- coding:utf-8 -*-

import unittest
import time
from datetime import datetime
from app import create_app, db
from app.models import User, Role, Permission, Follow, Topic, Question, \
    Answer, Like

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_get(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            p = u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u1 = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u1.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirm_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirm_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirm_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_password(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_password_token()
        self.assertTrue(u.confirm_reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_invalid_reset_password(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_reset_password_token()
        self.assertFalse(u2.confirm_reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_valid_change_email(self):
        u = User(email='abc@example.com')
        db.session.add(u)
        db.session.commit()
        token = u.generate_change_email('hello@example.org')
        self.assertTrue(u.confirm_change_email(token))
        self.assertTrue(u.email == 'hello@example.org')

    def test_invalid_email_change(self):
        u1 = User(email='john@163.com')
        u2 = User(email='jack@qq.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_change_email('kevin@gmail.com')
        self.assertFalse(u2.confirm_change_email(token))
        self.assertTrue(u1.email=='john@163.com')

    def test_invalid_duplicate_change_email(self):
        u1 = User(email='john@163.com')
        u2 = User(email='jack@qq.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_change_email('jack@qq.com')
        self.assertFalse(u1.confirm_change_email(token))
        self.assertTrue(u1.email=='john@163.com')

    def test_roles_permissions(self):
        u = User(email='xyz@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_follow_users(self):
        u1 = User(email='cat@example.com', password='cat')
        u2 = User(email='dog@jd.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followedby(u2))
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followedby(u1))
        self.assertFalse(u2.is_following(u1))
        self.assertFalse(u1.is_followedby(u2))
        u2.follow(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertTrue(u1.is_followedby(u2))
        self.assertTrue(u2.is_following(u1))
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_followedby(u1))

    def test_gravatar(self):
        u = User(email='john@example.com', password='cat')
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar_256 = u.gravatar(size=256)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')
        with self.app.test_request_context('/', base_url='https://example.com'):
            gravatar_ssl = u.gravatar()
        self.assertTrue('http://www.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6'in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)
        self.assertTrue('https://secure.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6' in gravatar_ssl)

    def test_follow_topic(self):
        u = User(email='john@gmail.com', password='cat')
        topic = Topic(name='history')
        db.session.add(u)
        db.session.add(topic)
        db.session.commit()
        self.assertFalse(u.is_following_topic(topic))
        self.assertFalse(u in topic.followers)
        u.follow_topic(topic)
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.is_following_topic(topic))
        self.assertTrue(u in topic.followers)
        u.unfollow_topic(topic)
        db.session.add(u)
        db.session.commit()
        self.assertFalse(u.is_following_topic(topic))
        self.assertFalse(u in topic.followers)

    def test_follow_question(self):
        u = User(email='john@gmail.com', password='cat')
        topic = Topic(name='history')
        question = Question(title='how are you?')
        question.topics.append(topic)
        db.session.add(u)
        db.session.add(topic)
        db.session.add(question)
        db.session.commit()
        self.assertFalse(u.is_following_question(question))
        self.assertFalse(u in question.followers)
        u.follow_question(question)
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.is_following_question(question))
        self.assertTrue(u in question.followers)
        u.unfollow_question(question)
        db.session.add(u)
        db.session.commit()
        self.assertFalse(u.is_following_question(question))
        self.assertFalse(u in question.followers)


