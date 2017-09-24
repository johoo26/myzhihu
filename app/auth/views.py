#!/usr/bin/env python
# -*- coding:utf-8 -*-

from . import auth
from .. import db
from flask import render_template, redirect, flash, url_for, request, g
from flask_login import logout_user, login_user, login_required, current_user
from .forms import RegisterForm, LoginForm, ChangePasswordForm, \
    ResetPasswordRequestForm, ResetPasswordForm, ChangeEmailForm, SearchForm
from ..models import User, Topic
from ..emails import send_mail

@auth.before_app_request
def before():
    if current_user.is_authenticated:
        if not current_user.confirmed and request.endpoint \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

    g.search_form = SearchForm()


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/resend-confirmation')
def resend_confirmation():
    token = current_user.generate_confirm_token()
    send_mail(current_user.email, u'确认您的账户', 'auth/email/confirm',
              user=current_user, token=token)
    flash(u'已重新发送确认信到您邮箱,请留意查收！')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    '注册视图函数，注册成功后重定向到登录页面'
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username = form.username.data, email=form.email.data,
                    password = form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirm_token()
        send_mail(user.email, u'确认您的账户', 'auth/email/confirm', user=user, token=token)
        flash(u'一封确认账户的邮件已发送到您的邮箱，请留意查收！')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(u'账户确认成功，您可以开始尽情使用了')
    else:
        flash(u'账户确认失败！')
    return redirect(url_for('main.index'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    '登录视图函数，登录成功后重定向到首页，否则显示登录失败信息'
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash(u'用户名或密码错误')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'您已退出')
    return redirect(url_for('auth.login'))

@auth.route('/settings')
@login_required
def setting():
    split_email = current_user.email.split('@')
    email = split_email[0][:2] + '******@' + split_email[1]
    return render_template('setting.html', email=email)

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            flash(u'密码已成功更改')
            return redirect(url_for('auth.setting'))
        else:
            flash(u'原密码输入不正确！')
    return render_template('auth/change_password.html', form=form)

@auth.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash(u'账号不存在！')
            return redirect(url_for('auth.reset_password_request'))
        token = user.generate_reset_password_token()
        send_mail(user.email, u'重设密码', 'auth/email/reset_password',
                  user=user, token=token)
        flash(u'已发送一封修改密码的邮件给你，请查收')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash(u'账号不存在！')
            return redirect(url_for('auth.reset_password', token=token))
        if user.confirm_reset_password(token, form.password.data):
            flash(u'密码更改成功')
        else:
            flash(u'密码重设失败！')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset-email-request', methods=['GET', 'POST'])
@login_required
def reset_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.password.data):
            flash(u'密码不正确！')
            return redirect(url_for('auth.reset_email_request'))
        token = current_user.generate_change_email(email=form.email.data)
        send_mail(form.email.data, u'更改邮箱地址', 'auth/email/change_email',
                  user=current_user, token=token)
        flash(u'已经发送一封邮件到新邮箱，请查收')
        return redirect(url_for('auth.setting'))
    return render_template('auth/change_email.html', form=form)

@auth.route('/reset-email/<token>')
@login_required
def change_email(token):
    if current_user.confirm_change_email(token):
        flash(u'邮箱地址更改成功')
    else:
        flash(u'更改邮箱失败！')
    return redirect(url_for('auth.setting'))