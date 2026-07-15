import sqlite3
import os


# ==================================================
# DATABASE CONFIG
# ==================================================

DATABASE_PATH = "data/ticketmp.db"



# ==================================================
# CONNECTION
# ==================================================

def get_db():

    os.makedirs(
        "data",
        exist_ok=True
    )


    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )


    conn.row_factory = sqlite3.Row


    # Performance SQLite
    conn.execute(
        "PRAGMA journal_mode=WAL;"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON;"
    )


    return conn





# ==================================================
# CREATE TABLES
# ==================================================

def create_tables():


    db = get_db()


    try:


        db.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_config (

            guild_id TEXT PRIMARY KEY,


            -- Tickets

            ticket_category TEXT DEFAULT NULL,

            ticket_log_channel TEXT DEFAULT NULL,

            ticket_staff_role TEXT DEFAULT NULL,

            ticket_message TEXT DEFAULT 
            'Cliquez sur le bouton pour ouvrir un ticket',



            -- Panel

            panel_channel TEXT DEFAULT NULL,

            panel_message TEXT DEFAULT 
            'Support TicketMP',



            -- General

            language TEXT DEFAULT 'fr',

            color TEXT DEFAULT '#5865F2',



            -- Security

            anti_raid INTEGER DEFAULT 0,

            anti_spam INTEGER DEFAULT 0,

            automod INTEGER DEFAULT 0,



            -- Logs

            logs INTEGER DEFAULT 0,

            log_channel TEXT DEFAULT NULL,



            -- Notifications

            notifications INTEGER DEFAULT 1,

            notification_channel TEXT DEFAULT NULL,



            -- Custom

            bot_name TEXT DEFAULT 'TicketMP',

            embed_footer TEXT DEFAULT 
            'TicketMP Dashboard',



            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
        )


        db.commit()


    except Exception as e:

        print(
            "❌ Database error:",
            e
        )


    finally:

        db.close()






# ==================================================
# CREATE SERVER CONFIG
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
            guild_id,
        )
        )


        db.commit()



    finally:

        db.close()







# ==================================================
# GET SERVER CONFIG
# ==================================================

def get_guild_config(guild_id):


    create_guild_config(
        guild_id
    )


    db=get_db()


    config=db.execute(
    """
    SELECT *

    FROM guild_config

    WHERE guild_id=?

    """,
    (
        guild_id,
    )
    ).fetchone()



    db.close()


    return config






# ==================================================
# UPDATE CONFIG
# ==================================================

def update_guild_config(
    guild_id,
    **kwargs
):


    if not kwargs:
        return



    db=get_db()



    fields=[]

    values=[]



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
        guild_id
    )



    query=f"""
    UPDATE guild_config

    SET {",".join(fields)}

    WHERE guild_id=?

    """



    try:


        db.execute(
            query,
            values
        )


        db.commit()



    finally:

        db.close()