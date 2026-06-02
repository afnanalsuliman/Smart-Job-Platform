from flask import Flask, render_template, request, redirect
import pandas as pd
import matplotlib.pyplot as plt
import os
import sqlite3

app = Flask(__name__)

# 🔥 إنشاء قاعدة البيانات
def init_db():
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            salary INTEGER,
            experience TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# 🔥 الصفحة الرئيسية
@app.route("/")
def home():

    # إنشاء مجلد static إذا مو موجود
    if not os.path.exists("static"):
        os.makedirs("static")

    chart_path = "static/chart.png"

    # 🔥 جلب البيانات
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("SELECT id, title, company, salary, experience FROM jobs")
    jobs = c.fetchall()
    conn.close()

    # 🔥 رسم بياني ديناميكي
    if jobs:
        df = pd.DataFrame(jobs, columns=["id", "title", "company", "salary", "experience"])

        plt.figure()
        df.groupby("experience")["salary"].mean().plot(kind="bar")

        plt.title("Average Salary by Experience")
        plt.xlabel("Experience Level")
        plt.ylabel("Salary")

        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()

    return render_template("index.html", jobs=jobs)


# 🔥 إضافة وظيفة
@app.route("/add", methods=["POST"])
def add_job():
    title = request.form["title"]
    company = request.form["company"]
    salary = request.form["salary"]
    experience = request.form["experience"]

    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    # منع التكرار
    c.execute("""
        SELECT * FROM jobs 
        WHERE title=? AND company=? AND salary=? AND experience=?
    """, (title, company, salary, experience))

    existing_job = c.fetchone()

    if not existing_job:
        c.execute("""
            INSERT INTO jobs (title, company, salary, experience)
            VALUES (?, ?, ?, ?)
        """, (title, company, salary, experience))
        conn.commit()

    conn.close()
    return redirect("/")


# 🔥 حذف وظيفة
@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

    return redirect("/")


# 🔥 صفحة التعديل (فتح الفورم)
@app.route("/edit/<int:job_id>")
def edit_job(job_id):
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()

    conn.close()

    return render_template("edit.html", job=job)


# 🔥 حفظ التعديل
@app.route("/update/<int:job_id>", methods=["POST"])
def update_job(job_id):
    title = request.form["title"]
    company = request.form["company"]
    salary = request.form["salary"]
    experience = request.form["experience"]

    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute("""
        UPDATE jobs
        SET title=?, company=?, salary=?, experience=?
        WHERE id=?
    """, (title, company, salary, experience, job_id))

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)