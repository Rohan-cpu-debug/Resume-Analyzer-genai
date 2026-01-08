# print("📂 Using DB at:", DB_NAME)

import sqlite3
import hashlib
import streamlit as st

DB_NAME = "users.db"


# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------- PASSWORD UTILS ----------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------- REGISTER ----------
def register_user(email: str, password: str):
    hashed_pw = hash_password(password)

    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, hashed_pw)
        )

        conn.commit()
        conn.close()
        return True, "User registered successfully"

    except sqlite3.IntegrityError:
        return False, "User already exists"


# ---------- LOGIN ----------
def login_user(email: str, password: str):
    hashed_pw = hash_password(password)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hashed_pw)
    )

    user = cur.fetchone()
    conn.close()

    if user:
        st.session_state["authenticated"] = True
        st.session_state["user_email"] = email
        return True
    return False


# ---------- LOGOUT ----------
def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None


# ---------- AUTH CHECK ----------
def is_authenticated():
    return st.session_state.get("authenticated", False)


# ---------- AUTH UI ----------
def init_analysis_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            role TEXT,
            overall_score INTEGER,
            ats_score INTEGER,
            strengths TEXT,
            missing_skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def auth_section():
    init_db()
    init_analysis_table()   # 👈 ADD THIS LINE


    if is_authenticated():
        st.sidebar.success(f"Logged in as {st.session_state['user_email']}")
        if st.sidebar.button("Logout"):
            logout_user()
            st.experimental_rerun()
        return True

    st.title("🔐 Login / Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")

        if st.button("Login"):
            if login_user(email, password):
                st.success("Login successful")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pw")

        if st.button("Register"):
            success, msg = register_user(email, password)
            if success:
                st.success(msg)
            else:
                st.error(msg)

    return False


# ---------- SAVE RESUME ANALYSIS ----------
def save_resume_analysis(user_email, role, analysis_result):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO resume_analysis (
            user_email,
            role,
            overall_score,
            ats_score,
            strengths,
            missing_skills
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_email,
        role,
        analysis_result.get("overall_score"),
        analysis_result.get("ats_score"),
        ", ".join(analysis_result.get("strengths", [])),
        ", ".join(analysis_result.get("missing_skills", []))
    ))

    conn.commit()
    conn.close()




# def get_user_history(user_email):
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT role, overall_score, ats_score, created_at
#         FROM resume_analysis
#         WHERE user_email = ?
#         ORDER BY created_at DESC
#     """, (user_email,))

#     rows = cur.fetchall()
#     conn.close()
#     return rows


# def get_user_history(user_email):
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT role, overall_score, ats_score, created_at
#         FROM resume_analysis
#         WHERE user_email=?
#         ORDER BY created_at DESC
#     """, (user_email,))

#     rows = cur.fetchall()
#     conn.close()
#     return rows




# ---------- RESUME ANALYSIS PERSISTENCE ----------
# def init_analysis_table():
  

#     conn = sqlite3.connect("users.db")
#     cur = conn.cursor()

#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS resume_analysis (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_email TEXT,
#             role TEXT,
#             overall_score INTEGER,
#             ats_score INTEGER,
#             strengths TEXT,
#             missing_skills TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     """)


    

 


#     conn.commit()
#     conn.close()
def get_user_history(user_email):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, role, overall_score, ats_score, strengths, missing_skills, created_at
        FROM resume_analysis
        WHERE user_email=?
        ORDER BY created_at DESC
    """, (user_email,))

    rows = cur.fetchall()
    conn.close()
    return [
    {
        "id": r[0],
        "role": r[1],
        "overall_score": r[2],
        "ats_score": r[3],
        "strengths": r[4],
        "missing_skills": r[5],
        "created_at": r[6]
    }
    for r in rows
]




    # return [
    #     {
    #         "role": r[0],
    #         "overall_score": r[1],
    #         "ats_score": r[2],
    #         "strengths": r[3],
    #         "missing_skills": r[4],
    #         "created_at": r[5]
    #     }
    #     for r in rows
    # ]



# ---------- DELETE SINGLE HISTORY ----------
def delete_single_history(history_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM resume_analysis WHERE id = ?",
        (history_id,)
    )

    conn.commit()
    conn.close()


# ---------- CLEAR ALL HISTORY FOR USER ----------
def clear_user_history(user_email):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM resume_analysis WHERE user_email = ?",
        (user_email,)
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
