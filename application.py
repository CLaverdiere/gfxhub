import os
import sqlite3

from flask import Flask, Response, abort, flash, g, redirect, render_template, request, session, url_for 
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image

# TODO DB helper functions. One connection.
# TODO borked on heroku.

# App settings
app = Flask(__name__)
app.config.update(dict(
    ADMIN = False,
    ALLOWED_EXT = ('png', 'jpg', 'jpeg', 'gif'),
    DATABASE = os.path.join(app.root_path, 'graphics.db'),
    DEBUG = False,
    PASS = 'admin',
    THUMBNAIL_SIZE = (200, 200),
    UPLOAD_FOLDER = 'static/g_pics/',
    USER = 'admin'
))

if(os.path.isfile('settings.py')):
    app.config.from_object('settings')

# Authentication
def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_auth(user, passwd):
    return user == (app.config['USER'] or 'admin') and passwd == (app.config['PASS'] or 'admin')


# Routes.
@app.route("/")
def gfxhub(name=None):
    db = get_db()

    cur = db.execute('select count(*) as total_rows from graphics')
    total_pics = cur.fetchone()['total_rows']

    cur = db.execute('select sum(views) as total_views from graphics')
    total_views = cur.fetchone()['total_views']

    stats = {'total_pics' : total_pics, 'total_views' : total_views}
    return render_template('home.html', name=name, stats=stats)

# Route to informational about page.
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin')
@requires_auth
def admin():
    app.config['ADMIN'] = True
    return render_template('admin.html')

# Route to the most starred graphics.
@app.route("/g/best")
def show_best_graphics(pics=None, num_shown=5):
    db = get_db()

    cur = db.execute('select * from graphics order by starred desc limit ' + str(num_shown))
    pics = cur.fetchall()

    return render_template('best.html', pics=pics)

# Route for users to contribute an image to the collection.
@app.route('/contribute', methods=['GET', 'POST'])
def contribute(categories=None):
    db = get_db()
    cur = db.execute('select distinct category from graphics order by category desc');
    categories = [row['category'] for row in cur.fetchall()]
    if request.method == 'POST':
        category = request.form['category-picker'] or 'misc'
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], category, filename))
            db.execute('insert into graphics (title, category) values (?, ?)',
                        [filename, category])
            db.commit()
            gen_thumbnails()
            flash("Successfully uploaded graphic. Thanks!")
            return redirect('/g/' + category + '/' + filename)
        else:
            flash("That filetype isn't supported. Please use one of: " + " ".join(app.config['ALLOWED_EXT']))
    return render_template('contribute.html', categories=categories)

# Route to a overview/gallery of graphics page.
@app.route('/gallery')
def gallery(num_shown=10):
    db = get_db()

    pics, labels = dict(), dict()
    orderings = {'created_at' : ['recent', 'Most Recent'], 
                 'starred' : ['best', 'Highest Rated'],
                 'views' : ['popular', 'Most Viewed']}

    for order in orderings:
        alias = orderings[order][0]
        desc = orderings[order][1]

        cur = db.execute('select * from graphics order by {} desc limit {}'.format(order, num_shown))
        pics[alias] = cur.fetchall()
        labels[alias] = desc

    return render_template('gallery.html', pics=pics, labels=labels, num_shown=num_shown)

# Route to show all categories of images.
@app.route('/g/')
def show_graphic_category_list():
    db = get_db()
    cur = db.execute('select distinct category from graphics order by category desc');
    categories = cur.fetchall()
    return render_template('category_list.html', categories=categories)

# Route to list all pictures belonging to a given image category.
@app.route('/g/<category>/')
def show_graphic_list(category=None):
    db = get_db()
    cur = db.execute('select title, category from graphics where category=?', [category])
    pics = cur.fetchall()
    return render_template('graphics_list.html', pics=pics)

# Route for a specific image in the collection.
@app.route('/g/<category>/<pic_name>', methods=['GET', 'POST', 'DELETE'])
def show_graphic(category=None, pic_name=None):
    db = get_db()

    cur = db.execute('select * from graphics where title=? and category=?', [pic_name, category])
    pic = cur.fetchone()

    # Increment starred count on POST.
    if request.method == 'POST':
        if request.form['delete']:
            db.execute('delete from graphics where id=?', [pic['id']])
            db.commit()
            flash("Successfully deleted graphic " + pic_name)
            return render_template('admin.html')

        # FIXME: crashes here.
        elif request.form['star']:
            db.execute('update graphics set starred = starred + 1 where title=? and category=?', [pic_name, category])
            db.commit()

    # We want to retrieve our routed image, as well as alphabetically adjacent images.
    cur = db.execute('select * from graphics where category=?', [category])
    pics = cur.fetchall()

    # Find adjacent pictures by id order.
    prevpics = filter(lambda p: p['id'] < pic['id'], pics)
    nextpics = filter(lambda p: p['id'] > pic['id'], pics)

    prevpic = prevpics[-1] if prevpics else None
    nextpic = nextpics[0] if nextpics else None

    adjacent_pics = {'prev' : prevpic, 'next': nextpic}

    # Increment the view counter for the image.
    db.execute('update graphics set views = views + 1 where title=? and category=?', [pic_name, category])
    db.commit()

    return render_template('graphic.html', category=category, pic=pic, adjacent_pics=adjacent_pics)

# Route to the most viewed graphics.
@app.route("/g/popular")
def show_popular_graphics(num_shown=5):
    db = get_db()
    cur = db.execute('select * from graphics order by views desc limit ' + str(num_shown))
    pics = cur.fetchall()
    return render_template('popular.html', pics=pics)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


# Helper functions, some taken from official docs.
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXT']

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Generate 200x200 thumbnails for faster loading of pictures.
# Called on each image upload.
def gen_thumbnails():
    for root, dirs, files in os.walk(app.config["UPLOAD_FOLDER"]):
        for file in files:
            filename = root + '/' + file
            if not os.path.isfile(filename + '.thumb') and file.endswith(app.config['ALLOWED_EXT']):
                print("converting {} to thumbnail.".format(file))
                image = Image.open(filename)
                image.thumbnail(app.config['THUMBNAIL_SIZE'], Image.ANTIALIAS)
                image.save(filename + '.thumb', 'png')

if __name__ == "__main__":
    app.run()
