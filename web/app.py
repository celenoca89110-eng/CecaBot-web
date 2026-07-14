import json
import os
from pathlib import Path
from flask import Flask, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent

TICKETS_JSON_FILE = BASE_DIR.parent / "tickets.json"
PANELS_JSON_FILE = BASE_DIR.parent / "panels.json"
CONFIG_JSON_FILE = BASE_DIR.parent / "config.json"

app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True


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

        return {}

    except Exception as e:
        print(f"❌ Erreur lecture {path}: {e}")
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

    except Exception as e:
        print(f"❌ Erreur sauvegarde {path}: {e}")


def ticket_counts(tickets: dict):

    open_count = 0
    closed_count = 0

    for ticket in tickets.values():

        if (
            isinstance(ticket, dict)
            and ticket.get("closed")
        ):
            closed_count += 1
        else:
            open_count += 1

    return open_count, closed_count


def count_panels(panels: dict):

    total = 0

    for value in panels.values():

        if isinstance(value, list):
            total += len(value)

        elif isinstance(value, dict):
            total += 1

    return total


@app.route("/")
def dashboard():

    tickets = load_json(
        TICKETS_JSON_FILE
    )

    panels = load_json(
        PANELS_JSON_FILE
    )

    config = load_json(
        CONFIG_JSON_FILE
    )

    open_count, closed_count = (
        ticket_counts(tickets)
    )

    stats = {
        "open_tickets": open_count,
        "closed_tickets": closed_count,
        "panels": count_panels(
            panels
        ),
        "guilds": len(
            config.get(
                "guilds",
                {}
            )
        )
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        tickets=tickets,
        panels=panels,
        config=config
    )


@app.route("/tickets")
def tickets_page():

    tickets = load_json(
        TICKETS_JSON_FILE
    )

    return render_template(
        "tickets.html",
        tickets=tickets
    )


@app.route("/panels")
def panels_page():

    panels = load_json(
        PANELS_JSON_FILE
    )

    return render_template(
        "panels.html",
        panels=panels
    )


@app.route("/api/stats")
def api_stats():

    tickets = load_json(
        TICKETS_JSON_FILE
    )

    panels = load_json(
        PANELS_JSON_FILE
    )

    config = load_json(
        CONFIG_JSON_FILE
    )

    open_count, closed_count = (
        ticket_counts(tickets)
    )

    return jsonify(
        {
            "success": True,
            "stats": {
                "tickets_open":
                    open_count,

                "tickets_closed":
                    closed_count,

                "panels":
                    count_panels(
                        panels
                    ),

                "guilds":
                    len(
                        config.get(
                            "guilds",
                            {}
                        )
                    )
            }
        }
    )


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


@app.route("/api/config")
def api_config():

    return jsonify(
        load_json(
            CONFIG_JSON_FILE
        )
    )


@app.route("/api/health")
def health():

    return jsonify(
        {
            "success": True,
            "status": "online"
        }
    )


@app.errorhandler(404)
def not_found(_):

    return jsonify(
        {
            "success": False,
            "error": "Page introuvable"
        }
    ), 404


@app.errorhandler(500)
def internal_error(error):

    print(error)

    return jsonify(
        {
            "success": False,
            "error": "Erreur interne"
        }
    ), 500


if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            3000
        )
    )

    host = os.getenv(
        "FLASK_HOST",
        "0.0.0.0"
    )

    print("================================")
    print("🌐 Dashboard TicketMP")
    print(f"Host : {host}")
    print(f"Port : {port}")
    print("================================")

    app.run(
        host=host,
        port=port,
        debug=True
    )