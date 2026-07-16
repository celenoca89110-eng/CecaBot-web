import sqlite3
import os
from pathlib import Path


# ==================================================
# DATABASE CONFIG
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    exist_ok=True
)


DATABASE_PATH = DATA_DIR / "ticketmp.db"



# ==================================================
# CONNECTION
# ==================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=15,
        check_same_thread=False
    )


    conn.row_factory = sqlite3.Row


    # Optimisation SQLite

    conn.execute(
        "PRAGMA journal_mode=WAL;"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON;"
    )

    conn.execute(
        "PRAGMA synchronous=NORMAL;"
    )


    return conn



# ==================================================
# CREATE TABLES
# ==================================================

def create_tables():

    db = get_db()

    try:


        # ==================================================
        # GUILD CONFIG
        # ==================================================

        db.execute("""
        CREATE TABLE IF NOT EXISTS guild_config (

            guild_id TEXT PRIMARY KEY,


            -- TICKETS

            ticket_category TEXT,

            ticket_log_channel TEXT,

            ticket_staff_role TEXT,

            ticket_message TEXT DEFAULT 
            'Cliquez sur le bouton pour ouvrir un ticket',



            -- PANEL

            panel_channel TEXT,

            panel_message TEXT DEFAULT 
            'Support TicketMP',



            -- GENERAL

            language TEXT DEFAULT 'fr',

            color TEXT DEFAULT '#5865F2',



            -- SECURITY

            anti_raid INTEGER DEFAULT 0,

            anti_spam INTEGER DEFAULT 0,

            automod INTEGER DEFAULT 0,



            -- LOGS GENERAL

            logs INTEGER DEFAULT 0,

            log_channel TEXT,



            -- NOTIFICATIONS

            notifications INTEGER DEFAULT 1,

            notification_channel TEXT,



            -- CUSTOM

            bot_name TEXT DEFAULT 'TicketMP',

            embed_footer TEXT DEFAULT 
            'TicketMP Dashboard',



            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP

        )
        """)



        # ==================================================
        # GUILD LOGS CONFIGURATION
        # ==================================================

        db.execute("""
        CREATE TABLE IF NOT EXISTS guild_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            guild_id TEXT NOT NULL,

            log_type TEXT NOT NULL,

            enabled INTEGER DEFAULT 0,

            channel_id TEXT DEFAULT NULL,


            UNIQUE(guild_id, log_type)

        )
        """)



        db.commit()


        print(
            "✅ Database initialized"
        )


    except sqlite3.Error as e:

        print(
            "❌ Database creation error:",
            e
        )


    finally:

        db.close()


# ==================================================
# CREATE GUILD CONFIG
# ==================================================

def create_guild_config(guild_id):

    db = get_db()

    try:

        db.execute(
        """
        INSERT OR IGNORE INTO guild_config
        (
            guild_id
        )
        VALUES
        (?)

        """,
        (
            str(guild_id),
        )
        )


        db.commit()


    except sqlite3.Error as e:

        print(
            "❌ Create guild error:",
            e
        )


    finally:

        db.close()



# ==================================================
# GET SERVER CONFIG
# ==================================================

def get_guild_config(guild_id):


    create_guild_config(
        guild_id
    )


    db = get_db()


    try:

        config = db.execute(
        """
        SELECT *

        FROM guild_config

        WHERE guild_id=?

        """,
        (
            str(guild_id),
        )
        ).fetchone()


        return config


    finally:

        db.close()



# ==================================================
# UPDATE CONFIG
# ==================================================

ALLOWED_FIELDS = {

    "ticket_category",
    "ticket_log_channel",
    "ticket_staff_role",
    "ticket_message",

    "panel_channel",
    "panel_message",

    "language",
    "color",

    "anti_raid",
    "anti_spam",
    "automod",

    "logs",
    "log_channel",

    "notifications",
    "notification_channel",

    "bot_name",
    "embed_footer"

}



def update_guild_config(
    guild_id,
    **kwargs
):


    if not kwargs:
        return False



    # Sécurité
    kwargs = {
        key:value
        for key,value in kwargs.items()
        if key in ALLOWED_FIELDS
    }



    if not kwargs:
        return False



    db = get_db()


    try:

        fields = []

        values = []


        for key,value in kwargs.items():

            fields.append(
                f"{key}=?"
            )

            values.append(
                value
            )


        fields.append(
            "updated_at=CURRENT_TIMESTAMP"
        )


        values.append(
            str(guild_id)
        )


        query = f"""
        UPDATE guild_config

        SET {",".join(fields)}

        WHERE guild_id=?

        """


        db.execute(
            query,
            values
        )


        db.commit()


        return True



    except sqlite3.Error as e:

        print(
            "❌ Update error:",
            e
        )

        return False



    finally:

        db.close()



# ==================================================
# INITIALIZATION
# ==================================================

def init_database():

    create_tables()

