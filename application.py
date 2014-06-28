from flask import Flask, url_for, render_template
app = Flask(__name__)

@app.route("/")
def gfxhub(name=None):
    return render_template('application.html', name=name)

@app.route('/g/')
@app.route('/g/<n>')
def show_graphic(n=0):
    return render_template('graphics.html', n=n)

@app.route('/about')
def about(n):
    return "gfxhub is a place to share graphics."

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
    for i in range(1, 12):
        url_for('static', filename='raytraced_pics/s{}.png'.format(i))
