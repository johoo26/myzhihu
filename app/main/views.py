#!/usr/bin/env python
# -*-coding:utf-8 -*-

from flask import render_template, flash, redirect, url_for, abort, \
    make_response,request, current_app, g
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import login_manager, db
from ..models import User, Topic, Question, Answer, Comment, Permission, Like
from .forms import EditProfileForm, AddTopicForm, AskingForm, AnswerForm, \
    CommentForm
from ..decorators import permission_required, admin_required
from datetime import datetime, timedelta

question_views = 0

#请求结束时调用，把查询时间超过限定值的SQL语句记录日志
@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['ZHIHU_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response

#首页；根据cookies判断要看的内容和页数
@main.route('/')
@login_required
def index():
    choice = int(request.cookies.get('choice', '0'))
    page = int(request.cookies.get('page', '1'))
    if choice == 2:
        answers = []
        pagination = current_user.likes_followings.\
            paginate(page, per_page=10, error_out=False)
        likes = pagination.items
    elif choice == 1:
        pagination = current_user.answers_followings.\
            paginate(page, per_page=10, error_out=False)
        answers = pagination.items
        likes = []
    else:
        pagination = current_user.answers_interested_topics.\
            paginate(page, per_page=10, error_out=False)
        answers = pagination.items
        likes = []

    return render_template('index.html', answers=answers,
                    likes=likes,choice=choice, pagination=pagination)

@main.route('/answers-interested-topics')
@login_required
def show_answers_interested_topics():
    PageNum = request.args.get('page', 1, type=int)
    resp = make_response(redirect(url_for('.index',)))
    resp.set_cookie('choice', '0', max_age=30*24*60*60)
    resp.set_cookie('page', str(PageNum))
    return resp

@main.route('/answers-followings')
@login_required
def show_answers_followings():
    PageNum = request.args.get('page', 1, type=int)
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('choice', '1', max_age=30*24*60*60)
    resp.set_cookie('page', str(PageNum))
    return resp

@main.route('/likes-followings')
@login_required
def show_likes_followings():
    PageNum = request.args.get('page', 1, type=int)
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('choice', '2', max_age=30*24*60*60)
    resp.set_cookie('page', str(PageNum))
    return resp

#个人页面，默认为个人的点赞动态
@main.route('/people/<username>/activities')
@login_required
def profile(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    pagination = user.personal_likes.paginate(page, per_page=10, error_out=False)
    likes = pagination.items
    return render_template('main/profile_activities.html',
                           pagination=pagination,user=user, likes=likes)

#个人回答集合
@main.route('/people/<username>/answers')
@login_required
def people_answers(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    pagination = user.personal_answers.paginate(page, per_page=10, error_out=False)
    answers = pagination.items
    return render_template('main/profile_answers.html',
                           pagination=pagination,user=user, answers=answers)

#个人提问集合
@main.route('/people/<username>/asks')
@login_required
def people_asks(username):
    user = User.query.filter_by(username=username).first_or_404()
    asks = user.personal_questions_asked
    return render_template('main/profile_asks.html', user=user, asks=asks)

#关注的用户
@main.route('/people/<username>/followerings')
@login_required
def followings(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('main/followings.html', user=user)

#关注该用户的人
@main.route('/people/<username>/followers')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('main/followers.html', user=user)

#关注的话题
@main.route('/people/<username>/following/topics')
@login_required
def people_following_topics(username):
    user = User.query.filter_by(username=username).first_or_404()
    topics = user.topics
    return render_template('main/profile_topics.html', user=user, topics=topics)

#关注的问题
@main.route('/people/<username>/following/questions')
@login_required
def people_following_questions(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    pagination = user.questions_following.order_by(
        Question.timestamp.desc()).paginate(page, per_page=15, error_out=False)
    questions = pagination.items
    return render_template('main/profile_questions.html',
                pagination=pagination, user=user, questions=questions)

#编辑个人资料
@main.route('/people/edit', methods=['GET', 'POST'])
@login_required
def editprofile():
    form = EditProfileForm(current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.gender = form.gender.data
        current_user.description = form.description.data
        current_user.location = form.location.data
        current_user.profession = form.profession.data
        current_user.working_experience = form.working_experience.data
        current_user.education_experience = form.education_experience.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash(u'个人资料已更新')
        return redirect(url_for('main.profile', username=current_user.username))
    form.username.data = current_user.username
    form.gender.data = current_user.gender
    form.description.data = current_user.description
    form.location.data = current_user.location
    form.profession.data = current_user.profession
    form.working_experience.data = current_user.working_experience
    form.education_experience.data = current_user.education_experience
    form.about_me.data = current_user.about_me
    return render_template('main/editprofile.html', form=form)

#话题广场，包含网站所有话题
@main.route('/topics')
@login_required
def topic_square():
    topics = Topic.query.all()
    return render_template('topic_square.html', topics=topics)

#添加话题
@main.route('/addtopic', methods=['GET', 'POST'])
@login_required
def add_topic():
    form = AddTopicForm()
    if form.validate_on_submit():
        topic = Topic(name=form.name.data, description=form.description.data)
        db.session.add(topic)
        db.session.commit()
        flash(u'已成功添加话题')
        return redirect(url_for('main.topic_square'))
    return render_template('add_topic.html', form=form)

#话题的动态，按照最新时间排布话题的所有回答
@main.route('/topic/<int:id>/hot')
@login_required
def topic_dynamics(id):
    page = request.args.get('page',1,type=int)
    topic = Topic.query.get_or_404(id)
    pagination = topic.all_answers.paginate(page, per_page=10, error_out=False)
    answers = pagination.items
    return render_template('topic_dynamics.html',pagination=pagination,
                           answers=answers, topic=topic)

#话题下的所有问题
@main.route('/topic/<int:id>/unanswered')
@login_required
def topic_unanswered(id):
    page = request.args.get('page', 1, type=int)
    topic = Topic.query.get_or_404(id)
    pagination = topic.questions.paginate(page, per_page=20, error_out=False)
    questions = pagination.items
    return render_template('topic_unanswered.html', pagination=pagination,
                           questions=questions, topic=topic)

#话题的关注者
@main.route('/topic/<int:id>/followers')
@login_required
def topic_followers(id):
    topic = Topic.query.get_or_404(id)
    return render_template('topic_followers.html', topic=topic)

#提问
@main.route('/asking', methods=['GET', 'POST'])
@login_required
def asking():
    form = AskingForm()
    if not current_user.can(Permission.WRITE_ARTICLES):
        abort(403)
    if form.validate_on_submit():
        question = Question(title=form.title.data,
                    body=form.body.data,
                    author=current_user._get_current_object())
        for topic_id in form.topics.data:
            topic = Topic.query.get(topic_id)
            question.topics.append(topic)
        db.session.add(question)
        db.session.commit()
        flash(u'问题已成功提交')
        return redirect(url_for('main.question', id=question.id))
    return render_template('main/asking.html', form=form)

#单个问题的页面
@main.route('/question/<int:id>', methods=['GET', 'POST'])
@login_required
def question(id):
    form = AnswerForm()
    if not current_user.can(Permission.WRITE_ARTICLES):
        abort(403)
    question = Question.query.get_or_404(id)
    global question_views
    question_views += 1
    if form.validate_on_submit():
        answer = Answer(body=form.body.data,
                        question=question,
                        author=current_user._get_current_object())
        db.session.add(answer)
        db.session.commit()
        flash(u'成功提交回答')
        return redirect(url_for('main.question', id=question.id))

    return render_template('main/question.html', question=question,
                           form=form, question_views=question_views)

#单个回答的页面
@main.route('/question/<int:id_que>/answer/<int:id_ans>', methods=['GET', 'POST'])
@login_required
def answer(id_que, id_ans):
    form = CommentForm()
    if not current_user.can(Permission.WRITE_ARTICLES):
        abort(403)
    answer = Answer.query.get_or_404(id_ans)
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          answer=answer,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash(u'评论已发表～')
        return redirect(url_for('main.answer', id_que=answer.question.id, id_ans=answer.id))
    return render_template('main/answer.html', answer=answer, form=form)

#修改回答
@main.route('/answer/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_answer(id):
    answer = Answer.query.get_or_404(id)
    if current_user != answer.author and not current_user.can(Permission.WRITE_ARTICLES):
        abort(403)
    form = AnswerForm()
    if form.validate_on_submit():
        answer.body = form.body.data
        db.session.add(answer)
        db.session.commit()
        flash(u'已更新回答')
        return redirect(url_for('main.answer', id_que=answer.question.id, id_ans=answer.id))
    form.body.data = answer.body
    return render_template('main/edit_answer.html', form=form, answer=answer)

#删除回答
@main.route('/delete/answer/<int:id>')
@login_required
def delete_answer(id):
    answer = Answer.query.get_or_404(id)
    if current_user != answer.author and not current_user.can(Permission.WRITE_ARTICLES):
        abort(403)
    db.session.delete(answer)
    flash(u'已删除回答！')
    return redirect(url_for('main.question', id=answer.question.id))

#删除问题
@main.route('/delete/question/<int:id>')
@login_required
def delete_question(id):
    question = Question.query.get_or_404(id)
    if current_user != question.author and not current_user.can(Permission.WRITE_ARTICLES):
        abort(403)
    db.session.delete(question)
    flash(u'已删除问题！')
    return redirect(url_for('main.index'))

#关注其他用户
@main.route('/people/<username>/follow')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'用户不存在')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash(u'您已经关注过了')
        return redirect(url_for('main.profile', username=username))
    current_user.follow(user)
    return redirect(url_for('main.profile', username=username))

#取关用户
@main.route('/people/<username>/unfollow')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'用户不存在')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash(u'您并未关注{}'.format(username))
        return redirect(url_for('main.profile', username=username))
    current_user.unfollow(user)
    return redirect(url_for('main.profile', username=username))

#关注话题
@main.route('/topic/<int:id>/follow')
@login_required
@permission_required(Permission.FOLLOW)
def follow_topic(id):
    topic = Topic.query.get_or_404(id)
    if current_user.is_following_topic(topic):
        flash(u'您已经关注该话题')
        return redirect(url_for('main.topic_dynamics', id=topic.id))
    current_user.follow_topic(topic)
    return redirect(url_for('main.topic_dynamics', id=topic.id))

#取关话题
@main.route('/topic/<int:id>/unfollow')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow_topic(id):
    topic = Topic.query.get_or_404(id)
    if not current_user.is_following_topic(topic):
        flash(u'您未关注该话题')
        return redirect(url_for('main.topic_dynamics', id=topic.id))
    current_user.unfollow_topic(topic)
    return redirect(url_for('main.topic_dynamics', id=topic.id))

#关注问题
@main.route('/question/<int:id>/follow')
@login_required
@permission_required(Permission.FOLLOW)
def follow_question(id):
    question = Question.query.get_or_404(id)
    if current_user.is_following_question(question):
        flash(u'您已经关注了该问题')
        return redirect(url_for('main.question',id=question.id))
    current_user.follow_question(question)
    return redirect(url_for('main.question', id=question.id))

#某个问题的关注者
@main.route('/question/<int:id>/followers')
@login_required
def question_followers(id):
    question = Question.query.get_or_404(id)
    return render_template('main/question_followers.html', question=question)

#取关问题
@main.route('/question/<int:id>/unfollow')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow_question(id):
    question = Question.query.get_or_404(id)
    if not current_user.is_following_question(question):
        flash(u'您尚未关注该问题')
        return redirect(url_for('main.question', id=question.id))
    current_user.unfollow_question(question)
    return redirect(url_for('main.question', id=question.id))

#赞同回答
@main.route('/answer/<int:id>/like')
@login_required
@permission_required(Permission.COMMENT)
def like_answer(id):
    answer = Answer.query.get_or_404(id)
    count = answer.likes.count()
    like = Like(answer=answer, user=current_user._get_current_object())
    db.session.add(like)
    answer.likes_count = count + 1
    db.session.add(answer)
    return redirect(url_for('main.question', id=answer.question.id))

#取消赞同回答
@main.route('/answer/<int:id>/dislike')
@login_required
@permission_required(Permission.COMMENT)
def dislike_answer(id):
    answer = Answer.query.get_or_404(id)
    like = answer.likes.filter_by(user_id=current_user.id).first()
    if like:
        db.session.delete(like)
    return redirect(url_for('main.question', id=answer.question.id))

#显示每天最热的回答
@main.route('/explore/daily-hot')
@login_required
def daily_hot():
    page = request.args.get('page', 1, type=int)
    in_one_day = datetime.utcnow() - timedelta(days=1)
    pagination = Answer.query.filter(Answer.timestamp > in_one_day).filter(
        Answer.likes_count > 2).order_by(Answer.timestamp.desc()).\
        paginate(page, error_out=False)
    answers_daily_hot = pagination.items
    return render_template('main/daily_hot.html',
                           pagination=pagination,
                           answers_daily_hot=answers_daily_hot)

#显示每月最热回答
@main.route('/explore/monthly-hot')
@login_required
def monthly_hot():
    page = request.args.get('page', 1, type=int)
    in_a_month = datetime.utcnow() - timedelta(days=30)
    pagination = Answer.query.filter(Answer.timestamp > in_a_month).\
        filter(Answer.likes_count > 10).order_by(Answer.timestamp.desc()).\
        paginate(page, error_out=False)
    answers_monthly_hot = pagination.items
    return render_template('/main/monthly_hot.html',
                           pagination=pagination,
                           answers_monthly_hot=answers_monthly_hot)

#搜索回答
@main.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('main.index'))
    return redirect(url_for('main.search_results', query=g.search_form.search.data))

#搜索回答并按时间降序排列
@main.route('/search_results/<query>')
@login_required
def search_results(query):
    answers = Answer.query.filter(Answer.body.ilike("%{}%".format(query.encode('utf-8'))))\
        .order_by(Answer.timestamp.desc()).limit(30)
    return render_template('search.html', answers=answers, query=query)
