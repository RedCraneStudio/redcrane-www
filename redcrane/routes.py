#!/usr/bin/env python

from flask import Flask, Blueprint, render_template, redirect, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
import bbcode, bcrypt, base64, re

from models import Post, User, Draft
from app import app, cache

# PREFIXES --------------------------------------->
# view_ = base view
# submit_ = submit
# form_ = form

url = Blueprint('url', __name__)
parser = bbcode.Parser(replace_links=False)
parser.add_simple_formatter('img', '<img src="%(value)s"></img>')
parser.add_simple_formatter('yt', '<iframe width="560" height="315" src="https://www.youtube.com/embed/%(value)s" frameborder="1" allowfullscreen></iframe>')

# REQUEST HANDLERS  ------------------------------>

@url.before_request
def before_request():
    g.user = current_user
    # variables to determine if hidden blog button
    # r_ prefix is to prevent overwriting 
    r_posts = Post.objects.all()

    try: r_drafts = Draft.objects(author=g.user[0])
    except: r_drafts = None

    g.blog_hidden = False if r_drafts or r_posts else True

# TEMPLATES -------------------------------------->

@cache.cached(timeout=50)
@url.route('/')
@url.route('/index/')
def index():
    posts = Post.objects.all().order_by('-created_at')[:5]
    return render_template('index.html', posts=posts)

@cache.cached(timeout=250)
@url.route('/about/')
def about():
    return render_template('about.html')

@url.route('/blog/')
@url.route('/blog/<int:page>/')
def blog(page=None):
    if page == None: page = 1

    try: drafts = Draft.objects(author=g.user[0])
    except: drafts = None

    posts = Post.objects.order_by('-created_at').paginate(page=page, per_page=5)

    return render_template('blog.html',
        posts=posts,
        drafts=drafts
    )

# BLOG POSTS ------------------------------------->

@url.route('/blog/search', methods=['GET'])
def search(query=None):
    results = []
    query = request.args.get('q')
    posts = Post.objects.all()

    for post in posts:
        query = re.sub("[^\w]", " ",  query).split()
        for word in query:
            if word.lower() in post.title.lower():
                results.append(post)

    return render_template('blog.html', search_results=results, query=query[0])

@cache.cached(timeout=250)
@url.route('/blog/post/<int:post_id>/')
def post(post_id=None):
    try:
        post = Post.objects.get_or_404(id=post_id)
    except:
        return redirect('/blog')

    post.body = parser.format(post.body)

    return render_template('post.html', post=post)

@url.route('/blog/post/remove/<int:post_id>/')
@login_required
def remove_post(post_id=None):
    post = Post.objects.get_or_404(id=post_id)
    post.delete()

    app.logger.debug('Deleted post - %s by %s' % (post.title, post.author))
    return redirect('/blog')

@url.route('/blog/post/edit/<int:post_id>/')
@login_required
def edit_post(post_id=None):
    post = Post.objects.get_or_404(id=post_id)
    post.id = post_id

    app.logger.debug('Edited post - %s by %s on %s' % (post.title, post.author,
    post.created_at))
    return render_template('submit.html', edit=True, post=post)

@url.route('/submit/')
@login_required
def form_post():
    return render_template('submit.html')

@url.route('/submit/post/', methods=['POST'])
@url.route('/submit/post/<int:post_id>/', methods=['POST'])
@login_required
def submit_post(post_id=None):
    try:
        post = Post(
                id = len(Post.objects.all())+1,
                title = request.form['title'],
                body = request.form['body'],
                author = g.user[0]
            )
        if post_id:
            previous_post = Post.objects.get_or_404(id=post_id)
            post.id = previous_post.id
    except Exception as error:
        return render_template('submit.html', error=error)

    app.logger.debug('New post - %s by %s' % (post.title, post.author))
    post.save()
    return redirect('/blog/')

# DRAFTS ----------------------------------------->

@url.route('/blog/draft/remove/<string:draft_id>/')
@login_required
def remove_draft(draft_id=None):
    draft = Draft.objects(id=draft_id)[0]
    if draft.author == g.user[0]:
        draft.delete()
        app.logger.debug('Deleted draft - %s by %s' % (draft.title, draft.author))

    return redirect('/blog')

@url.route('/blog/draft/edit/<string:draft_id>/')
def edit_draft(draft_id=None):
    draft = Draft.objects(id=draft_id)[0]
    if draft.author == g.user[0]:
        app.logger.debug('Edited draft - %s by %s on %s' % (draft.title,
        draft.author, draft.created_at))

        return render_template('submit.html',
            is_draft=True,
            draft=draft
        )
    return redirect('/blog/')

@url.route('/submit/draft/', methods=['POST'])
@url.route('/submit/draft/<string:draft_id>/', methods=['POST'])
@login_required
def submit_draft(draft_id=None):
    try:
        draft = Draft(
            title = request.form['title'],
            body = request.form['body'],
            author = g.user[0]
        )
        if draft_id:
            draft.id = draft_id
    except Exception as error:
        return render_template('submit.html', error=error)

    app.logger.debug('New draft - %s by %s' % (draft.title, draft.author))
    draft.save()
    return redirect('/blog/')

# AUTH ------------------------------------------->

def validate(user, raw_password):
    raw_password = raw_password.encode('base64', 'strict')
    user.password = user.password[7:]
    user.password = base64.b64decode(user.password)

    hash = bcrypt.hashpw(raw_password, bcrypt.gensalt(12))

    if bcrypt.hashpw(raw_password, user.password) == user.password:
        return True
    else:
        return False

@url.route('/auth/', methods=['POST'])
def auth():
    if g.user.is_authenticated == True:
        return redirect('/')

    for user in User.objects.all():
        if user.username == request.form['username']:
            if validate(user, request.form['password']):
                login_user(user)
                return redirect('/')
            else:
                return render_template('index.html', login_err='Incorrect password.')
    return render_template('index.html', login_err='Username does not exist!')

@url.route('/admin/')
def login():
    return render_template('login.html')

@url.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/')
