from NewsApp import app
from newspaper import Article
from flask import render_template, request, flash, session, url_for, redirect, jsonify
from forms import SignupForm, SigninForm
from models import db, User
import time
import praw
from functools import wraps
import itertools
from random import shuffle

 
app.secret_key = 'development key'

class RedditPost():
    def __init__(self, post):
        self.reddit_title = post.title
        self.url = post.url

        # use newspaper module to download article information
        # article = Article(url=post.url)
        # article.download()
        # article.parse()

        # self.article_title = article.title
        # self.image = article.top_image


class ArticlePost():
    def __init__(self, url):
        article = Article(url=url)
        article.download()
        article.parse()

        self.title = article.title
        self.image = article.top_image
        self.text = article.text


def login_required(f):
    @wraps(f)
    def new_f(*args):
        if 'email' not in session:
            return redirect(url_for('signin'))
        else:
            return f(*args)
    return new_f



def get_useragent():
    return praw.Reddit(user_agent='Alien News/1.0 by ellbosch')


def get_reddit_posts(subreddit, n):
    subreddit_posts = get_useragent().get_subreddit(subreddit).get_hot(limit=n)
    posts = []
    for p in subreddit_posts:
        post = RedditPost(p)
        posts.append(post)

    return posts


def random_subreddit():
    subr = ""
    subreddits = ['worldnews', 'science', 'technology', 'news']
    shuffle(subreddits)

    for s in itertools.islice(subreddits, 1):
        subr = s
    return subr


@app.route('/')
def homepage():
    sub = random_subreddit()
    posts = get_reddit_posts(sub, 10)

    article = ArticlePost(posts[0].url)

    return render_template('index.html', post_list=posts, article=article) 


@app.route('/article/')
def show_article():
    url = str(request.args['url'])

    article = ArticlePost(url)

    return jsonify(result = {"title": article.title,
                             "text": article.text})


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
  
    if 'email' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        if form.validate() == False:
            return render_template('signup.html', form=form)
        else:
            newuser = User(form.firstname.data, form.lastname.data, form.email.data, form.password.data)
            db.session.add(newuser)
            db.session.commit()

            session['email'] = newuser.email
            return redirect(url_for('profile'))
   
    elif request.method == 'GET':
        return render_template('signup.html', form=form)


@app.route('/profile')
@login_required
def profile():
    if 'email' not in session:
        return redirect(url_for('signin'))
    
    user = User.query.filter_by(email = session['email']).first()
 
    if user is None:
        return redirect(url_for('signin'))
    else:
        return render_template('profile.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
  
    if 'email' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        if form.validate() == False:
            return render_template('signin.html', form=form)
        else:
            session['email'] = form.email.data
            return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template('signin.html', form=form)


@app.route('/signout')
@login_required
def signout():
     
    session.pop('email', None)
    return redirect(url_for('signin'))

