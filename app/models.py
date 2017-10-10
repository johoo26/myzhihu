#!/usr/bin/env python
# -*- coding:utf-8 -*-
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from . import db, login_manager, whooshee
from flask_login import UserMixin, current_user, AnonymousUserMixin
from flask import request, current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import hashlib, forgery_py
from random import seed, randint
from sqlalchemy.exc import IntegrityError
from markdown import markdown
import bleach


class Permission(object):
    """用户权限"""
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80

class Follow(db.Model):
    """关注用户/被关注用户 表格"""
    __tablename__  = 'follows'

    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)

#问题/关注问题的用户表格
questions_users = db.Table('questions_users',
                    db.Column('question_id', db.Integer, db.ForeignKey('questions.id')),
                    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')))

class Question(db.Model):
    """问题表格。每个问题可能关联多个话题，有多个关注者，有多个回答。"""
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), unique=True)
    body = db.Column(db.Text())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
    followers = db.relationship('User',
                                secondary=questions_users,
                                backref=db.backref('questions_following', lazy='dynamic'),
                                lazy='dynamic')
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

    #生成大量虚拟问题
    @staticmethod
    def generate_fake(count=500):

        seed()
        user_count = User.query.count()
        topic_count = Topic.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            q = Question(title=forgery_py.lorem_ipsum.title(),
                         body=forgery_py.lorem_ipsum.sentences(),
                         timestamp=forgery_py.date.date(True),
                         author=u)
            for i in range(randint(1,5)):
                topic = Topic.query.offset(randint(0, topic_count-1)).first()
                q.topics.append(topic)
            db.session.add(q)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()



class User(UserMixin, db.Model):
    """模型中最关键的，用户表格。"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean(), default=False)
    about_me = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    avatar_hash = db.Column(db.String(64))
    description = db.Column(db.String(128))
    location = db.Column(db.String(128))
    profession = db.Column(db.String(128))
    working_experience = db.Column(db.Text)
    education_experience = db.Column(db.Text)
    gender = db.Column(db.String(32))
    questions_asked = db.relationship('Question',backref='author', lazy='dynamic')
    answers = db.relationship('Answer', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')

    #用户作为关注方
    followings = db.relationship('Follow',
                                foreign_keys = [Follow.follower_id],
                                backref = db.backref('follower', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    #用户作为被关注方
    followers = db.relationship('Follow',
                                foreign_keys = [Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    #生成虚拟用户
    @staticmethod
    def generate_fake(count=100):

        seed()
        for i in range(count):
            u = User(username=forgery_py.internet.user_name(True),
                     email=forgery_py.internet.email_address(),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     description=forgery_py.lorem_ipsum.words(),
                     location=forgery_py.address.city(),
                     profession = forgery_py.lorem_ipsum.title(),
                     working_experience = forgery_py.lorem_ipsum.words(),
                     education_experience = forgery_py.lorem_ipsum.words(),
                     gender = forgery_py.personal.gender())
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    #构造方法。实例化用户时，设置用户角色和avatar_hash用于头像
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ZHIHU_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            else:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError( 'password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administer(self):
        return self.can(Permission.ADMINISTER)

    def is_following(self, user):
        return self.followings.filter_by(followed_id=user.id).first() is not None

    def is_followedby(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followings.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following_topic(self, topic):
        return topic in self.topics

    def follow_topic(self, topic):
        if not self.is_following_topic(topic):
            self.topics.append(topic)
            db.session.add(self)

    def unfollow_topic(self, topic):
        if self.is_following_topic(topic):
            self.topics.remove(topic)
            db.session.add(self)

    def is_following_question(self, question):
        return question in self.questions_following

    def follow_question(self, question):
        if not self.is_following_question(question):
            self.questions_following.append(question)
            db.session.add(self)

    def unfollow_question(self, question):
        if self.is_following_question(question):
            self.questions_following.remove(question)
            db.session.add(self)

    #用户在某一话题下的回答数量
    def answers_of_topic(self, topic):
        answer_counts = 0
        for answer in self.answers:
            if topic in answer.question.topics:
                answer_counts += 1
        return answer_counts

    #判断用户是否赞过回答
    def have_liked(self, answer):
        return answer.likes.filter_by(user_id=current_user.id).first() is not None

    #找出用户关注的全部话题下的所有回答并按照时间降序排列
    @property
    def answers_interested_topics(self):
        return db.session.query(Answer).join(Question).filter(
            Question.topics.any(Topic.followers.any(User.id ==
                    self.id))).order_by(Answer.timestamp.desc())

    #找出关注的所有人的回答并按时间降序排列
    @property
    def answers_followings(self):
        return Answer.query.join(Follow, Follow.followed_id == Answer.user_id).\
            filter(Follow.follower_id == self.id).order_by(Answer.timestamp.desc())

    #找出关注的所有人的赞同并按时间降序排列
    @property
    def likes_followings(self):
        return Like.query.join(Follow, Follow.followed_id == Like.user_id).\
            filter(Follow.follower_id == self.id).order_by(Like.timestamp.desc())

    #找出一用户所有的赞同并按时间降序排列
    @property
    def personal_likes(self):
        return Like.query.order_by(Like.timestamp.desc()).\
            filter(Like.user_id == self.id)

    #找出一用户所有的回答并按时间降序排列
    @property
    def personal_answers(self):
        return Answer.query.order_by(Answer.timestamp.desc()).\
            filter(Answer.user_id == self.id)

    #找出一用户所有提问并按时间降序排列
    @property
    def personal_questions_asked(self):
        return Question.query.order_by(Question.timestamp.desc()).\
            filter(Question.user_id == self.id)

    #为注册用户生产令牌
    def generate_confirm_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm':self.id})

    #验证注册用户的令牌
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_password_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset':self.id})

    def confirm_reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_change_email(self, email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change-email':self.id, 'email':email})

    def confirm_change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change-email') != self.id:
            return False
        new_email = data.get('email')
        if new_email is None:
            return False
        if User.query.filter_by(email=new_email).first():
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administer(self):
        return False

login_manager.anonymous_user = AnonymousUser


class Role(db.Model):
    """定义网站的用户角色，普通用户/协管员/管理员"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    permissions = db.Column(db.Integer)
    default = db.Column(db.Boolean, default=False, index=True)

    #把角色填充到roles表格
    @staticmethod
    def insert_roles():
        roles = {
            'User':(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES|
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role:{}>'.format(self.name)

#用户/话题表格，多对多关系
topics_users = db.Table('topics_users',
                db.Column('topic_id', db.Integer, db.ForeignKey('topics.id')),
                db.Column('user_id', db.Integer, db.ForeignKey('users.id')))

#话题/问题表格，多对多关系
topics_questions = db.Table('topics_questions',
                    db.Column('topic_id', db.Integer, db.ForeignKey('topics.id')),
                    db.Column('question_id', db.Integer, db.ForeignKey('questions.id')))


class Topic(db.Model):
    """话题模型。一个话题有多个关注的用户，多个问题"""
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    description = db.Column(db.Text())

    #话题关注者
    followers = db.relationship('User',
                          secondary=topics_users,
                          backref=db.backref('topics', lazy='dynamic'),
                          lazy='dynamic')

    #话题下的问题
    questions = db.relationship('Question',
                            secondary=topics_questions,
                            backref=db.backref('topics', lazy='dynamic'),
                            lazy='dynamic')

    #找出一个话题下所有的回答并按时间降序排列
    @property
    def all_answers(self):
        return db.session.query(Answer).join(Question).filter(
            Question.topics.any(Topic.id == self.id)).order_by(
            Answer.timestamp.desc())

    #生成大量虚拟话题
    @staticmethod
    def generate_fake(count=50):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            t = Topic(name=forgery_py.lorem_ipsum.word(),
                      description=forgery_py.lorem_ipsum.sentences())
            db.session.add(t)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

@whooshee.register_model('body')
class Answer(db.Model):
    """回答模型。一个回答从属于一个问题，一个作者。
    一个回答可能有多个赞同和评论。
    回答可以使用部分HTML格式"""
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.Text())
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='answer', lazy='dynamic')
    likes = db.relationship('Like', backref='answer', lazy='dynamic')
    likes_count = db.Column(db.Integer)
    body_html = db.Column(db.Text)

    #生成大量虚拟回答
    @staticmethod
    def generate_fake(count=2000):

        seed()
        user_count = User.query.count()
        question_count = Question.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            q = Question.query.offset(randint(0, question_count-1)).first()
            ans = Answer(body=forgery_py.lorem_ipsum.paragraph(),
                         timestamp=forgery_py.date.date(True),
                         author=u,
                         question=q)
            db.session.add(ans)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    #定义回答允许使用的标签
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i',  'li', 'ol', 'ul', 'pre', 'strong', 'h1',
                        'h2', 'h3', 'h4', 'p', 'br']
        target.body_html = bleach.linkify(bleach.clean(markdown(
            value, output_format = 'html'), tags=allowed_tags, strip=True))

#监听回答，一旦有新回答就调用on_changed_body函数
db.event.listen(Answer.body, 'set', Answer.on_changed_body)

class Comment(db.Model):
    """评论模型类"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
    body = db.Column(db.Text())
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    #生成虚拟评论
    @staticmethod
    def generate_fake(count=4000):

        seed()
        user_count = User.query.count()
        answer_count = Answer.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            ans = Answer.query.offset(randint(0, answer_count-1)).first()
            c = Comment(body=forgery_py.lorem_ipsum.paragraph(),
                        timestamp=forgery_py.date.date(True),
                        author=u,
                        answer=ans)
            db.session.add(c)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Like(db.Model):
    """赞同模型类，一个赞同从属于一个回答/一个作者"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    unread = db.Column(db.Boolean, default=True)

    @staticmethod
    def generate_fake(count=10000):

        seed()
        user_count = User.query.count()
        answer_count = Answer.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            ans = Answer.query.offset(randint(0, answer_count - 1)).first()
            count = ans.likes.count()
            like = Like(timestamp=forgery_py.date.date(True),
                        user=u,
                        answer=ans)
            db.session.add(like)

            ans.likes_count = count + 1
            db.session.add(ans)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    #判断是否为一周内的赞同
    def weekly(self):
        time_in_one_week = datetime.utcnow() - timedelta(days=7)
        return self.timestamp > time_in_one_week
