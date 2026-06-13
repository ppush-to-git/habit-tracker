import sqlite3
import os
from flask import Flask,request,render_template,redirect,session
from datetime import date,timedelta
import hashlib
habitpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.db")
conn=sqlite3.connect(habitpath)
curs=conn.cursor()
curs.execute(f"""
    CREATE TABLE IF NOT EXISTS habits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit TEXT,
    lastcompleted TEXT,
    streak INTEGER,
    uid INTEGER)
    """)
conn.commit()
conn.close()

userpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
conn=sqlite3.connect(userpath)
curs=conn.cursor()
curs.execute(f"""
    CREATE TABLE IF NOT EXISTS users(
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT)
    """)
conn.commit()
conn.close()
today=str(date.today())
yesterday=str(date.today()-timedelta(days=1))

def addUser(username,password):
    conn=sqlite3.connect(userpath)
    curs=conn.cursor()
    curs.execute("SELECT * FROM users")
    data=curs.fetchall()
    for row in data:
        if username==row[1]:
            return "exists"
    curs.execute(f"""
    INSERT INTO users(username,password)
    VALUES(?,?)
    """,(username,password))
    conn.commit()
    conn.close()

def loginUser(username,password):
    conn=sqlite3.connect(userpath)
    curs=conn.cursor()
    curs.execute("""SELECT * FROM users""")
    userdata=curs.fetchall()
    for user in userdata:
        if username==user[1] and password==user[2]:
            return user[0]
        
def addHabit(habit,uid):
    conn=sqlite3.connect(habitpath)
    curs=conn.cursor()
    curs.execute("""
    INSERT INTO habits(habit,lastcompleted,streak,uid)
    VALUES(?,?,?,?)""",(habit,today,0,uid))
    conn.commit()
    conn.close()

def viewHabits(uid):
    conn=sqlite3.connect(habitpath)
    curs=conn.cursor()
    curs.execute("""SELECT * FROM habits
                 WHERE uid=?""",(uid,))
    data=curs.fetchall()
    conn.close()
    return data
   
def deleteHabit(idn):
    conn=sqlite3.connect(habitpath)
    curs=conn.cursor()
    curs.execute("""
                DELETE FROM habits
                WHERE id=?""",(idn,))
    conn.commit()
    conn.close()

def updateHabit(param,value,idn,uid):
    conn=sqlite3.connect(habitpath)
    curs=conn.cursor()
    curs.execute(f"""
                UPDATE habits
                SET {param}=?
                WHERE id=? AND uid=?""",(value,idn,uid))
    conn.commit()
    conn.close()
                
app=Flask(__name__)
app.secret_key="something"
@app.route("/",methods=["GET","POST"])
def signup():
    if request.method=="POST":
        if "signup" in request.form:
            username=request.form["username"]
            password=request.form["password"]
            password=hashlib.sha256(password.encode()).hexdigest()
            if username=="" or password=="":
                message="Please fill both the boxes!"
            else:
                check=addUser(username,password)
                if check=="exists":
                    message="Username already exists! Go to the login page or try another username!"
                else:
                    message="Signed up successfully!"
            return render_template("signup.html",message=message)
        elif "login" in request.form:
            return redirect("/login")
    return render_template("signup.html")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        if "login" in request.form:
            username=request.form['username']
            password=request.form['password']
            password=hashlib.sha256(password.encode()).hexdigest()
            uid=loginUser(username,password)
            if uid is None:
                message="Invalid Credentials! Try Again!"
            elif username=="" or password=="":
                message="Please fill both the boxes!"
            else:
                message="Login Successful!" 
                session['user_id']=uid
                return redirect("/home")
            return render_template("login.html",message=message)
    return render_template("login.html")
@app.route("/home", methods=["GET","POST"])
def home():
    uid=session.get('user_id')
    if uid is None:
        return redirect("/login")
    habits=viewHabits(uid)
    for habit in habits:
        if habit[2] not in (today,yesterday):
            updateHabit("streak",0,habit[0],uid)
    if request.method == "POST":
        if "delete" in request.form:
            idn=int(request.form["delete"])
            deleteHabit(idn)
        elif "edit" in request.form:
            idn=int(request.form["edit"])
            return redirect(f"/edit/{idn}")
        elif "completed" in request.form:
            idn=int(request.form["completed"])
            for habit in habits:
                if habit[0] == idn and habit[4]==uid:
                    if habit[2]==yesterday:
                        streak=habit[3]+1
                        updateHabit("streak",streak,idn,uid)
                        updateHabit("lastcompleted",today,idn,uid)
                    elif habit[2]==today and habit[3]==0:
                        streak=1
                        updateHabit("streak",streak,idn,uid)
                        updateHabit("lastcompleted",today,idn,uid) 
                    elif habit[2]==today and habit[3]!=0:
                        print("it works")
                        streak=habit[3]
                        updateHabit("streak",streak,idn,uid)
                        updateHabit("lastcompleted",today,idn,uid) 
                    else:
                        streak=1
                        updateHabit("streak",streak,idn,uid)
                        updateHabit("lastcompleted",today,idn,uid)  
        elif "add" in request.form:
            habit = (request.form["habit"])
            addHabit(habit,uid)
        elif "logout" in request.form:
            session.pop("user_id", None)
            return redirect("/login")
    habits=viewHabits(uid)
    return render_template("home.html",habits=habits)
@app.route("/edit/<int:idn>", methods=["GET","POST"])
def edit(idn):
    uid=session['user_id']
    if request.method=="POST":
        if "editbutton" in request.form:
            value=request.form['edit']
            updateHabit("habit",value,idn,uid)
        elif "home" in request.form:
            return redirect("/home")
    habits=viewHabits(uid)
    for hab in habits:
        if idn==hab[0] and uid==hab[4]:
            habit=hab
    return render_template("edit.html",habit=habit)
app.run(debug=True)