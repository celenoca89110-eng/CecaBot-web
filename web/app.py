import json
import os
from pathlib import Path

import requests

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    session,
    redirect
)

from config import get_user_role


# =========================
# APP
# =========================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "dev-secret-change"
)

app.config["JSON_SORT_KEYS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True



# =========================
# DISCORD OAUTH
# =========================

DISCORD_CLIENT_ID = os.getenv(
    "DISCORD_CLIENT_ID"
)

DISCORD_CLIENT_SECRET = os.getenv(
    "DISCORD_CLIENT_SECRET"
)


DISCORD_REDIRECT = os.getenv(
    "DISCORD_REDIRECT",
    "https://cecabot-web.onrender.com/callback"
)



# =========================
# FILES
# =========================

BASE_DIR = Path(__file__).resolve().parent


TICKETS_JSON_FILE = (
    BASE_DIR.parent / "tickets.json"
)

PANELS_JSON_FILE = (
    BASE_DIR.parent / "panels.json"
)

CONFIG_JSON_FILE = (
    BASE_DIR.parent / "config.json"
)



# =========================
# LOGIN DISCORD
# =========================


@app.route("/login")
def login():

    url = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={DISCORD_REDIRECT}"
        "&scope=identify%20guilds"
    )


    return redirect(url)



@app.route("/callback")
def callback():

    code = request.args.get("code")


    if not code:
        return "Code Discord absent",400


    token_request = requests.post(

        "https://discord.com/api/oauth2/token",

        data={

            "client_id":
            DISCORD_CLIENT_ID,

            "client_secret":
            DISCORD_CLIENT_SECRET,

            "grant_type":
            "authorization_code",

            "code":
            code,

            "redirect_uri":
            DISCORD_REDIRECT
        },

        headers={

            "Content-Type":
            "application/x-www-form-urlencoded"

        }

    )


    token = token_request.json()


    if "access_token" not in token:

        return "Erreur OAuth Discord",400



    headers={

        "Authorization":
        f"Bearer {token['access_token']}"

    }



    user = requests.get(

        "https://discord.com/api/users/@me",

        headers=headers

    ).json()



    guilds = requests.get(

        "https://discord.com/api/users/@me/guilds",

        headers=headers

    ).json()



    discord_id = int(
        user["id"]
    )


    role = get_user_role(
        discord_id
    )



    session["user"] = {

        "id":
        discord_id,


        "username":
        user.get(
            "global_name",
            user["username"]
        ),


        "avatar":
        user.get("avatar"),


        "role":
        role,


        "guilds":
        guilds

    }



    return redirect("/")




# =========================
# JSON
# =========================


def load_json(path):

    try:

        if not path.exists():
            return {}


        data=json.loads(

            path.read_text(
                encoding="utf-8"
            )

        )


        if isinstance(data,dict):

            return data


        return {}


    except Exception as e:

        print(
            "Erreur JSON:",
            e
        )

        return {}




def ticket_counts(tickets):

    opened=0
    closed=0


    for ticket in tickets.values():

        if isinstance(ticket,dict):

            if ticket.get("closed"):

                closed+=1

            else:

                opened+=1


    return opened,closed




def count_panels(panels):

    total=0


    for value in panels.values():

        if isinstance(value,list):

            total+=len(value)


        elif isinstance(value,dict):

            total+=1


    return total




# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():

    user = session.get("user")

    # Connexion Discord obligatoire
    if not user:
        return redirect("/login")


    tickets = load_json(
        TICKETS_JSON_FILE
    )


    panels = load_json(
        PANELS_JSON_FILE
    )


    config = load_json(
        CONFIG_JSON_FILE
    )


    opened, closed = ticket_counts(
        tickets
    )


    stats = {

        "open": opened,

        "closed": closed,

        "panels": count_panels(
            panels
        )

    }


    return render_template(

        "dashboard.html",

        user=user,

        stats=stats,

        tickets=tickets,

        panels=panels,

        config=config

    )

# =========================
# PAGES
# =========================


@app.route("/tickets")
def tickets_page():

    return render_template(

        "tickets.html",

        tickets=load_json(
            TICKETS_JSON_FILE
        )

    )



@app.route("/panels")
def panels_page():

    return render_template(

        "panels.html",

        panels=load_json(
            PANELS_JSON_FILE
        )

    )




@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")




# =========================
# API
# =========================


@app.route("/api/health")
def health():

    return jsonify({

        "status":
        "online",

        "service":
        "TicketMP"

    })




@app.errorhandler(404)
def not_found(e):

    return jsonify({

        "error":
        "Page introuvable"

    }),404





if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                3000
            )
        )

    )