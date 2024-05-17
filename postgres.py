import json
import psycopg2
from psycopg2.extras import RealDictCursor


class Postgres:
    def __init__(self):
        self.conn = psycopg2.connect(
            "dbname=postgres user=postgres password=postgres host=localhost"
        )
        self.cursor = self.conn.cursor()

    def perform_get_query(self, query_name, params):
        with open("queries/" + query_name + ".sql", "r") as f:
            query = f.read()
        self.cursor.execute(query % params)
        response = self.cursor.fetchall()
        return response

    def perform_insert_or_update_query(self, query_name, params):
        with open("queries/" + query_name + ".sql", "r") as f:
            query = f.read()
        self.cursor.execute(query % params)
        self.conn.commit()

    def perform_insert_or_update_returning_query(self, query_name, params):
        with open("queries/" + query_name + ".sql", "r") as f:
            query = f.read()
        self.cursor.execute(query % params)
        response = self.cursor.fetchone()
        self.conn.commit()
        return response

    # def perform_update_query(self, query_name, params):
