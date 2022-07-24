"""
    _summary_
    Singleton connection to the Database. Used across the system to limit the flow. Since the database is
    run by the program there should only ever be one thing accessing it anyway.
    Modules are singleton by default so we can skip the classes and just define the connection
"""
import sqlite3

connection = sqlite3.connect('kiraBotFiles\kiraDB.db')