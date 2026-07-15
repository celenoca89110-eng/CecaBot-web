import os
import json
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlencode

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


# ==========================
# STORE DATABASE
# ==========================

try:
    import store
    store.init_db()

except Exception as e:
    print(f"⚠️ Erreur store : {e}")
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
    "FLASK_SECRET",
    "change-moi-cette-cle"
)


app.config.update(

    SESSION_COOKIE_NAME="ticketmp_session",

    SESSION_COOKIE_HTTPONLY=True,

    SESSION_COOKIE_SECURE=True,

    SESSION_COOKIE_SAMESITE="None",

    PERMANENT_SESSION_LIFETIME=timedelta(days=7)

)



# ==========================
# ENV DISCORD
# ==========================

DISCORD_CLIENT_ID = os.getenv(
    "DISCORD_CLIENT_ID"
)

DISCORD_CLIENT_SECRET = os.getenv(
    "DISCORD_CLIENT_SECRET"
)


DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://cecabot-web.onrender.com/callback"
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
            f"⚠️ JSON erreur {path}: {e}"
        )

        return {}



# ==========================
# AUTH DISCORD
# ==========================


@app.route("/login")
def login():

    params = {

        "client_id": DISCORD_CLIENT_ID,

        "response_type": "code",

        "redirect_uri": DISCORD_REDIRECT_URI,

        "scope": "identify guilds"

    }


    url = (
        "https://discord.com/oauth2/authorize?"
        + urlencode(params)
    )


    return redirect(url)



@app.route("/callback")
def callback():

    code = request.args.get("code")


    if not code:

        return "Code Discord absent",400



    token_response = requests.post(

        "https://discord.com/api/oauth2/token",

        data={

            "client_id": DISCORD_CLIENT_ID,

            "client_secret": DISCORD_CLIENT_SECRET,

            "grant_type": "authorization_code",

            "code": code,

            "redirect_uri": DISCORD_REDIRECT_URI

        },

        headers={

            "Content-Type":
            "application/x-www-form-urlencoded"

        }

    )


    token = token_response.json()


    if "access_token" not in token:

        print(token)

        return jsonify(token),400



    user_response = requests.get(

        "https://discord.com/api/users/@me",

        headers={

            "Authorization":
            f"Bearer {token['access_token']}"

        }

    )


    user = user_response.json()



    session.clear()



session["user"] = {

    "id": str(user["id"]),

    "username": user["username"],

    "avatar": user.get("avatar")

}



# ==========================
# SERVEURS DISCORD
# ==========================


def get_user_guilds(access_token):

    try:

        response = requests.get(

            "https://discord.com/api/users/@me/guilds",

            headers={

                "Authorization":
                f"Bearer {access_token}"

            },

            timeout=10

        )


        if response.status_code != 200:

            print(
                "❌ Erreur Discord Guilds:",
                response.text
            )

            return []


        return response.json()



    except Exception as e:

        print(
            "❌ Erreur récupération serveurs:",
            e
        )

        return []





def format_guild(guild):


    permissions = int(
        guild.get(
            "permissions",
            0
        )
    )



    is_admin = bool(
        permissions & 0x8
    )


    can_manage = bool(
        permissions & 0x20
    )



    return {


        "id":
        guild.get("id"),



        "name":
        guild.get(
            "name",
            "Serveur inconnu"
        ),



        "icon":
        guild.get("icon"),



        "owner":
        guild.get(
            "owner",
            False
        ),



        "permissions":
        permissions,



        "administrator":
        is_admin,



        "can_manage":
        (
            can_manage
            or
            is_admin
            or
            guild.get(
                "owner",
                False
            )
        )

    }




# ==========================
# CALLBACK DISCORD
# ==========================


@app.route("/callback")
def callback():


    code = request.args.get(
        "code"
    )


    if not code:

        return "Code Discord manquant",400



    # Ici tu gardes ton échange OAuth
    # token = requests.post(...)



    access_token = token["access_token"]



    # Sauvegarde utilisateur

    session["user"] = user_data




    # ==========================
    # SERVEURS DISCORD
    # ==========================


    guilds = get_user_guilds(
        access_token
    )



    available_servers = []



    for guild in guilds:


        data = format_guild(
            guild
        )


        if data["can_manage"]:

            available_servers.append(
                data
            )




    session["guilds"] = available_servers


    session.permanent = True




    print(
        f"✅ Connexion Discord : {session['user']['username']}"
    )


    print(
        f"🏠 Serveurs accessibles : {len(available_servers)}"
    )



    return redirect(
        "/servers"
    )







# ==========================
# SERVERS
# ==========================


@app.route("/servers")
def servers():


    if "user" not in session:

        return redirect(
            "/login"
        )



    return render_template(

        "servers.html",

        user=session["user"],

        guilds=session.get(
            "guilds",
            []
        )

    )



# ==========================
# DASHBOARD
# ==========================


@app.route("/")
def dashboard():


    if "user" not in session:

        return render_template(
            "login.html"
        )


    tickets = {}

    opened = 0

    closed = 0



    if store:

        tickets = store.get_tickets_dict()

        stats = store.stats_get()


        opened = stats.get(
            "opened",
            0
        )

        closed = stats.get(
            "closed",
            0
        )



    panels = load_json(
        BASE_DIR / "panels.json"
    )


    total_panels = sum(

        len(v)

        for v in panels.values()

        if isinstance(v,list)

    )



    return render_template(

        "dashboard.html",

        user=session["user"],

        tickets=tickets,

        panels=panels,

        stats={

            "open": opened,

            "closed": closed,

            "panels": total_panels

        }

    )



# ==========================
# PAGES
# ==========================


@app.route("/tickets")
def tickets_page():

    if "user" not in session:

        return redirect("/login")


    tickets = (

        store.get_tickets_dict()

        if store

        else {}

    )


    return render_template(

        "tickets.html",

        tickets=tickets

    )



@app.route("/panels")
def panels_page():

    if "user" not in session:

        return redirect("/login")


    return render_template(

        "panels.html",

        panels=load_json(
            BASE_DIR / "panels.json"
        )

    )



# ==========================
# API
# ==========================


@app.route("/api/status")
def api_status():

    return jsonify({

        "status":"online",

        "service":"TicketMP Dashboard",

        "version":"3.0"

    })



@app.route("/api/session")
def api_session():

    return jsonify(
        dict(session)
    )



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
# START
# ==========================


if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "3000"
        )
    )


    print("==============================")
    print("🌐 TicketMP Dashboard")
    print(f"📡 Port : {port}")
    print("==============================")


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )