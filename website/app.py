import os
import json
from pathlib import Path

import requests

from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    request,
    session
)


# ==========================
# PATHS
# ==========================

BASE_DIR = Path(__file__).resolve().parent


CONFIG_FILE = BASE_DIR / "config.json"


# ==========================
# STORE DATABASE
# ==========================

try:
    import store
    store.init_db()

except Exception as e:
    print(
        f"⚠️ Erreur chargement store : {e}"
    )
    store = None



# ==========================
# FLASK
# ==========================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


app.secret_key = os.getenv(
    "FLASK_SECRET"
)


app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)


# ==========================
# ENV
# ==========================


DISCORD_CLIENT_ID = os.getenv(
    "DISCORD_CLIENT_ID"
)

DISCORD_CLIENT_SECRET = os.getenv(
    "DISCORD_CLIENT_SECRET"
)

DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "http://127.0.0.1:3000/callback"
)



# ==========================
# JSON
# ==========================


def load_json(path):

    try:

        if not path.exists():
            return {}

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception as e:

        print(
            f"⚠️ JSON {path}: {e}"
        )

        return {}




# ==========================
# DISCORD LOGIN
# ==========================


@app.route("/login")
def login():

    url = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        "&scope=identify"
    )


    return redirect(url)



@app.route("/callback")
def callback():


    code = request.args.get(
        "code"
    )


    if not code:

        return (
            "Code Discord absent",
            400
        )



    data = {

        "client_id":
            DISCORD_CLIENT_ID,

        "client_secret":
            DISCORD_CLIENT_SECRET,

        "grant_type":
            "authorization_code",

        "code":
            code,

        "redirect_uri":
            DISCORD_REDIRECT_URI

    }



    response = requests.post(

        "https://discord.com/api/oauth2/token",

        data=data,

        headers={
            "Content-Type":
            "application/x-www-form-urlencoded"
        }

    )



    token = response.json()



    if "access_token" not in token:

        return jsonify(token),400



    user_response = requests.get(

        "https://discord.com/api/users/@me",

        headers={

            "Authorization":
            f"Bearer {token['access_token']}"

        }

    )



    user = user_response.json()


    session["user"] = user



    return redirect("/")





# ==========================
# DASHBOARD
# ==========================


@app.route("/")
def dashboard():


    if "user" not in session:

        return render_template(
            "login.html"
        )



    # Tickets SQLite

    if store:

        tickets = store.get_tickets_dict()

        stats_db = store.stats_get()


        opened = stats_db.get(
            "opened",
            0
        )

        closed = stats_db.get(
            "closed",
            0
        )


    else:

        tickets = {}

        opened = 0

        closed = 0




    panels_file = BASE_DIR / "panels.json"


    panels = load_json(
        panels_file
    )



    total_panels = 0


    for value in panels.values():

        if isinstance(value,list):

            total_panels += len(value)



    stats = {


        "open":
            opened,


        "closed":
            closed,


        "panels":
            total_panels

    }



    return render_template(

        "dashboard.html",

        stats=stats,

        tickets=tickets,

        panels=panels,

        user=session["user"]

    )





# ==========================
# TICKETS PAGE
# ==========================


@app.route("/tickets")
def tickets_page():


    if store:

        tickets = store.get_tickets_dict()

    else:

        tickets = {}



    return render_template(

        "tickets.html",

        tickets=tickets

    )





# ==========================
# PANELS PAGE
# ==========================


@app.route("/panels")
def panels_page():


    panels = load_json(

        BASE_DIR / "panels.json"

    )


    return render_template(

        "panels.html",

        panels=panels

    )





# ==========================
# API
# ==========================


@app.route("/api/status")
def status():


    return jsonify({

        "status":
            "online",

        "service":
            "TicketMP Dashboard",

        "version":
            "2.0"


    })




@app.route("/api/tickets")
def api_tickets():


    if store:

        return jsonify(
            store.get_tickets_dict()
        )


    return jsonify({})





@app.route("/api/panels")
def api_panels():


    return jsonify(

        load_json(

            BASE_DIR / "panels.json"

        )

    )





# ==========================
# START DIRECT
# ==========================


if __name__ == "__main__":


    port = int(

        os.getenv(

            "PORT",

            "3000"

        )

    )


    print("==============================")
    print("🌐 TicketMP Dashboard lancé")
    print(f"📡 Port : {port}")
    print("==============================")


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False,

        use_reloader=False

    )