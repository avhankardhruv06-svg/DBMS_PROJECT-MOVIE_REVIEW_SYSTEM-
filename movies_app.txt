import oracledb
import getpass
from datetime import datetime

def get_connection():
    return oracledb.connect(
        user="scott",
        password="tiger",
        dsn="localhost/orclpdb1"
    )

def next_seq(seq_name):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT {seq_name}.NEXTVAL FROM dual")
        return cur.fetchone()[0]

def register_user():
    name = input("Name: ").strip()
    email = input("Email: ").strip()
    pwd = getpass.getpass("Password: ").strip()
    join_date = datetime.now().strftime("%Y-%m-%d")
    try:
        uid = next_seq("users_seq")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (join_date, user_id, name, password, email, admin)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, (join_date, uid, name, pwd, email, 0))
            conn.commit()
        print("Registered. Your user id:", uid)
    except Exception as e:
        print("Error registering:", e)

def login_user():
    email = input("Email: ").strip()
    pwd = getpass.getpass("Password: ").strip()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, admin FROM users WHERE email=:1 AND password=:2", (email, pwd))
        r = cur.fetchone()
        if r:
            user_id, name, admin = r
            print(f"Welcome {name} ({'Admin' if admin else 'User'})!")
            return int(user_id), int(admin)
        else:
            print("Invalid credentials.")
            return None, 0

def search_movies():
    print("\nEnter filters — leave blank to skip.")
    title = input("Title substring: ").strip()
    movie_name = input("Movie name substring: ").strip()
    genre = input("Genre: ").strip()
    actor = input("Actor name substring: ").strip()
    director = input("Director name substring: ").strip()
    year = input("Release year (exact): ").strip()
    dur_min = input("Min duration (minutes): ").strip()
    dur_max = input("Max duration (minutes): ").strip()

    query = """
    SELECT m.movie_id, m.title, m.movie_name, m.release_year, m.duration, g.genre_name, d.director_name, a.actor_name,
           AVG(r.rating) OVER (PARTITION BY m.movie_id) AS avg_rating
    FROM movie m
    LEFT JOIN genre g ON m.genre_id = g.genre_id
    LEFT JOIN director d ON m.director_id = d.director_id
    LEFT JOIN actor a ON m.actor_id = a.actor_id
    LEFT JOIN review r ON r.movie_id = m.movie_id
    WHERE 1=1
    """
    params = []
    if title:
        params.append(f"%{title.lower()}%"); query += f" AND LOWER(m.title) LIKE :{len(params)}"
    if movie_name:
        params.append(f"%{movie_name.lower()}%"); query += f" AND LOWER(m.movie_name) LIKE :{len(params)}"
    if genre:
        params.append(genre.lower()); query += f" AND LOWER(g.genre_name)=:{len(params)}"
    if actor:
        params.append(f"%{actor.lower()}%"); query += f" AND LOWER(a.actor_name) LIKE :{len(params)}"
    if director:
        params.append(f"%{director.lower()}%"); query += f" AND LOWER(d.director_name) LIKE :{len(params)}"
    if year:
        try:
            params.append(int(year)); query += f" AND m.release_year=:{len(params)}"
        except:
            print("Ignoring invalid year")
    if dur_min:
        try:
            params.append(int(dur_min)); query += f" AND m.duration >= :{len(params)}"
        except:
            print("Ignoring invalid min duration")
    if dur_max:
        try:
            params.append(int(dur_max)); query += f" AND m.duration <= :{len(params)}"
        except:
            print("Ignoring invalid max duration")

    query += " GROUP BY m.movie_id, m.title, m.movie_name, m.release_year, m.duration, g.genre_name, d.director_name, a.actor_name ORDER BY m.movie_name"

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        if not rows:
            print("No movies found.")
            return
        print("\nFound movies:")
        for r in rows:
            mid, ttl, mname, ry, dur, gname, dname, aname, avg_rating = r
            avg_str = f"{avg_rating:.2f}" if avg_rating is not None else "N/A"
            print(f"[{mid}] {mname} (Title: {ttl}) — {ry}, {dur}min, Genre: {gname}, Director: {dname}, Actor: {aname}, AvgRating: {avg_str}")

def add_or_update_review(user_id):
    movie_id = input("Movie ID: ").strip()
    if not movie_id.isdigit():
        print("Invalid movie id.")
        return
    movie_id = int(movie_id)
    rating = input("Rating (1.0 - 5.0): ").strip()
    try:
        rating = float(rating)
    except:
        print("Invalid rating.")
        return
    text = input("Review text: ").strip()
    now = datetime.now()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT review_id FROM review WHERE user_id=:1 AND movie_id=:2", (user_id, movie_id))
        r = cur.fetchone()
        if r:
            review_id = r[0]
            cur.execute("""
                UPDATE review SET rating=:1, review_text=:2, review_date=:3 WHERE review_id=:4
            """, (rating, text, now, review_id))
            print("Review updated.")
        else:
            rid = next_seq("review_seq")
            cur.execute("""
                INSERT INTO review (review_text, rating, review_id, user_id, movie_id, review_date)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, (text, rating, rid, user_id, movie_id, now))
            print("Review added.")
        conn.commit()

def delete_review(user_id):
    movie_id = input("Movie ID of review to delete: ").strip()
    if not movie_id.isdigit():
        print("Invalid movie id.")
        return
    movie_id = int(movie_id)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM review WHERE user_id=:1 AND movie_id=:2", (user_id, movie_id))
        if cur.rowcount:
            conn.commit()
            print("Review deleted.")
        else:
            print("No review found to delete.")

def view_movie_reviews():
    movie_id = input("Movie ID: ").strip()
    if not movie_id.isdigit():
        print("Invalid movie id.")
        return
    movie_id = int(movie_id)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.name, r.rating, r.review_text, r.review_date
            FROM review r JOIN users u ON r.user_id = u.user_id
            WHERE r.movie_id=:1
            ORDER BY r.review_date DESC
        """, (movie_id,))
        rows = cur.fetchall()
        if not rows:
            print("No reviews found for this movie.")
            return
        print(f"\nReviews for movie id {movie_id}:")
        for name, rating, text, rd in rows:
            date_str = rd.strftime("%Y-%m-%d") if isinstance(rd, datetime) else str(rd)
            print(f"- {name} ({rating}/5) on {date_str}: {text}")

def add_genre():
    name = input("Genre name: ").strip()
    gid = next_seq("genre_seq")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO genre (genre_id, genre_name) VALUES (:1, :2)", (gid, name))
        conn.commit()
    print("✅ Genre added. id:", gid)

def add_actor():
    name = input("Actor name: ").strip()
    birth = input("Birth year: ").strip()
    nat = input("Nationality: ").strip()
    aid = next_seq("actor_seq")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO actor (actor_id, actor_name, birth_year, nationality) VALUES (:1,:2,:3,:4)",
                    (aid, name, int(birth) if birth.isdigit() else None, nat))
        conn.commit()
    print("✅ Actor added id:", aid)

def add_director():
    name = input("Director name: ").strip()
    birth = input("Birth year: ").strip()
    nat = input("Nationality: ").strip()
    did = next_seq("director_seq")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO director (director_id, director_name, nationality, birth_year) VALUES (:1,:2,:3,:4)",
                    (did, name, nat, int(birth) if birth.isdigit() else None))
        conn.commit()
    print("✅ Director added id:", did)

def add_movie_admin():
    title = input("Title (short): ").strip()
    movie_name = input("Movie name (display): ").strip()
    year = input("Release year: ").strip()
    duration = input("Duration (minutes): ").strip()
    print("Choose genre: (enter id) or blank to create new")
    g_id = input("Genre id: ").strip()
    if not g_id:
        print("Create new genre:")
        add_genre()
        g_id = input("Enter new genre id you created: ").strip()
    print("Choose director id (or create new):")
    d_id = input("Director id: ").strip()
    if not d_id:
        add_director()
        d_id = input("Enter new director id you created: ").strip()
    print("Choose actor id (or create new):")
    a_id = input("Actor id: ").strip()
    if not a_id:
        add_actor()
        a_id = input("Enter new actor id you created: ").strip()

    mid = next_seq("movie_seq")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO movie (title, movie_id, movie_name, release_year, duration, genre_id, director_id, actor_id)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
        """, (title, mid, movie_name, int(year) if year.isdigit() else None,
              int(duration) if duration.isdigit() else None,
              int(g_id), int(d_id), int(a_id)))
        conn.commit()
    print("✅ Movie added id:", mid)

def edit_movie_admin():
    movie_id = input("Movie id to edit: ").strip()
    if not movie_id.isdigit():
        print("Invalid id")
        return
    movie_id = int(movie_id)
    print("Leave field blank to keep current value.")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT title, movie_name, release_year, duration, genre_id, director_id, actor_id FROM movie WHERE movie_id=:1", (movie_id,))
        row = cur.fetchone()
        if not row:
            print("Movie not found.")
            return
        cur_title, cur_mname, cur_year, cur_dur, cur_gid, cur_did, cur_aid = row
        title = input(f"Title [{cur_title}]: ").strip() or cur_title
        movie_name = input(f"Movie name [{cur_mname}]: ").strip() or cur_mname
        year = input(f"Release year [{cur_year}]: ").strip() or cur_year
        duration = input(f"Duration [{cur_dur}]: ").strip() or cur_dur
        gid = input(f"Genre id [{cur_gid}]: ").strip() or cur_gid
        did = input(f"Director id [{cur_did}]: ").strip() or cur_did
        aid = input(f"Actor id [{cur_aid}]: ").strip() or cur_aid
        cur.execute("""
            UPDATE movie SET title=:1, movie_name=:2, release_year=:3, duration=:4, genre_id=:5, director_id=:6, actor_id=:7
            WHERE movie_id=:8
        """, (title, movie_name, int(year) if str(year).isdigit() else None,
              int(duration) if str(duration).isdigit() else None,
              int(gid), int(did), int(aid), movie_id))
        conn.commit()
    print("✅ Movie updated.")

def delete_movie_admin():
    movie_id = input("Movie id to delete: ").strip()
    if not movie_id.isdigit():
        print("Invalid id")
        return
    movie_id = int(movie_id)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM review WHERE movie_id=:1", (movie_id,))
        cur.execute("DELETE FROM movie WHERE movie_id=:1", (movie_id,))
        conn.commit()
    print("✅ Movie and its reviews removed (if existed).")

def list_all(table, cols="*"):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT {cols} FROM {table} ORDER BY 1")
        rows = cur.fetchall()
        if not rows:
            print(f"No records in {table}.")
            return
        print(f"\n--- {table.upper()} ---")
        for r in rows:
            print(r)

def user_menu(user_id):
    while True:
        print("\n--- User Menu ---")
        print("1. Search movies")
        print("2. Add or update review")
        print("3. Delete my review")
        print("4. View reviews for a movie")
        print("5. Logout")
        c = input("Choice: ").strip()
        if c == "1":
            search_movies()
        elif c == "2":
            add_or_update_review(user_id)
        elif c == "3":
            delete_review(user_id)
        elif c == "4":
            view_movie_reviews()
        elif c == "5":
            break
        else:
            print("Invalid choice.")

def admin_menu(user_id):
    while True:
        print("\n--- Admin Menu ---")
        print("1. Search movies")
        print("2. Add movie")
        print("3. Edit movie")
        print("4. Delete movie")
        print("5. Add actor")
        print("6. Add director")
        print("7. Add genre")
        print("8. List actors")
        print("9. List directors")
        print("10. List genres")
        print("11. List movies")
        print("12. View reviews for a movie")
        print("13. Add or update review (as admin)")
        print("14. Logout")
        c = input("Choice: ").strip()
        if c == "1":
            search_movies()
        elif c == "2":
            add_movie_admin()
        elif c == "3":
            edit_movie_admin()
        elif c == "4":
            delete_movie_admin()
        elif c == "5":
            add_actor()
        elif c == "6":
            add_director()
        elif c == "7":
            add_genre()
        elif c == "8":
            list_all("actor", "actor_id, actor_name, birth_year, nationality")
        elif c == "9":
            list_all("director", "director_id, director_name, nationality, birth_year")
        elif c == "10":
            list_all("genre", "genre_id, genre_name")
        elif c == "11":
            list_all("movie", "movie_id, movie_name, release_year, duration")
        elif c == "12":
            view_movie_reviews()
        elif c == "13":
            add_or_update_review(user_id)
        elif c == "14":
            break
        else:
            print("Invalid choice.")

def main():
    print("=== Movie App (Oracle) ===")
    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        cmd = input("Choice: ").strip()
        if cmd == "1":
            register_user()
        elif cmd == "2":
            uid, admin = login_user()
            if uid:
                if admin:
                    admin_menu(uid)
                else:
                    user_menu(uid)
        elif cmd == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()