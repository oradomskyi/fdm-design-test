import logging
import json
import datetime
import time
from dotenv import load_dotenv
import os
import csv

from flask import current_app, Flask, render_template, request

from DBLedger import DBLedger
from GCPStorage import GCPStorage as storage
from GradeCalculator import GradeCalculator

app = Flask(__name__)

# global variables is not a great thing, better use Singletons or just pass the object reference 
db = None

load_dotenv('.env-server')
load_dotenv(os.environ.get('STORAGE_ENV'))

MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov": 11, "Dec": 12}


def get_year_month_from_list(yearmonthlist):
    year_month = []
    for v in yearmonthlist:
        if 0 == len(v):
            logging.warning("Encountered empty month")
            return year_month

        m_y = v.split(' ')
        month = MONTHS[m_y[0]]
        year = int(m_y[1])
        year_month.append([year, month])
    return year_month
    
def createDBConnector():
    try:
        global db
        if db is None:
            db = DBLedger()
            logging.warning("created DBConnector class")
    except Exception as e:
        logging.warning("Can't make database connector, is it already created?", e)

def update_ledger_order_forecast(filename):
    global db
    print(filename)
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        idx_quality_group = 0
        year_month = []
        for i, row in enumerate(reader):
            print(i, row)
            if(1 == i):
                year_month = get_year_month_from_list(row[1:])

            if(1 < i):
                quality_group = row[0]
                heats = row[1:]
                quality_group_id = -1
                if(0 < len(quality_group)):
                    # check if exists in a table
                    existing_quality_groups = db.get_rows(db.db_table_quality_groups, n=None)
                    #print(existing_quality_groups)
                    
                    if existing_quality_groups is not None:
                        for qg_id, qg_name in existing_quality_groups:
                            if quality_group in qg_name:
                                quality_group_id = qg_id
                                break
                    else:
                        logging.warning(f'Quality Group table is empty in a Ledger Database')
                        continue
                
                if -1 < quality_group_id:
                    for ym, heat in zip (year_month, heats):
                        year = ym[0]
                        month = ym[1]
                        db.insert_row(table_name=db.db_table_order_forecast,
                            table_args_dict={
                                "year":year,
                                "month":month,
                                "qualitygroupid":quality_group_id,
                                "heats":heat
                            })
                else:
                    logging.warning(f'Quality Group {quality_group} does not exist a Ledger Database')

def update_ledger_production_history(filename):
    global db
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        existing_grades = []
        existing_quality_groups = []
        year_month = []
        for i, row in enumerate(reader):
            print(i, row)

            if(1 == i):
                year_month = get_year_month_from_list(row[2:])
            
            if(1 < i):
                quality_group = row[0]
                grade = row[1]
                grade_id = -1
                tons = row[2:2+len(year_month)]

                # fill the Quality Group table
                if(0 < len(quality_group)):
                    # check if exists in a table
                    existing_quality_groups = db.get_rows(db.db_table_quality_groups, n=None)
                    #print(existing_quality_groups)
                    qg_names = []
                    if existing_quality_groups is not None:
                        qg_names = [ name for i,name in existing_quality_groups]
                    
                    if existing_quality_groups is None or quality_group not in qg_names:
                        if existing_quality_groups is None:
                            existing_quality_groups = []

                        result = db.insert_row(table_name=db.db_table_quality_groups, table_args_dict={"name":str(f'\'{quality_group}\'')})
                        #print(result, quality_group)
                        existing_quality_groups.append( [ int(result[0][0]), quality_group] )
                    else:
                        pass

                # fill Grades table 
                if(0 < len(grade)):
                    # check if exists in a table
                    existing_grades = db.get_rows(db.db_table_grades, n=None)
                    #print('existing_quality_groups', existing_quality_groups)
                    g_names = []
                    if existing_grades is not None:
                        g_names = [ name for i, qg_id, name in existing_grades]

                    if existing_grades is None or grade not in g_names:
                        if existing_grades is None:
                            existing_grades = []

                        quality_group_id = existing_quality_groups[-1][0] # ID of the last added group

                        result = db.insert_row(table_name=db.db_table_grades, table_args_dict={"QualityGroupID": quality_group_id, "name":str(f'\'{grade}\'')})
                        #print(result)
                        grade_id = int(result[0][0])
                    else:
                        grade_id += 1 # depends on the particular usage scenario, I expect this code will fail in most cases.
                
                # fill Production Monthly table
                for ym, ton in zip(year_month, tons):
                    year = ym[0]
                    month = ym[1]
                    db.insert_row(table_name=db.db_table_production_monthly,
                        table_args_dict={
                            "Month":month,
                            "Year":year,
                            "GradeID":grade_id,
                            "Tons":ton
                        })

def update_ledger_daily_schedule(filename):
    global db

    grades = db.get_rows(db.db_table_grades)
    grade_ids = {}
    for g in grades:
        grade_ids[g[2]] = g[0]

    print(f'grade_ids {grade_ids}')
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        date = []
        existing_moulds = db.get_rows(db.db_table_moulds, n=None)
        for i, row in enumerate(reader):
            print(i, row)

            if(1 == i):
                for v in row:
                    if 0 < len(v):
                        date.append(v)

                print(date)

            if(2 < i):
                i_day = 0
                i_item = 0
                while i_item < len(row):
                    if 0 == len(row[i_item]):
                        break
                    
                    print(i_item, row)
                    hh_mm      = row[i_item]
                    grade_name = row[i_item + 1]
                    mould_name = row[i_item + 2]
                    
                    grade_id = -1
                    if grade_name not in grade_ids:
                        # information in provided tables is incomplete, so I cannot load all info properly
                        i_item += 3
                        i_day += 1
                        continue    

                    print(f'grade_id {grade_id}')
                    mould_id = -1
                    if existing_moulds is not None:
                        mould_ids = {}
                        for i, size, name, duration in existing_moulds:
                            mould_ids[name] = i

                        if mould_name in mould_ids:
                            mould_id = mould_ids[mould_name]
                    else:
                        mould_id = db.insert_row(table_name=db.db_table_moulds,
                            table_args_dict={
                                "Size": 1,
                                "Name":str(f'\'{mould_name}\''),
                                "Duration": 71
                            })
                        print(mould_id)
                    
                    month, day, year = date[i_day].split(' ')[1].split('/')
                    hh, mm = hh_mm.split(':')
                    dt = datetime.datetime(int(year), int(month), int(day), int(hh), int(mm), 0, 0)
                    ts = dt.strftime(r'%Y-%m-%d %H:%M:%S')
                    result = db.insert_row(table_name=db.db_table_charges,
                            table_args_dict={
                                "timestamp": str(f'\'{ts}\''),
                                "GradeID": grade_id,
                                "MouldID": mould_id
                            })
                    print(result)           
                    i_item += 3
                    i_day += 1

def delete_local_file(filename):
    # cleanup local storage
    try:
        os.remove(filename)
    except OSError:
        pass

def upload_file(request):
    f = request.files['file']
    # save the file on a local server storage
    # big files will freeze the server, better to do it asynchronously
    f.save(f.filename)

    # upload to blob storage
    storage().upload(f.filename, os.environ.get('GCP_STORAGE_NAME'))

@app.route('/uploadDailySchedule', methods = ['POST'])
def uploadDailySchedule():
    if request.method == 'POST':
        try:
            upload_file(request)
            filename = request.files['file'].filename
            update_ledger_daily_schedule(filename)

            return render_template('index.html')
        except Exception as e:
            logging.warning(f"File savind failed:{e}")
            return """An internal error occurred: <pre>{}</pre>
                See logs for full stacktrace.""".format(e), 500

    return "Error occured", 500

@app.route('/uploadProductionHistory', methods = ['POST'])
def uploadProductionHistory():
    if request.method == 'POST':
        try:
            upload_file(request)
            filename = request.files['file'].filename
            update_ledger_production_history(filename)

            return render_template('index.html')
        except Exception as e:
            logging.warning(f"File savind failed:{e}")
            return """An internal error occurred: <pre>{}</pre>
                See logs for full stacktrace.""".format(e), 500

    return "Error occured", 500

@app.route('/uploadOrderForecast', methods = ['POST'])
def uploadOrderForecast():
    if request.method == 'POST':
        try:
            upload_file(request)
            filename = request.files['file'].filename
            update_ledger_order_forecast(filename)
            
            return render_template('index.html')
        except Exception as e:
            logging.warning(f"File savind failed:{e}")
            return """An internal error occurred: <pre>{}</pre>
                See logs for full stacktrace.""".format(e), 500

    return "Error occured", 500

@app.route('/selectAllGrades')
def selectAllGrades():
    global db
    return {"data":db.get_rows(db.db_table_grades, n=None)}

@app.route('/selectAllQualityGroups')
def selectAllQualityGroups():
    global db
    return {"data": db.get_rows(db.db_table_quality_groups, n=None)}

@app.route('/selectAllMoulds')
def selectAllMoulds():
    global db
    return {"data": db.get_rows(db.db_table_moulds, n=None)}

@app.route('/selectAllOrderForecast')
def selectAllOrderForecast():
    global db
    return {"data": db.get_rows(db.db_table_order_forecast, n=None)}

@app.route('/selectAllProductionMonthly')
def selectAllProductionMonthly():
    global db
    return {"data": db.get_rows(db.db_table_production_monthly, n=None)}

@app.route('/selectAllCharges')
def selectAllCharges():
    global db
    return {"data": db.get_rows(db.db_table_charges, n=None)}

@app.route('/clearAllGrades')
def clearAllGrades():
    global db
    db.clear_table(db.db_table_grades)
    return render_template('index.html')

@app.route('/clearAllQualityGroups')
def clearAllQualityGroups():
    global db
    db.clear_table(db.db_table_quality_groups)
    return render_template('index.html')

@app.route('/clearAllMoulds')
def clearAllMoulds():
    global db
    db.clear_table(db.db_table_moulds)
    return render_template('index.html')

@app.route('/clearAllOrderForecast')
def clearAllOrderForecast():
    global db
    db.clear_table(db.db_table_order_forecast)
    return render_template('index.html')

@app.route('/clearAllProductionMonthly')
def clearAllProductionMonthly():
    global db
    db.clear_table(db.db_table_production_monthly)
    return render_template('index.html')

@app.route('/clearAllCharges')
def clearAllCharges():
    global db
    db.clear_table(db.db_table_charges)
    return render_template('index.html')

@app.route('/recreateDatabaseLedger')
def recreateDatabaseLedger():
    global db
    db.recreate_database_Ledger()
    return render_template('index.html')

def createStorage():
    # I know that this is not the best way to init the singleton, 
    # but is ok for now because this is TEST environment
    s = storage()
    s.setup(os.environ.get('STORAGE_ENV'))

@app.route('/predictSeptember24')
def predictSeptember24():
    global db
    gc = GradeCalculator(db)
    data = gc.getGradesEstimate(year=24, month=9)
    return {'data':data}

@app.route("/")
def main():
    createStorage()
    createDBConnector()
    return render_template('index.html', model={"title": "FDM API Test"})

if __name__ == "__main__":
    # http is only for demo test purposes, https is obligatory for production.
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
