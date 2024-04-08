from flask import request
from flask import Flask,flash,redirect,url_for,make_response,session
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as db
from sqlalchemy import create_engine
from flask import render_template
from sqlalchemy import or_,and_
from flask_login import login_user, logout_user, login_required, current_user
from flask_login import UserMixin
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = "abc" 
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db=SQLAlchemy()
db.init_app(app)
app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.home"

@login_manager.user_loader
def load_user(id):
    record =None
    if 'user_type' in session:
        if session["user_type"] == "user":
           record = LoginDetails.query.get(int(id))
        if session["user_type"] == "admin":
            record = LoginDetails.query.get(int(id))
        return record

class PlayersList(db.Model):
    __tablename__='playerslist'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String)
    role=db.Column(db.String)
    nationality=db.Column(db.String)
    points=db.Column(db.Integer)
    base_prize=db.Column(db.Integer)
    status=db.Column(db.Integer)

class Team(db.Model):
    __tablename__='team'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String)
    stored_players=db.relationship('Teamlist',backref='team',cascade="all,delete")
    purse=db.Column(db.Integer, default=100)

class Teamlist(db.Model):
    __tablename__='teamlist'
    id=db.Column(db.Integer,primary_key=True)
    pid=db.Column(db.Integer,db.ForeignKey('playerslist.id',ondelete="CASCADE"))
    tid=db.Column(db.Integer,db.ForeignKey('team.id',ondelete="CASCADE"))
    amount=db.Column(db.Integer)
    points=db.Column(db.Integer)

class LoginDetails(db.Model,UserMixin):
    __tablename__='LoginDetails'
    id=db.Column(db.Integer,primary_key=True)
    uname=db.Column(db.String)
    pwd=db.Column(db.String)
    tid=db.Column(db.Integer,db.ForeignKey('team.id',ondelete="CASCADE"))
   

engine= create_engine("sqlite:///database.db")
db.create_all()


@login_required
@app.route("/admin0", methods=["GET", "POST"])
def home():
    player=PlayersList.query.filter(PlayersList.status==0).first()
    teams=Team.query.all()
    teamlists=Teamlist.query.all()
    return render_template("index.html",teams=teams,player=player,entry=False,teamlists=teamlists)

@app.route("/",methods=['GET','POST'])
def apphome():
    return render_template("home.html")

@app.route("/login", methods=['GET','POST'])
def login():
    if request.method=="POST":
        uname=request.form.get("uname")
        pwd=request.form.get("pwd")
        login_as=request.form.get("type")
        user=LoginDetails.query.filter(LoginDetails.uname==uname).first()
        if user:
            if login_as=="Admin":
                if uname=='admin' and pwd=='admin123':
                    session['user_type'] = 'admin'
                    session['user_type'] = 'admin'
                    login_user(user, remember=True)
                    return redirect(url_for('home'))
                
            if login_as=='Team':
                if user.pwd==pwd:
                    session['user_type'] = 'user'
                    login_user(user, remember=True)
                    return redirect(url_for('team'))
    return [uname,pwd,login_as]

@login_required
@app.route("/team",methods=['GET','POST'])
def team():
    user=current_user
    Teamplayer=PlayersList.query.filter(and_(user.tid==Teamlist.tid ,Teamlist.pid==PlayersList.id)).all()
    team_del=Team.query.filter(user.tid==Team.id).one()
    teamlists=Teamlist.query.filter(and_(user.tid==Teamlist.tid ,Teamlist.pid==PlayersList.id)).all()
    
    return render_template('team.html',myteamplayers=Teamplayer,teamdetails=team_del,teamlists=teamlists)

@login_required
@app.route("/admin", methods=["get","post"])
def admin():
    if request.method=="POST":
        player=PlayersList.query.filter(PlayersList.status==0).first()
        teams=Team.query.all()
        teamlists=Teamlist.query.all()
        teamlists=teamlists[:-1]
        team=request.form.get("team")
        final=request.form.get("submit")
        unsold=request.form.get("unsold")
        if team:
            teamlist=Teamlist.query.filter(Teamlist.pid==player.id).first()
            curteam=Team.query.filter(Team.name==team).one()
            if not teamlist:
                new_entry=Teamlist(tid=curteam.id,pid=player.id,amount=player.base_prize,points=player.points)
                db.session.add(new_entry)
                db.session.commit()
                teamlists=Teamlist.query.all()
                teamlists=teamlists[:-1]
            else:
                
                if teamlist.amount<8:
                    teamlist.amount=teamlist.amount+0.25
                else:
                    teamlist.amount=teamlist.amount+0.5
                teamlist.pid=player.id
                teamlist.tid=curteam.id
                db.session.commit()
                teamlists=Teamlist.query.all()
                teamlists=teamlists[:-1]
            return render_template("index.html",teams=teams,player=player,teamlist=teamlist,entry=True,curteam=curteam,teamlists=teamlists)
        if final:
            
            teamlist=Teamlist.query.filter(Teamlist.pid==player.id).first()
            curteam=Team.query.filter(Team.id==teamlist.tid).one()
            player.status=1
            curteam.purse=curteam.purse-teamlist.amount
            db.session.commit()
            return redirect(url_for('home'))
        if unsold:
            player.status=-1
            db.session.commit()
            return redirect(url_for('home'))
        
    return render_template("home.html")
    
    


if __name__ == '__main__':
  app.run(host='0.0.0.0',debug=True)
