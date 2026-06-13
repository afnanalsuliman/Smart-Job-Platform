from flask import Flask, render_template, request, redirect
import pandas as pd
import matplotlib.pyplot as plt
import os
import sqlite3

app = Flask(__name__)

# إنشاء قاعدة البيانات
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


# الصفحة الرئيسية
@app.route("/")
def home():

    search = request.args.get("search", "")
    experience_filter = request.args.get("experience", "")
    sort = request.args.get("sort", "")
    # إنشاء مجلد static إذا مو موجود
    if not os.path.exists("static"):
        os.makedirs("static")

    chart_path = "static/chart.png"

    # جلب البيانات
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    if search and experience_filter:
        c.execute("""
            SELECT id, title, company, salary, experience
            FROM jobs
            WHERE (title LIKE ? OR company LIKE ?)
            AND experience = ?
        """, (f"%{search}%", f"%{search}%", experience_filter))

    elif search:
        c.execute("""
            SELECT id, title, company, salary, experience
            FROM jobs
            WHERE title LIKE ? OR company LIKE ?
        """, (f"%{search}%", f"%{search}%"))

    elif experience_filter:
        c.execute("""
            SELECT id, title, company, salary, experience
            FROM jobs
            WHERE experience = ?
        """, (experience_filter,))

    else:
        c.execute("""
            SELECT id, title, company, salary, experience
            FROM jobs
        """)

    jobs = c.fetchall()
    conn.close()

    if sort == "high":
        jobs = sorted(jobs, key=lambda x: x[3], reverse=True)

    elif sort == "low":
        jobs = sorted(jobs, key=lambda x: x[3])

    # Statistics
    total_jobs = len(jobs)

    if jobs:
        salaries = [job[3] for job in jobs]

        average_salary = round(sum(salaries) / len(salaries))
        highest_salary = max(salaries)

        junior_count = len([j for j in jobs if j[4] == "Junior"])
        mid_count = len([j for j in jobs if j[4] == "Mid"])
        senior_count = len([j for j in jobs if j[4] == "Senior"])

    else:
        average_salary = 0
        highest_salary = 0

        junior_count = 0
        mid_count = 0
        senior_count = 0
    # رسم الشارت
    if jobs:
        df = pd.DataFrame(
            jobs,
            columns=["id", "title", "company", "salary", "experience"]
        )

        experience_counts = df["experience"].value_counts()

        plt.figure(figsize=(6, 6))

        plt.pie(
            experience_counts,
            labels=experience_counts.index,
            autopct="%1.1f%%"
        )

        plt.title("Jobs Distribution by Experience")

        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()

    return render_template(
        "index.html",
        jobs=jobs,
        search=search,
        total_jobs=total_jobs,
        average_salary=average_salary,
        highest_salary=highest_salary,
        junior_count=junior_count,
        mid_count=mid_count,
        senior_count=senior_count
    )

# إضافة وظيفة
@app.route("/add", methods=["POST"])
def add_job():

    title = request.form["title"]
    company = request.form["company"]
    salary = request.form["salary"]
    experience = request.form["experience"]

    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute("""
        SELECT *
        FROM jobs
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


# حذف وظيفة
@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):

    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute("DELETE FROM jobs WHERE id=?", (job_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# فتح صفحة التعديل
@app.route("/edit/<int:job_id>")
def edit_job(job_id):

    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()

    conn.close()

    return render_template("edit.html", job=job)


# حفظ التعديل
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

@app.route("/download")
def download_csv():

    conn = sqlite3.connect("jobs.db")

    df = pd.read_sql_query(
        "SELECT * FROM jobs",
        conn
    )

    conn.close()

    csv_file = "jobs_export.csv"

    df.to_csv(csv_file, index=False)

    from flask import send_file

    return send_file(
        csv_file,
        as_attachment=True
    )
if __name__ == "__main__":
    app.run(debug=True)
