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


# ==================================================
# PATH
# ==================================================

BASE_DIR = Path(__file__).resolve().parent



# ==================================================
# DATABASE STORE
# ==================================================

try:
    import store
    store.init_db()

except Exception as e:
    print("⚠️ Store erreur :", e)
    store = None



# ==================================================
# FLASK
# ==================================================

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



# ==================================================
# DISCORD CONFIG
# ==================================================

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




# ==================================================
# JSON
# ==================================================

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
            "JSON erreur:",
            e
        )

        return {}





# ==================================================
# DISCORD API
# ==================================================

def discord_get(url, token):

    try:

        response = requests.get(

            url,

            headers={

                "Authorization":
                f"Bearer {token}"

            },

            timeout=10

        )


        if response.status_code != 200:

            print(
                "Discord API:",
                response.text
            )

            return None


        return response.json()



    except Exception as e:

        print(
            "Discord request erreur:",
            e
        )

        return None






def get_user_guilds(token):

    data = discord_get(

        "https://discord.com/api/users/@me/guilds",

        token

    )


    return data or []





def format_guild(guild):


    permissions = int(

        guild.get(
            "permissions",
            0
        )

    )



    owner = guild.get(
        "owner",
        False
    )


    admin = bool(
        permissions & 8
    )


    manage = bool(
        permissions & 32
    )



    return {


        "id":
        guild.get("id"),



        "name":
        guild.get(
            "name",
            "Serveur"
        ),



        "icon":
        guild.get(
            "icon"
        ),



        "owner":
        owner,


        "administrator":
        admin,


        "manage":
        manage,


        "can_manage":
        (
            owner
            or
            admin
            or
            manage
        )

    }





# ==================================================
# LOGIN DISCORD
# ==================================================

@app.route("/login")
def login():


    params = {


        "client_id":
        DISCORD_CLIENT_ID,


        "response_type":
        "code",


        "redirect_uri":
        DISCORD_REDIRECT_URI,


        "scope":
        "identify guilds"

    }



    return redirect(

        "https://discord.com/oauth2/authorize?"

        +

        urlencode(params)

    )





# ==================================================
# CALLBACK
# ==================================================

@app.route("/callback")
def callback():


    code = request.args.get(
        "code"
    )


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
            DISCORD_REDIRECT_URI

        },


        timeout=10

    )



    token = token_request.json()



    if "access_token" not in token:

        return jsonify(token),400




    access_token = token["access_token"]





    user = discord_get(

        "https://discord.com/api/users/@me",

        access_token

    )



    if not user:

        return "Erreur utilisateur Discord",400




    session.clear()



    session["user"] = {


        "id":
        user["id"],


        "username":
        user["username"],


        "avatar":
        user.get("avatar")


    }





    servers=[]


    for guild in get_user_guilds(access_token):


        data = format_guild(
            guild
        )


        if data["can_manage"]:

            servers.append(
                data
            )




    session["guilds"] = servers


    session.permanent=True



    print(
        f"✅ Connexion : {user['username']}"
    )


    print(
        f"🏠 Serveurs : {len(servers)}"
    )



    return redirect("/servers")





# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")






# ==================================================
# SERVERS
# ==================================================

@app.route("/servers")
def servers():


    if "user" not in session:

        return redirect("/login")



    return render_template(

        "servers.html",

        user=session["user"],

        guilds=session.get(
            "guilds",
            []
        )

    )






@app.route("/server/<guild_id>")
def server_manage(guild_id):


    if "user" not in session:

        return redirect("/login")



    guild = next(

        (
            g
            for g in session.get(
                "guilds",
                []
            )

            if g["id"] == guild_id

        ),

        None

    )



    if not guild:

        return "Serveur inaccessible",403



    return render_template(

        "server.html",

        user=session["user"],

        guild=guild

    )







# ==================================================
# DASHBOARD
# ==================================================

@app.route("/")
def dashboard():


    if "user" not in session:

        return render_template(
            "login.html"
        )



    opened=0
    closed=0
    tickets={}



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

        BASE_DIR /
        "panels.json"

    )



    total_panels=sum(

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

            "open":opened,

            "closed":closed,

            "panels":total_panels

        }

    )






# ==================================================
# PAGES
# ==================================================

@app.route("/tickets")
def tickets_page():

    if "user" not in session:

        return redirect("/login")



    return render_template(

        "tickets.html",

        tickets=

        store.get_tickets_dict()

        if store

        else {}

    )





@app.route("/panels")
def panels_page():


    if "user" not in session:

        return redirect("/login")



    return render_template(

        "panels.html",

        panels=load_json(

            BASE_DIR /
            "panels.json"

        )

    )






# ==================================================
# API
# ==================================================

@app.route("/api/status")
def api_status():

    return jsonify({

        "status":"online",

        "service":"TicketMP",

        "version":"4.0"

    })





@app.route("/api/session")
def api_session():

    return jsonify(
        dict(session)
    )





@app.route("/api/tickets")
def api_tickets():

    return jsonify(

        store.get_tickets_dict()

        if store

        else {}

    )





@app.route("/api/panels")
def api_panels():

    return jsonify(

        load_json(

            BASE_DIR /
            "panels.json"

        )

    )






# ==================================================
# START
# ==================================================

if __name__=="__main__":


    port=int(

        os.getenv(
            "PORT",
            3000
        )

    )



    print("==============================")
    print("🎫 TicketMP Dashboard")
    print(f"🌐 Port : {port}")
    print("==============================")



    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )