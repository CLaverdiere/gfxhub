import os, sqlite3
from flask import Flask, url_for, render_template, request, redirect, session, abort, flash, g
from werkzeug.utils import secure_filename

# TODO Bug: Stars / views get stuck at None. Make default values of 0.

# Globals
G_DIR = "static/g_pics/"
ALLOWED_EXT = set(['png', 'jpg', 'jpeg', 'gif'])


# App settings
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'graphics.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    UPLOAD_FOLDER = G_DIR
))
app.config.from_envvar('GRAPHICS_SETTINGS', silent=True)


# Routes.
@app.route("/")
def gfxhub(name=None):
    db = get_db()

    cur = db.execute('select count(*) as total_rows from graphics')
    total_pics = cur.fetchone()['total_rows']

    cur = db.execute('select sum(views) as total_views from graphics')
    total_views = cur.fetchone()['total_views']

    stats = {'total_pics' : total_pics, 'total_views' : total_views}
    return render_template('application.html', name=name, stats=stats)

# Route to informational about page.
@app.route('/about')
def about():
    return render_template('about.html')

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
            flash("Successfully uploaded graphic. Thanks!")
            return redirect('/g/' + category + '/' + filename)
        else:
            flash("That filetype isn't supported. Please use one of: " + " ".join(ALLOWED_EXT))
    return render_template('contribute.html', categories=categories)

# Route to a overview/gallery of graphics page.
@app.route('/gallery')
def gallery(num_shown = 5):
    db = get_db()

    cur = db.execute('select * from graphics order by starred desc limit ' + str(num_shown))
    best_pics = cur.fetchall()

    cur = db.execute('select * from graphics order by views desc limit ' + str(num_shown))
    popular_pics = cur.fetchall()

    cur = db.execute('select * from graphics order by created_at desc limit ' + str(num_shown))
    recent_pics = cur.fetchall()

    pics = {'best': best_pics, 'popular': popular_pics, 'recent': recent_pics}

    return render_template('gallery.html', pics=pics, num_shown=num_shown)

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
@app.route('/g/<category>/<pic_name>', methods=['GET', 'POST'])
def show_graphic(category=None, pic_name=None):
    db = get_db()

    # Increment starred count on POST.
    if request.method == 'POST':
        if request.form['star']:
            db.execute('update graphics set starred = starred + 1 where title=? and category=?', [pic_name, category])

    # We want to retrieve our routed image, as well as alphabetically adjacent images.
    cur = db.execute('select * from graphics where title=? and category=?', [pic_name, category])
    pic = cur.fetchone()

    prevcur = db.execute('select * from graphics where id=? and category=?', [pic['id'] - 1, category])
    nextcur = db.execute('select * from graphics where id=? and category=?', [pic['id'] + 1, category])

    prevpic = prevcur.fetchone()
    nextpic = nextcur.fetchone()

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


# Helper functions, most taken from official docs.
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXT

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

if __name__ == "__main__":
    app.run()
