import os

from DBConnector import DBConnector

class DBLedger(DBConnector):
    def __init__(self):
        super().__init__()
        self.db_name                      = os.environ.get('DB_NAME')
        self.db_table_charges             = os.environ.get('DB_TABLE_CHARGES')
        self.db_table_grades              = os.environ.get('DB_TABLE_GRADES')
        self.db_table_moulds              = os.environ.get('DB_TABLE_MOULDS')
        self.db_table_production_monthly  = os.environ.get('DB_PRODUCTION_MONTHLY')
        self.db_table_order_forecast      = os.environ.get('DB_ORDER_FORECAST')
        self.db_table_quality_groups      = os.environ.get('DB_QUALITY_GROUPS')

    def clear_table(self, table_name):
        request = f"""DELETE FROM {table_name} RETURNING *;"""
        return self.execute_sql(request)
    
    def get_rows(self, table_name, n=None):
        if n is not None:
            request = f"""SELECT * FROM {table_name} ORDER BY id LIMIT {n};"""
        else:
            request = f"""SELECT * FROM {table_name};"""

        return self.execute_sql(request)

    def get_production_history_1_month(self, year, month):
        request = f"""SELECT * FROM {self.db_table_production_monthly} WHERE Year={year} AND Month={month};"""
        return self.execute_sql(request)
    
    def get_order_forecast_1_month(self, year, month):
        request = f"""SELECT * FROM {self.db_table_order_forecast} WHERE Year={year} AND Month={month};"""
        return self.execute_sql(request)

    def insert_row(self, table_name, table_args_dict):
        """ Insert a new coordinates into the history table """
    
        request = f"""INSERT INTO {table_name}("""

        for k, v in table_args_dict.items(): 
            request += f"{k},"

        # trim the last ','
        request = request[:-1]

        request += """) VALUES ("""
        
        for k,v in table_args_dict.items():
            request += f"{v},"

        # trim the last ','
        request = request[:-1]

        request += """) RETURNING id;"""

        return self.execute_sql(request)

    def recreate_database_Ledger(self):
    
        self.execute_sql("DROP TABLE IF EXISTS grades;")
        self.execute_sql("DROP TABLE IF EXISTS moulds;")
        self.execute_sql("DROP TABLE IF EXISTS quality_groups;")
        self.execute_sql("DROP TABLE IF EXISTS order_forecast;")
        self.execute_sql("DROP TABLE IF EXISTS charges;")
        self.execute_sql("DROP TABLE IF EXISTS production_monthly;")
        
        self.execute_sql("CREATE TABLE grades (ID SERIAL PRIMARY KEY, QualityGroupID INT NOT NULL, Name VARCHAR(128) NOT NULL);")
        self.execute_sql("CREATE TABLE moulds (ID SERIAL PRIMARY KEY, Size INT NOT NULL, Name VARCHAR(128) NOT NULL, Duration INT NOT NULL);")
        self.execute_sql("CREATE TABLE quality_groups (ID SERIAL PRIMARY KEY, Name VARCHAR(128) NOT NULL);""")
        self.execute_sql("CREATE TABLE order_forecast (ID SERIAL PRIMARY KEY, Year INT NOT NULL, Month INT NOT NULL, QualityGroupID INT NOT NULL, Heats INT NOT NULL);")
        self.execute_sql("CREATE TABLE charges (ID SERIAL PRIMARY KEY, timestamp timestamp default current_timestamp, GradeID INT NOT NULL, MouldID INT NOT NULL);")
        self.execute_sql("CREATE TABLE production_monthly (ID SERIAL PRIMARY KEY, Month INT NOT NULL, Year INT NOT NULL, GradeID INT NOT NULL, Tons INT NOT NULL);")