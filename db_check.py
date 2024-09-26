import time
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv('.env-db') 
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

try:
    conn = psycopg2.connect(f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS}")
    
    print("Connected:", conn)
    conn.close()
except psycopg2.OperationalError as ex:
    print("Connection failed: {0}".format(ex))


'''

DROP TABLE grades;
DROP TABLE moulds;
DROP TABLE quality_groups;
DROP TABLE order_forecast;
DROP TABLE charges;
DROP TABLE production_monthly;

CREATE TABLE grades (
  ID SERIAL PRIMARY KEY, 
  QualityGroupID INT NOT NULL,
  Name VARCHAR(128) NOT NULL
);

CREATE TABLE moulds (
  ID SERIAL PRIMARY KEY, 
  Size INT NOT NULL,
  Name VARCHAR(128) NOT NULL,
  Duration INT NOT NULL
);

CREATE TABLE quality_groups (
  ID SERIAL PRIMARY KEY, 
  Name VARCHAR(128) NOT NULL
);

CREATE TABLE order_forecast (
  ID SERIAL PRIMARY KEY, 
  Year INT NOT NULL,
  Month INT NOT NULL,
  QualityGroupID INT NOT NULL,
  Heats INT NOT NULL
);

CREATE TABLE charges (
  ID SERIAL PRIMARY KEY,
  timestamp timestamp default current_timestamp,
  GradeID INT NOT NULL,
  MouldID INT NOT NULL
);

CREATE TABLE production_monthly (
  ID SERIAL PRIMARY KEY,
  Month INT NOT NULL,
  Year INT NOT NULL,
  GradeID INT NOT NULL,
  Tons INT NOT NULL
);

'''