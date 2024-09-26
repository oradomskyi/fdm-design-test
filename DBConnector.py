import time
import os
import logging

from dotenv import load_dotenv
import psycopg2

class DBConnector:
    def __init__(self):
        #logging.warning('DBConnector()')
        load_dotenv('.env-db') 
        self.DB_HOST = os.environ.get('DB_HOST')
        #logging.warning(self.DB_HOST)
        self.DB_NAME = os.environ.get('DB_NAME')
        #logging.warning(self.DB_NAME)
        self.DB_USER = os.environ.get('DB_USER')
        #logging.warning(self.DB_USER)
        self.DB_PASS = os.environ.get('DB_PASS')
        #logging.warning(self.DB_PASS)

    def execute_sql(self, request):
        result = None
        try:
            with  psycopg2.connect("host={} dbname={} user={} password={}".format(
                    self.DB_HOST,
                    self.DB_NAME,
                    self.DB_USER,
                    self.DB_PASS)
                ) as conn: # **config
                with  conn.cursor() as cur:
                    # execute
                    cur.execute(request)

                    try:
                        # get the generated id back                
                        rows = cur.fetchall()
                        if rows:
                            #print("Received: ", rows)
                            result = rows
                    except:
                        pass
                    
                    # commit the changes to the database
                    conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.warning(error)    
        finally:
            #print("result:", result)
            return result
