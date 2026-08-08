import os
import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')

# ==========================================
# DATABASE CONNECTION FUNCTION
# ==========================================
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME'),
            port=int(os.environ.get('DB_PORT', 23530)),
            ssl_disabled=False
        )
        return connection
    except Error as e:
        print(f"Database Connection Error: {e}")
        return None

# ==========================================
# AUTO-CREATE TABLES ON STARTUP
# ==========================================
def init_db():
    conn = get_db_connection()
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            
            # Table for project showcases
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    image_url VARCHAR(500) DEFAULT NULL,
                    tech_stack VARCHAR(255) DEFAULT NULL,
                    github_url VARCHAR(500) DEFAULT NULL,
                    live_demo_url VARCHAR(500) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table for contact messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Table for analytics counters (Visitors / ML predictions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    action_type VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            cursor.close()
            print("Database tables initialized successfully!")
        except Error as e:
            print(f"Error initializing tables: {e}")
        finally:
            conn.close()

# Run table initialization on startup
init_db()

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def home():
    projects = []
    visitor_count = 0
    messages_count = 0
    ml_count = 0

    conn = get_db_connection()
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor(dictionary=True)

            # 1. Log a new live page view
            cursor.execute("INSERT INTO analytics (action_type) VALUES ('page_view')")
            conn.commit()

            # 2. Query total visitors count
            cursor.execute("SELECT COUNT(*) AS total FROM analytics WHERE action_type = 'page_view'")
            visitor_res = cursor.fetchone()
            visitor_count = visitor_res['total'] if visitor_res else 0

            # 3. Query total contact form messages count
            cursor.execute("SELECT COUNT(*) AS total FROM messages")
            msg_res = cursor.fetchone()
            messages_count = msg_res['total'] if msg_res else 0

            # 4. Query total ML predictions served (or analytics log count)
            cursor.execute("SELECT COUNT(*) AS total FROM analytics WHERE action_type = 'ml_prediction'")
            ml_res = cursor.fetchone()
            ml_count = ml_res['total'] if ml_res else 0

            # 5. Fetch all projects
            cursor.execute("SELECT * FROM projects")
            projects = cursor.fetchall()

            cursor.close()
        except Error as e:
            print(f"Error fetching stats/projects: {e}")
        finally:
            conn.close()

    return render_template(
        'index.html',
        projects=projects,
        visitor_count=visitor_count,
        ml_count=ml_count,
        messages_count=messages_count
    )


@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    if name and email and message:
        conn = get_db_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor()
                query = "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, email, message))
                conn.commit()
                cursor.close()
                flash("Message sent successfully!", "success")
            except Error as e:
                print(f"Error saving message: {e}")
                flash("Failed to send message.", "danger")
            finally:
                conn.close()

    return redirect(url_for('home'))


@app.route('/download-cv')
def download_cv():
    return send_from_directory(directory='static', path='cv.pdf', as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
