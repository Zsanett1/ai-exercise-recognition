import sqlite3
import hashlib
import datetime

db_file = "fitness_app.db"

def init_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("""
                   create table if not exists users (
                   id integer primary key autoincrement,
                   username text unique not null,
                   password text not null,
                   full_name text,
                   age integer,
                   gender text, 
                   profile_picture text,
                   fitness_goal text,
                   fitness_level text,
                   daily_target integer
                   )""")
    
    cursor.execute("""
                    create table if not exists workouts (
                    id integer primary key autoincrement,
                    username text not null,
                    exercise_name text not null,
                    total_reps integer not null,
                    correct_reps integer not null,
                    feedback text,
                    screenshot text,
                    date text not null
                    )""")
    
    cursor.execute("""
                   create table if not exists exercises (
                   id integer primary key autoincrement,
                   name text unique not null,
                   category text not null,
                   equipment text,
                   focus text,
                   image_path text,
                   model_label text,
                   is_trackable integer default 0
                   )""")
    
    cursor.execute("""
                   create table if not exists exercise_steps (
                   id integer primary key autoincrement,
                   exercise_id integer not null,
                   step_order integer not null,
                   instruction text not null,
                   foreign key (exercise_id) references exercises(id)
                   )""")

    cursor.execute("""
                   create table if not exists exercise_categories (
                   id integer primary key autoincrement,
                   name text unique not null,
                   description text
                   )""")

    conn.commit()
    conn.close()

    seed_exercise_categories()
    seed_exercises()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    hashed = hash_password(password)
    try:
        cursor.execute("insert into users (username, password) values (?, ?)", (username, hashed))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def check_login(username, password):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    hashed = hash_password(password)
    cursor.execute("select * from users where username = ? and password = ?", (username, hashed))
    user = cursor.fetchone()
    conn.close()
    return user 

def get_user_profile(username):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("select full_name, age, gender, profile_picture, fitness_goal, fitness_level, daily_target from users where username = ?", (username, ))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "full_name": row[0] or "",
            "age": row[1] or 0,
            "gender": row[2] or "Male",
            "profile_picture": row[3] or "default",
            "fitness_goal": row[4] or "Stay Fit",
            "fitness_level": row[5] or "Beginner",
            "daily_target": row[6] or 50
        }
    return None

def update_user_profile(username, full_name, age, gender, profile_picture, fitness_goal, fitness_level, daily_target):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
                   update users
                   set full_name = ?, age = ?, gender = ?, profile_picture = ?, fitness_goal = ?, fitness_level = ?, daily_target = ?
                   where username = ?""", 
                   (full_name, age, gender, profile_picture, fitness_goal, fitness_level, daily_target, username))
    conn.commit()
    conn.close()

def insert_workout(username, exercise_name, total_reps, correct_reps, feedback, screenshot, date_str):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
                   insert into workouts (username, exercise_name, total_reps, correct_reps, feedback, screenshot, date)
                   values (?, ?, ?, ?, ?, ?, ?)
                   """, (username, exercise_name, total_reps, correct_reps, feedback, screenshot, date_str))
    conn.commit()
    conn.close()

def get_workouts_by_date(username, date_str):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
                   select exercise_name, total_reps, correct_reps, feedback, screenshot
                   from workouts where username = ? and date = ?
                   """, (username, date_str))
    rows = cursor.fetchall()
    conn.close()
    workouts_list = []
    for row in rows:
        workouts_list.append({
            "exercise_name": row[0],
            "total_reps": row[1],
            "correct_reps": row[2],
            "feedback": row[3],
            "screenshot": row[4]
        })
    return workouts_list

def get_user_stats(username):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("select count(*) from workouts where username = ?", (username, ))
    total_workouts = cursor.fetchone()[0] or 0
    cursor.execute("select sum(total_reps) from workouts where username = ?", (username, ))
    total_reps = cursor.fetchone()[0] or 0
    conn.close()
    return total_workouts, total_reps

def get_last_active_session(username):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("select max(date) from workouts where username = ?", (username, ))
    last_date_str = cursor.fetchone()[0]
    conn.close()
    if not last_date_str:
        return "Never"
    last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days = 1)
    if last_date == today:
        return "Today"
    elif last_date == yesterday:
        return "Yesterday"
    else:
        return last_date.strftime("%B %d, %Y")

def get_daily_reps(username):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("select sum(total_reps) from workouts where username = ? and date = ?", (username, today_str))
    daily_reps = cursor.fetchone()[0] or 0
    conn.close()
    return daily_reps

def seed_exercises():
    exercises = [
        {
            "name": "Push Up",
            "category": "Upper Body",
            "equipment": "None",
            "focus": "Chest, shoulders, triceps",
            "image_path": "assets/push_up.jpg",
            "model_label": "push_up",
            "is_trackable": 0,
            "steps": [
                "Start in a high plank position with your hands under your shoulders.",
                "Keep your body in a straight line from head to heels.",
                "Lower your chest toward the floor with controlled movement.",
                "Push back up until your arms are extended.",
            ],
        },
        {
            "name": "Shoulder Press",
            "category": "Upper Body",
            "equipment": "Dumbbells or resistance bands, or two bottles of water",
            "focus": "Shoulders, upper chest, triceps",
            "image_path": "assets/shoulder_press.jpg",
            "model_label": "shoulder_press",
            "is_trackable": 0,
            "steps": [
                "Stand tall and hold the weights at shoulder height.",
                "Brace your core and avoid arching your lower back.",
                "Press the weights overhead in a controlled motion.",
                "Lower them slowly back to shoulder height.",
            ],
        },
        {
            "name": "Bicep Curl",
            "category": "Arms",
            "equipment": "Dumbbells or resistance bands, or two bottles of water",
            "focus": "Biceps and forearms",
            "image_path": "assets/bicep_curl.jpg",
            "model_label": "bicep_curl",
            "is_trackable": 0,
            "steps": [
                "Stand tall with your elbows close to your torso.",
                "Curl the weight upward without swinging your body.",
                "Pause briefly at the top of the movement.",
                "Lower the weight slowly and fully control the return.",
            ],
        },
        {
            "name": "Overhead Extension",
            "category": "Arms",
            "equipment": "One dumbbell or resistance band, or a bottle of water",
            "focus": "Triceps",
            "image_path": "assets/overhead_extension.jpg",
            "model_label": "overhead_extension",
            "is_trackable": 0,
            "steps": [
                "Hold the weight overhead with both hands.",
                "Keep your elbows pointing forward and close to your head.",
                "Lower the weight behind your head with control.",
                "Extend your arms back to the starting position.",
            ],
        },
        {
            "name": "Squat",
            "category": "Lower Body",
            "equipment": "None",
            "focus": "Quadriceps, glutes, hamstrings",
            "image_path": "assets/squat.jpg",
            "model_label": "squat",
            "is_trackable": 1,
            "steps": [
                "Stand with your feet about shoulder-width apart.",
                "Push your hips back and bend your knees.",
                "Keep your chest lifted and knees aligned with your feet.",
                "Drive through your heels to return to standing.",
            ],
        },
        {
            "name": "Calf Raises",
            "category": "Lower Body",
            "equipment": "None",
            "focus": "Calves",
            "image_path": "assets/calf_raises.jpg",
            "model_label": "calf_raises",
            "is_trackable": 0,
            "steps": [
                "Stand tall with your feet hip-width apart.",
                "Rise onto the balls of your feet.",
                "Pause briefly at the top.",
                "Lower your heels slowly back to the floor.",
            ],
        },
        {
            "name": "Abdominal Crunch",
            "category": "Core / Abs",
            "equipment": "Yoga mat recommended",
            "focus": "Upper abdominals",
            "image_path": "assets/crunch.jpg",
            "model_label": "crunch",
            "is_trackable": 0,
            "steps": [
                "Lie on your back with your knees bent and feet flat on the floor.",
                "Place your hands lightly behind your head or across your chest.",
                "Engage your core and lift your shoulders from the floor.",
                "Lower back down slowly without relaxing completely.",
            ],
        },
        {
            "name": "Plank",
            "category": "Core / Abs",
            "equipment": "Yoga mat recommended",
            "focus": "Core, shoulders, glutes",
            "image_path": "assets/plank.jpg",
            "model_label": "plank",
            "is_trackable": 0,
            "steps": [
                "Place your elbows directly under your shoulders.",
                "Keep your body in a straight line from head to heels.",
                "Brace your core and squeeze your glutes.",
                "Breathe steadily and avoid letting your hips sag.",
            ],
        },
        {
            "name": "Superman",
            "category": "Core / Abs",
            "equipment": "Yoga mat recommended",
            "focus": "Lower back, glutes, posterior chain",
            "image_path": "assets/superman.jpg",
            "model_label": "superman",
            "is_trackable": 0,
            "steps": [
                "Lie face down with arms extended in front of you.",
                "Lift your arms, chest, and legs slightly from the floor.",
                "Hold briefly while keeping your neck neutral.",
                "Lower back down with control.",
            ],
        },
    ]
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    for exercise in exercises:
        cursor.execute("""
                insert or ignore into exercises
                (name, category, equipment, focus, image_path, model_label, is_trackable)
                values (?, ?, ?, ?, ?, ?, ?)
                """, (
                    exercise["name"], exercise["category"], exercise["equipment"], exercise["focus"], 
                    exercise["image_path"], exercise["model_label"], exercise["is_trackable"],
                ))
        cursor.execute("select id from exercises where name = ?", (exercise["name"],))
        exercise_id = cursor.fetchone()[0]
        cursor.execute("select count(*) from exercise_steps where exercise_id = ?", (exercise_id,))
        steps_already_exist = cursor.fetchone()[0] > 0
        if not steps_already_exist:
            for index, instruction in enumerate(exercise["steps"], start = 1):
                cursor.execute("""
                               insert into exercise_steps (exercise_id, step_order, instruction)
                               values (?, ?, ?)""", (exercise_id, index, instruction))
    conn.commit()
    conn.close()

def seed_exercise_categories():
    categories = [
        {
            "name": "Upper Body",
            "description": "Upper body exercises mainly focus on the chest, shoulders, back and arms. They help improve pushing strength, posture, and everyday upper-body control.",
        },
        {
            "name": "Arms",
            "description": "Arm exercises focus on the biceps, triceps, and forearms. They support pulling, pushing, lifting, and better control during other upper-body movements.",
        },
        {
            "name": "Lower Body",
            "description": "Lower body exercises target the glutes, quadriceps, hamstrings, and calves. They are important for balance, walking, standing, and overall functional strength.",
        },
        {
            "name": "Core / Abs",
            "description": "Core exercises focus on the abdominal muscles, lower back, and stabilizing muscles. A strong core supports posture, balance, and safer movement during workouts.",
        },
    ]
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    for category in categories:
        cursor.execute("""
                        insert or ignore into exercise_categories (name, description)
                        values (?, ?)""", (category["name"], category["description"]))
    conn.commit()
    conn.close()

def get_exercise_categories():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("select name, description from exercise_categories order by name")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "name": row[0],
            "description": row[1] or "",
        }
        for row in rows
    ]

def get_exercises_by_category(category):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
                   select id, name, category, equipment, focus, image_path, model_label, is_trackable
                   from exercises where category = ? order by name""", (category,))
    exercise_rows = cursor.fetchall()
    exercises = []
    for row in exercise_rows:
        exercise_id = row[0]
        cursor.execute("""
                       select instruction from exercise_steps
                       where exercise_id = ? order by step_order""", (exercise_id,))
        step_rows = cursor.fetchall()
        exercises.append({
            "id": exercise_id, 
            "name": row[1],
            "category": row[2],
            "equipment": row[3],
            "focus": row[4],
            "image_path": row[5],
            "model_label": row[6],
            "is_trackable": bool(row[7]),
            "steps": [step[0] for step in step_rows],
        })
    conn.close()
    return exercises