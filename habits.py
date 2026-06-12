import sqlite3
import os
from flask import Flask,request,render_template,redirect
from datetime import date,timedelta
fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.db")
conn=sqlite3.connect(fullpath)
curs=conn.cursor()
today=str(date.today())
yesterday=str(date.today()-timedelta(days=1))
curs.execute(f"""
    CREATE TABLE IF NOT EXISTS habits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit TEXT,
    lastcompleted TEXT,
    streak INTEGER)
    """)
conn.commit()
conn.close()

def addHabit(habit):
    fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.db")
    conn=sqlite3.connect(fullpath)
    curs=conn.cursor()
    lastcompleted=today
    curs.execute("""
    INSERT INTO habits(habit,lastcompleted,streak)
    VALUES(?,?,?)""",(habit,lastcompleted,0))
    conn.commit()
    conn.close()

def viewHabits():
    fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.db")
    conn=sqlite3.connect(fullpath)
    curs=conn.cursor()
    curs.execute("SELECT * FROM habits")
    data=curs.fetchall()
    conn.close()
    return data
   
def deleteHabit(idn):
    fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.db")
    conn=sqlite3.connect(fullpath)
    curs=conn.cursor()
    curs.execute("""
                DELETE FROM habits
                WHERE id=?""",(idn,))
    conn.commit()
    conn.close()

def updateHabit(param,value,idn):
    fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.db")
    conn=sqlite3.connect(fullpath)
    curs=conn.cursor()
    curs.execute(f"""
                UPDATE habits
                SET {param}=?
                WHERE id=?""",(value,idn))
    conn.commit()
    conn.close()
                

app=Flask(__name__)
@app.route("/", methods=["GET","POST"])
def home():
    habits=viewHabits()
    for habit in habits:
        if habit[2] not in (today,yesterday):
            updateHabit("streak",0,habit[0])
    if request.method == "POST":
        if "delete" in request.form:
            idn=request.form["delete"]
            deleteHabit(idn)
        elif "edit" in request.form:
            idn=request.form["edit"]
            return redirect(f"/edit/{idn}")
        elif "completed" in request.form:
            idn=int(request.form["completed"])
            for habit in habits:
                if habit[0] == idn:
                    if habit[2]==yesterday:
                        streak=habit[3]+1
                        updateHabit("streak",streak,idn)
                        updateHabit("lastcompleted",today,idn)
                    elif habit[2]==today:
                        streak=habit[3]
                        updateHabit("streak",streak,idn)
                        updateHabit("lastcompleted",today,idn)
                    else:
                        streak=1
                        updateHabit("streak",streak,idn)
                        updateHabit("lastcompleted",today,idn)  
        elif "add" in request.form:
            habit = request.form["habit"]
            addHabit(habit)
    habits=viewHabits()
    return render_template("home.html",habits=habits)
@app.route("/edit/<int:idn>", methods=["GET","POST"])
def edit(idn):
    if request.method=="POST":
        if "editbutton" in request.form:
            value=request.form['edit']
            updateHabit("habit",value,idn)
        elif "home" in request.form:
            return redirect("/")
    habits=viewHabits()
    for hab in habits:
        if idn==hab[0]:
            habit=hab
    return render_template("edit.html",habit=habit)
app.run(debug=True)