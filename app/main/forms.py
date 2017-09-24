#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, \
    SelectField, SelectMultipleField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Length
from wtforms import ValidationError
from ..models import User, Topic, Question
from flask_pagedown.fields import PageDownField

class EditProfileForm(FlaskForm):
    username = StringField(u'用户名')
    gender = RadioField(u'性别', choices=[('Male', u'男'), ('Female', u'女')])
    description = StringField(u'一句话介绍')
    location = StringField(u'居住地')
    profession = StringField(u'所在行业')
    working_experience = TextAreaField(u'职业经历')
    education_experience = TextAreaField(u'教育经历')
    about_me = TextAreaField(u'个人简介')
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_username(self, field):
        if field.data != self.user.username and \
            User.query.filter_by(username=field.data).first():
            raise ValidationError(u'该用户名已存在')

class AddTopicForm(FlaskForm):
    name = StringField(u'话题名称', validators=[DataRequired(), Length(1, 64)])
    description = TextAreaField(u'话题描述', validators=[DataRequired()])
    submit = SubmitField(u'提交')

    def validate_name(self, field):
        if Topic.query.filter_by(name=field.data).first():
            raise ValidationError(u'话题已存在！')

class AskingForm(FlaskForm):
    title = StringField(u'问题标题', validators=[DataRequired()])
    topics = SelectMultipleField(u'添加话题-可以多选（ctrl）', coerce=int, validators=[DataRequired()])
    body = TextAreaField(u'问题描述,可选')
    submit = SubmitField(u'提交问题')

    def __init__(self, *args, **kwargs):
        super(AskingForm, self).__init__(*args, **kwargs)
        self.topics.choices = [(topic.id, topic.name)
                               for topic in Topic.query.order_by(Topic.name).all()]

    def validate_title(self,field):
        if Question.query.filter_by(title=field.data).first():
            raise ValidationError(u'该问题已存在！')

class AnswerForm(FlaskForm):
    body = PageDownField(u'写回答--Markdown编辑器', validators=[DataRequired()])
    submit = SubmitField(u'提交答案')

class CommentForm(FlaskForm):
    body = TextAreaField(u'评论', validators=[DataRequired()])
    submit = SubmitField(u'评论')

