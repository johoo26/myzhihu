#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, ValidationError, \
    BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from ..models import User

class RegisterForm(FlaskForm):
    username = StringField(u'用户名', validators=[DataRequired(), Length(1,32)])
    email = StringField(u'邮箱地址', validators=[DataRequired(), Email()])
    password = PasswordField(u'密码', validators=[DataRequired(), Length(1,32),
                            EqualTo('password2', message='password must match!')])
    password2 = PasswordField(u'验证密码', validators=[DataRequired()])
    submit = SubmitField(u'注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户名已存在')
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'该邮箱已存在')
    def validate_dnsname(self, field):
        if User.query.filter_by(dnsname=field.data).first():
            raise ValidationError(u'域名已被占用')

class LoginForm(FlaskForm):
    email = StringField(u'邮箱地址', validators=[DataRequired(), Length(1, 32), Email()])
    password = PasswordField(u'密码', validators=[DataRequired(), Length(1, 32)])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u'原密码', validators=[DataRequired()])
    new_password = PasswordField(u'新密码', validators=[DataRequired(),
                                    EqualTo('password2', message=u'密码前后不一致')])
    password2 = PasswordField(u'确认新密码', validators=[DataRequired()])
    submit = SubmitField(u'提交')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(u'邮件地址', validators=[DataRequired(), Email()])
    submit = SubmitField(u'提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'该账号不存在！')

class ResetPasswordForm(FlaskForm):
    email = StringField(u'邮件地址', validators=[DataRequired(), Email()])
    password = PasswordField(u'新密码', validators=[DataRequired(),
                                    EqualTo('password2', message=u'密码前后不一致')])
    password2 = PasswordField(u'确认新密码', validators=[DataRequired()])
    submit = SubmitField(u'提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'该账号不存在！')

class ChangeEmailForm(FlaskForm):
    email = StringField(u'新邮箱地址', validators=[DataRequired(), Email()])
    password = PasswordField(u'密码', validators=[DataRequired()])
    submit = SubmitField(u'更改邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮件已存在！')

class SearchForm(FlaskForm):
    search = StringField(u'搜索', validators=[DataRequired()])
