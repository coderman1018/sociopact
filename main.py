from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date

app = Flask(__name__)
app.secret_key = "sociopact-123"
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///sociopact.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CreatePostForm(FlaskForm):
    title = StringField("Task Title:", validators=[DataRequired()])
    img_url = StringField("Task Image (URL):", validators=[DataRequired(), URL()])
    body = CKEditorField("Task Content:", validators=[DataRequired()])
    submit = SubmitField("Submit Task")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(100), unique=False, nullable=False) 
    level = db.Column(db.Integer, unique=False, nullable=True)
    totalpoints = db.Column(db.Integer, unique=False, nullable=True)
    helped = db.Column(db.Integer, unique=False, nullable=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=False, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(950), nullable=False)
    response = db.Column(db.Integer, unique=False, nullable=True)
    archived = db.Column(db.Integer, unique=False, nullable=True)
    people = db.Column(db.String(950), nullable=False)
    accepted = db.Column(db.String(950), nullable=False)





with app.app_context():
    db.create_all()

@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    deleting = BlogPost.query.filter_by(id=post_id).first()
    deleting.archived = 1
    db.session.commit()
    return redirect(url_for('myposts'))

@app.route("/volunteer/<int:post_id>")
def volunteer(post_id):
    volunteering = BlogPost.query.filter_by(id=post_id).first()
    person = User.query.filter_by(username=session.get('username', None)).first()
    if person.username not in volunteering.people:
        volunteering.response+=1
        volunteering.people+=person.username+' '
        db.session.commit()
    return redirect(url_for('blog'))


@app.route("/unarchive/<int:post_id>")
def unarchive(post_id):
    unarchive = BlogPost.query.filter_by(id=post_id).first()
    unarchive.archived = 0
    db.session.commit()
    return redirect(url_for('myposts'))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        selected = request.form["username"]
        myuser = User.query.filter_by(username=selected).first()

        if myuser:
            session['username'] = myuser.username
            session['level'] = myuser.level
            session['totalpoints'] = myuser.totalpoints
            session['helped'] = myuser.helped

            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        new_user = User(username=request.form["username"],
                        password=request.form["password"],
                        email = request.form["email"],
                        address = request.form["address"],
                        level=1,
                        totalpoints=0,
                        helped=0
                                        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route('/')
def notuser():
    return render_template("notuser.html")

@app.route('/index')
def index():
    current = User.query.filter_by(username=session.get('username', None)).first()
    return render_template("index.html",
                           user=current.username,
                           level=current.level,
                           totalpoints=current.totalpoints,
                           )

@app.route('/accepted/<title>/<person>')
def accepted(title,person):
    post = BlogPost.query.filter_by(title=title).first()
    mylist = post.people.split()
    myindex = mylist.index(person)
    one = mylist.pop(myindex)
    post.people = ' '.join(mylist)
    post.response-=1
    post.accepted += one+' '
    db.session.commit()
    return redirect(url_for('myposts'))

@app.route("/about")
def about():
    current = User.query.filter_by(username=session.get('username', None)).first()
    return render_template("about.html",
                           user=current.username,
                           level=current.level,
                           totalpoints=current.totalpoints,
                           helped = current.helped
                           )


@app.route("/blog")
def blog():
    posts = BlogPost.query.all()
    current = User.query.filter_by(username=session.get('username', None)).first()
    return render_template("blog.html", all_posts=posts, now=current.username)


@app.route("/myposts")
def myposts():
    current = User.query.filter_by(username=session.get('username', None)).first()
    posts = BlogPost.query.all()
    details = {}
    people_details = {}
    accept = {}
    for x in posts:
        everyone = x.people.split()
        details[x.title] = everyone
        for selected in everyone:
            myuser = User.query.filter_by(username=selected).first()
            level,points = myuser.level,myuser.totalpoints
            people_details[selected] = [level,points]
        accept[x.title]=x.accepted
    print(accept)
    return render_template("myposts.html", all_posts=posts, now=current.username, details=details, everyone=people_details, clicked=accept)

@app.route("/new-post", methods=["GET", "POST"])
def new_post():
    current = User.query.filter_by(username=session.get('username', None)).first()
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current.username,
            date=date.today().strftime("%B %d, %Y"),
            response = 0,
            archived = 0,
            people = '',
            accepted = ''
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("blog"))
    return render_template("add.html", form=form)

# @app.route("/helper/<name>")
# def helper(name):
#     person = User.query.filter_by(username=name).first()
#     lev,points = person.level,person.totalpoints
#     return (lev,points)


if __name__ == "__main__":
    app.run(debug=True)

