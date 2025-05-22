import os
import json
import redis

from urllib.parse import urlencode
from urllib.parse import quote_plus

from os import environ as env

from flask import session
from flask import request
from flask import url_for
from flask import redirect
from flask import render_template
from flask import send_from_directory

from __init__ import app
from __init__ import oauth

from auth0 import AuthDecorators as auth

# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)


try:
    rc = redis.Redis("redis")
    rc.ping()
except Exception as e:
    print(f"[ERROR] {e}")
    exit()


###################
# Flask app routes
###################
@app.route("/")
@app.route("/index")
def index():
    return render_template(
        "index.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/annotation")
@auth.requires_auth
def annotation():
    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    if not rc.exists(f"users:{username}:progress"):
        print(f"[INFO] User {username} not found. Creating new user...")
        rc.hset(
            f"users:{username}:progress",
            mapping={
                "query_key": "",
                "image_hash": "",
            },
        )
    return render_template(
        "annotation.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


###################
# Flask API routes
###################


# Annotator API
@app.route("/resume_annotation", methods=["POST"])
@auth.requires_auth
def resume_annotation():
    """Resume annotation for a specific user."""

    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    progress = rc.hgetall(f"users:{username}:progress")
    if not progress:
        return json.dumps({"error": "User not found"}), 404
    progress = rc.decode_object(progress)

    query_key = None
    image_hash = None
    if progress["query_key"] == "" or progress["image_hash"] == "":
        query_keys = rc.keys("queries:*")
        query_keys = [key.decode("utf-8") for key in query_keys]
        query_keys = [key for key in query_keys if len(key.split(":")) == 2]

        for key in query_keys:
            if rc.exists(f"annotations:{username}:{key}"):
                continue

            query_key = key
            break

        if query_key is None:
            return json.dumps({"error": "No queries available"}), 404

        query = rc.hgetall(f"{query_key}")
        if not query:
            return json.dumps({"error": "Query not found"}), 404
        query = rc.decode_object(query)

        ground_truth = json.loads(query["ground_truth"])
        image_hash = ground_truth[0]
        current_progress = 0
    else:
        query_key = progress["query_key"]
        image_hash = progress["image_hash"]

        query = rc.hgetall(f"{query_key}")
        if not query:
            return json.dumps({"error": "Query not found"}), 404
        query = rc.decode_object(query)

        ground_truth = json.loads(query["ground_truth"])
        current_progress = rc.hlen(f"annotations:{username}:{query_key}")
        current_progress = int(current_progress / len(ground_truth) * 100)

    image = rc.hgetall(f"images:{image_hash.split('.')[0]}")
    if not image:
        return json.dumps({"error": "Image not found"}), 404
    image = rc.decode_object(image)

    image_url = f"/image/{image['hash']}.{image['extension']}"
    article_key = json.loads(image["articles"])[0]
    article = rc.hgetall(f"{article_key}")
    if not article:
        return json.dumps({"error": "Article not found"}), 404
    article = rc.decode_object(article)

    return_obj = {
        "query_key": query_key,
        "query": query["query"],
        "image_hash": image_hash,
        "image_url": image_url,
        "article_title": article["title"],
        "progress": current_progress,
    }
    return json.dumps(return_obj), 200


@app.route("/next_query", methods=["POST"])
@auth.requires_auth
def next_query():
    """Get the next query for a specific user."""

    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    query_keys = rc.keys("queries:*")
    query_keys = [key.decode("utf-8") for key in query_keys]
    query_keys = [key for key in query_keys if len(key.split(":")) == 2]
    query_key = None
    for key in query_keys:
        if rc.exists(f"annotations:{username}:{key}"):
            continue

        query_key = key
        break

    if query_key is None:
        return json.dumps({"error": "No queries available"}), 404

    query = rc.hgetall(f"{query_key}")
    if not query:
        return json.dumps({"error": "Query not found"}), 404
    query = rc.decode_object(query)

    return_obj = {
        "query_key": query_key,
        "query": query["query"],
    }
    return json.dumps(return_obj), 200


@app.route("/next_image", methods=["POST"])
@auth.requires_auth
def next_image():
    """Get the next image for a specific user."""

    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    query_key = request.json.get("query_key", None)

    query = rc.hgetall(f"{query_key}")
    if not query:
        return json.dumps({"error": "Query not found"}), 404
    query = rc.decode_object(query)

    image_hash = None
    ground_truth = json.loads(query["ground_truth"])
    for hash in ground_truth:
        if rc.hexists(f"annotations:{username}:{query_key}", hash):
            continue

        image_hash = hash
        break

    if image_hash is None:
        return json.dumps({"error": "No more images"}), 404

    image = rc.hgetall(f"images:{image_hash}")
    if not image:
        return json.dumps({"error": "Image not found"}), 404
    image = rc.decode_object(image)

    article_key = json.loads(image["articles"])[0]
    article = rc.hgetall(f"{article_key}")
    if not article:
        return json.dumps({"error": "Article not found"}), 404
    article = rc.decode_object(article)

    current_progress = rc.hlen(f"annotations:{username}:{query_key}")
    current_progress = int(current_progress / len(ground_truth) * 100)

    return_obj = {
        "image_hash": image_hash,
        "image_url": f"/image/{image['hash']}.{image['extension']}",
        "article_title": article["title"],
        "progress": current_progress,
    }
    return json.dumps(return_obj), 200


@app.route("/submit_annotation", methods=["POST"])
@auth.requires_auth
def submit_annotation():
    """Submit the annotation for a specific user."""

    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    query_key = request.json.get("query_key", None)
    image_hash = request.json.get("image_hash", None)
    annotation = request.json.get("annotation", -1)

    if query_key is None or image_hash is None or annotation == -1:
        return json.dumps({"error": "Missing parameters"}), 400

    if rc.hexists(f"annotations:{username}:{query_key}", image_hash):
        return json.dumps({"error": "Annotation already exists"}), 400
    rc.hset(f"annotations:{username}:{query_key}", image_hash, annotation)

    if rc.hexists(f"{query_key}:images:{image_hash}", username):
        return json.dumps({"error": "Annotation already exists"}), 400
    rc.hset(f"{query_key}:images:{image_hash}", username, annotation)

    rc.hset(
        f"users:{username}:progress",
        mapping={
            "query_key": query_key,
            "image_hash": image_hash,
        },
    )

    return json.dumps({"status": "success"}), 200


@app.route("/undo_annotation", methods=["POST"])
@auth.requires_auth
def undo_annotation():
    """Undo the last annotation for a specific user."""

    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    query_key = request.json.get("query_key", None)
    image_hash = request.json.get("image_hash", None)

    if query_key is None or image_hash is None:
        return json.dumps({"error": "Missing parameters"}), 400

    if not rc.hexists(f"annotations:{username}:{query_key}", image_hash):
        return json.dumps({"error": "Annotation does not exist"}), 400
    rc.hdel(f"annotations:{username}:{query_key}", image_hash)

    if not rc.hexists(f"{query_key}:images:{image_hash}", username):
        return json.dumps({"error": "Annotation does not exist"}), 400
    rc.hdel(f"{query_key}:images:{image_hash}", username)

    return json.dumps({"status": "success"}), 200


@app.route("/dns_annotation_rules", methods=["POST"])
@auth.requires_auth
def dns_annotation_rules():
    """Get the DNS annotation rules for a specific user."""

    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    show_rules = 0

    if not rc.hexists(f"users:{username}", "dns_annotation_rules"):
        rc.hset(f"users:{username}", mapping={"dns_annotation_rules": 0})

        show_rules = 0
    else:
        cache = rc.hgetall(f"users:{username}")
        cache = rc.decode_object(cache)
        show_rules = cache["dns_annotation_rules"]

    return_obj = {
        "show_rules": show_rules,
    }
    return json.dumps(return_obj), 200


@app.route("/set_dns_annotation_rules", methods=["POST"])
@auth.requires_auth
def set_dns_annotation_rules():
    """Set the DNS annotation rules for a specific user."""

    try:
        user = session.get("user")
        user_info = user["userinfo"]
        username = user_info["name"]
    except Exception as _:
        redirect("/")

    show_rules = request.json.get("show_rules", 0)

    if show_rules not in [0, 1]:
        return json.dumps({"error": "Invalid parameter"}), 400

    rc.hset(f"users:{username}", mapping={"dns_annotation_rules": show_rules})

    return json.dumps({"status": "success"}), 200


@app.route("/image/<path:filename>")
def image(filename):
    return send_from_directory(
        os.path.join(os.path.expanduser("~"), "images/"), filename
    )


@app.route("/markdown/<path:filename>")
def markdown(filename):
    return send_from_directory("./static/markdown/", filename)


###################
# Auth0 logic
###################
@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/authorize", methods=["GET", "POST"])
def authorize():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
