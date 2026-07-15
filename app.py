import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template


# ==========================
# CONFIG
# ==========================

BASE_DIR = Path(__file__).resolve().parent

TICKETS_JSON_FILE = BASE_DIR / "tickets.json"
PANELS_JSON_FILE = BASE_DIR / "panels.json"


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ==========================
# JSON SYSTEM
# ==========================

def load_json(path: Path) -> dict:

    try:

        if not path.exists():
            return {}

        content = path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            return {}

        data = json.loads(content)

        if isinstance(data, dict):
            return data

    except Exception as e:

        print(
            f"⚠️ Erreur lecture JSON {path}: {e}"
        )

    return {}



def save_json(path: Path, data: dict):

    try:

        path.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        return True

    except Exception as e:

        print(
            f"❌ Erreur sauvegarde {path}: {e}"
        )

        return False



# ==========================
# STATS
# ==========================

def ticket_counts(tickets: dict):

    opened = 0
    closed = 0

    for ticket in tickets.values():

        if isinstance(ticket, dict):

            if ticket.get("closed"):
                closed += 1

            else:
                opened += 1

    return opened, closed



def count_panels(panels: dict):

    total = 0

    for value in panels.values():

        if isinstance(value, list):
            total += len(value)

    return total



# ==========================
# WEB DASHBOARD
# ==========================

@app.route("/")
def dashboard():

    tickets = load_json(
        TICKETS_JSON_FILE
    )

    panels = load_json(
        PANELS_JSON_FILE
    )


    opened, closed = ticket_counts(
        tickets
    )


    stats = {

        "tickets_open": opened,

        "tickets_closed": closed,

        "panels": count_panels(
            panels
        ),

    }


    return render_template(
        "dashboard.html",
        stats=stats,
        tickets=tickets,
        panels=panels
    )



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



# ==========================
# API
# ==========================

@app.route("/api/status")
def api_status():

    return jsonify({

        "status": "online",

        "service": "TicketMP Dashboard",

        "version": "1.0"

    })



@app.route("/api/tickets")
def api_tickets():

    return jsonify(
        load_json(
            TICKETS_JSON_FILE
        )
    )



@app.route("/api/panels")
def api_panels():

    return jsonify(
        load_json(
            PANELS_JSON_FILE
        )
    )



# ==========================
# START SOLO
# ==========================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "3000"
        )
    )


    print(
        "🌐 TicketMP Dashboard lancé"
    )

    print(
        f"📡 Port : {port}"
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )