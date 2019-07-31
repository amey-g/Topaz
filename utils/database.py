import time
import datetime
from flask import current_app

from utils.github import update_public_repos


# Cache data once every 15 minutes
cache_rate = 15 * 60  # sec


def get_public_repos(db_conn):
    """
    Returns a list of public repos from github
    Args:
        db_conn: sqlite3 db connection object

    Returns (repos, update_time): a list of repos and the last updated time

    """
    c = db_conn.cursor()
    start_time = current_app.config["CACHED_TIME"]
    if time.time() - start_time > cache_rate:
        current_app.config.from_mapping(CACHED_TIME=time.time())
        update_public_repos(db_conn)

    updated_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    c.execute("SELECT * FROM public_repos")
    all_rows = c.fetchall()
    repos = [dict(row) for row in all_rows[::-1]]
    return repos, updated_time


def get_blogs(db_conn):
    """
    Returns a list of blogs from recent to old order
    Args:
        db_conn: sqlite3 db connection object

    Returns (list): a list of dicts with key as columns and values as table values

    """
    c = db_conn.cursor()
    c.execute("SELECT * FROM blogs")
    all_rows = c.fetchall()
    all_rows = [dict(row) for row in all_rows[::-1]]
    return all_rows


def add_blog(db_conn, title, description, url, image_url):
    """
    Adds entries as another row
    Args:
        db_conn: sqlite3 db connection object
        title (str): blog title
        description (str): blog description
        url (str): blog link
        image_url (str): image link

    Returns:

    """
    c = db_conn.cursor()
    try:
        c.execute("INSERT INTO blogs (title, description, url, image_url, timestamp) VALUES "
                  "(?, ?, ?, ?, CURRENT_TIMESTAMP)",
                  (title, description, url, image_url))
        db_conn.commit()
        db_conn.close()
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    return True


def try_pop(l):
    """
    Try popping if not return a None dict
    Args:
        l: list to try popp'in

    Returns: popped value and list

    """
    try:
        value = l.pop(0)
    except IndexError:
        value = {"timestamp": None}
    return value, l


def max_times(times):
    """
    Returns the index of the max datetime
    Args:
        times (list): a list of datetimes in format 'YYYY-MM-DD HH:MM:SS'

    Returns: index of latest time

    """
    date_times = []
    for t in times:
        if t is None:
            date_times.append(datetime.datetime.now().replace(1970, 1, 1, 0, 0, 0))  # replace Nones with earliest date
            continue
        dt = []
        t = t.split("-")
        t = [i for i in t]
        for i in t:
            if ":" in i:
                i = i.split(" ")
                dt.append(i[0])
                dt.extend([j.strip() for j in i[1].split(":")])
            else:
                dt.append(i.strip())
        dt = list(map(int, dt))
        date_times.append(datetime.datetime.now().replace(*dt))
    return date_times.index(max(date_times))


def get_top_k_entries(db_conn, k):
    """
    Returns a list of top k latest entries
    Args:
        db_conn: db connection object
        k (int): top k

    Returns: a list of top k entries

    """
    top_k = []
    repos, _ = get_public_repos(db_conn)
    blogs = get_blogs(db_conn)
    repo, repos = try_pop(repos)
    blog, blogs = try_pop(blogs)
    for _ in range(k):
        times = [repo["timestamp"], blog["timestamp"]]
        latest_idx = max_times(times)
        if latest_idx == 0:
            top_k.append(repo)
            repo, repos = try_pop(repos)
        elif latest_idx == 1:
            top_k.append(blog)
            blog, blogs = try_pop(blogs)
    return top_k
