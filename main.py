from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date
import win32api

app = Flask(__name__)
app.secret_key = "sociopact-123"
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///sociopact.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CreatePostForm(FlaskForm):
    title = StringField("Task Title:", validators=[DataRequired()])
    body = CKEditorField("Task Content:", validators=[DataRequired()])
    submit = SubmitField("Submit Task")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=False, nullable=False)
    password = db.Column(db.String(250), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=False, nullable=False)
    address = db.Column(db.String(100), unique=False, nullable=False) 
    level = db.Column(db.Integer, unique=False, nullable=True)
    totalpoints = db.Column(db.Integer, unique=False, nullable=True)
    helped = db.Column(db.Integer, unique=False, nullable=True)
    completed = db.Column(db.String(950), nullable=True)
    tocomplete = db.Column(db.String(950), nullable=True)
    ratings = db.Column(db.String(950), nullable=True)
    volunteered = db.Column(db.String(950), nullable=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=False, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    response = db.Column(db.Integer, unique=False, nullable=True)
    archived = db.Column(db.Integer, unique=False, nullable=True)
    people = db.Column(db.String(950), nullable=False)
    accepted = db.Column(db.String(950), nullable=False)
    doneby = db.Column(db.String(950), nullable=False)
    donebydate = db.Column(db.String(250), nullable=True)
    





with app.app_context():
    db.create_all()

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        dup = False
        for x in User.query.all():
            if x.email==email: 
                dup = True
        if not dup:
            new_user = User(username=request.form["username"],
                            password=request.form["password"],
                            email = request.form["email"],
                            address = request.form["neighborhoods"],
                            level=1,
                            totalpoints=0,
                            helped=0,
                            completed='',
                            tocomplete='',
                            ratings='',
                            volunteered=''
                                            )
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))
        else:
            win32api.MessageBox(0, 'You have already signed up with this email. Try logging in instead', 'Duplicate Email',4096)
    return render_template("signup.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        selected = request.form["username"]
        userpass = request.form["password"]
        myuser = User.query.filter_by(email=selected).first()

        if not myuser or myuser.password!=userpass:
            win32api.MessageBox(0, 'Incorrect username or password', 'Error',4096)
            
        else:

            session['username'] = myuser.username
            session['level'] = myuser.level
            session['totalpoints'] = myuser.totalpoints
            session['helped'] = myuser.helped
            

            return redirect(url_for("index"))
    return render_template("login.html")

@app.route('/')
def notuser():
    return render_template("notuser.html")

@app.route('/index')
def index():
    current = User.query.filter_by(username=session.get('username', None)).first()
    d = {}
    if current.tocomplete!='':
        mylist = current.tocomplete.split('+')
        for x in mylist:
            if x!='':
                post = BlogPost.query.filter_by(title=x).first()
                d[x] = [post.author,User.query.filter_by(username=post.author).first().email,post.id]
                

    d2 = {}
    if current.completed!='':
        mylist = current.completed.split('+')
        for x in mylist:
            if x!='':
                post = BlogPost.query.filter_by(title=x).first()
                d2[x]=post.author
    d3 = {}
    if current.volunteered!='':
        mylist = current.volunteered.split('+')
        for x in mylist:
            if x!='':
                post = BlogPost.query.filter_by(title=x).first()
                d3[x]=[post.author,post.archived,post.doneby,post.id]

    return render_template("index.html",
                           user=current.username,
                           level=current.level,
                           totalpoints=current.totalpoints,
                           completed = d2,
                           tocomplete = d,
                           volunteeredfor = d3
                           )

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
    person.volunteered+=volunteering.title+'+'
    if person.username not in volunteering.people:
        volunteering.response+=1
        volunteering.people+=person.username+' '
        db.session.commit()
    return redirect(url_for('tasks'))



@app.route("/unarchive/<int:post_id>")
def unarchive(post_id):
    unarchive = BlogPost.query.filter_by(id=post_id).first()
    unarchive.archived = 0
    db.session.commit()
    return redirect(url_for('myposts'))

@app.route('/rating/<name>/<title>', methods=["GET", "POST"])
def rating(name,title):
    if request.method == "POST":
        num = int(request.form.get("stars"))
        helper = User.query.filter_by(username=name).first()
        helper.ratings+=str(num)+' '
        helper.totalpoints+=num*2
        helper.helped+=1

        post = BlogPost.query.filter_by(title=title).first()
        post.doneby=helper.username
        post.archived=1
        post.donebydate = date.today().strftime("%B %d, %Y")
        mylist = post.accepted.split()
        myindex = mylist.index(helper.username)
        mylist.pop(myindex)
        post.accepted = ' '.join(mylist)

        mylist = helper.tocomplete.split('+')
        myindex = mylist.index(title)
        popped = mylist.pop(myindex)
        helper.tocomplete = '+'.join(mylist)

        helper.completed+=popped+'+'

        db.session.commit()
        return redirect(url_for('myposts'))
    return render_template("rating.html",name=name, title=title)

@app.route('/complete/<person>/<title>')
def complete(person,title):
    user = User.query.filter_by(username=person).first()
    user.completed.append(title)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/accepted/<title>/<person>')
def accepted(title,person):
    myuser = User.query.filter_by(username=person).first()
    post = BlogPost.query.filter_by(title=title).first()
    mylist = post.people.split()
    myindex = mylist.index(person)
    one = mylist.pop(myindex)
    post.people = ' '.join(mylist)
    post.response-=1
    post.accepted += one+' '
    myuser.tocomplete+=title+'+'
    db.session.commit()
    return redirect(url_for('myposts'))

@app.route('/deny/<title>/<person>')
def deny(title,person):
    post = BlogPost.query.filter_by(title=title).first()
    mylist = post.people.split()
    myindex = mylist.index(person)
    mylist.pop(myindex)
    post.people = ' '.join(mylist)
    post.response-=1
    db.session.commit()
    return redirect(url_for('myposts'))


@app.route("/about")
def about():
    current = User.query.filter_by(username=session.get('username', None)).first()
    if current.totalpoints>=100:
        current.level+=1
        current.totalpoints-=100
    avg=[]
    for i in current.ratings.split():
        avg.append(int(i))
    average = round(sum(avg)/len(avg),1) if avg!=[] else 0
    users = [x for x in User.query.all() if current.address==x.address]
    details=[]
    for x in users:
        details.append([x.username,(x.level-1)*100+x.totalpoints])
    details = sorted(details,key=lambda x:x[1])[::-1]
    leaderboard=True
    if len(details)<3:
        one,two,three = 0,0,0
        leaderboard=False
    if len(details)>=3:
        one,two,three = details[0],details[1],details[2]
    return render_template("about.html",
                           user=current.username,
                           level=current.level,
                           totalpoints=current.totalpoints,
                           helped = current.helped,
                           average=average,
                           one=one,
                           two=two,
                           three=three,
                           leaderboard=leaderboard

                           )


@app.route("/tasks")
def tasks():
    posts = BlogPost.query.all()
    current = User.query.filter_by(username=session.get('username', None)).first()
    return render_template("blog.html", all_posts=posts[::-1], now=current.username,now2=current.address)


@app.route("/myposts")
def myposts():
    current = User.query.filter_by(username=session.get('username', None)).first()
    posts = BlogPost.query.all()
    details = {}
    people_details = {}
    accept = {}
    avg = []
    for x in posts:
        everyone = x.people.split()
        details[x.title] = everyone
        for selected in everyone:
            myuser = User.query.filter_by(username=selected).first()
            level,points = myuser.level,myuser.totalpoints
            for i in myuser.ratings.split():
                avg.append(int(i))
            average = round(sum(avg)/len(avg),1) if avg!=[] else 0
            people_details[selected] = [level,points,average]
            
        accept[x.title]=x.accepted
    return render_template("myposts.html", all_posts=posts, now=current.username, details=details, everyone=people_details, clicked=accept)

@app.route("/new-post", methods=["GET", "POST"])
def new_post():
    current = User.query.filter_by(username=session.get('username', None)).first()
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            body=form.body.data,
            author=current.username,
            date=date.today().strftime("%B %d, %Y"),
            address=current.address,
            response = 0,
            archived = 0,
            people = '',
            accepted = '',
            doneby='',
            donebydate = ''
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("tasks"))
    return render_template("add.html", form=form)

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.body = edit_form.body.data    
        db.session.commit()
        return redirect(url_for("myposts"))
    return render_template("add.html", form=edit_form, is_edit=True)

@app.route("/onepost/<int:post_id>/<ishome>")
def onepost(post_id,ishome):
    print(ishome)
    post = BlogPost.query.get(post_id)
    return render_template("onepost.html",post=post,ishome=ishome)

if __name__ == "__main__":
    app.run(debug=True)

