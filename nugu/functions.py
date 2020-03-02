from flask import Flask
from flask_restful import Resource, Api
from flaskext.mysql import MySQL
from datetime import date, datetime, time,timedelta
from tmslive import *

mysql = MySQL()
app = Flask(__name__)
api = Api(app)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'tms'
app.config['MYSQL_DATABASE_HOST'] = ''
app.config['MYSQL_DATABASE_PORT'] = 3306

mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor()
#엑세스 토큰으로 부터 이메일 가져오기
def getemail(access_token):
    data = {
        'property_keys': '["kakao_account.email"]'
    }
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache"
    }
    url = "https://kapi.kakao.com/v1/user/me"
    headers.update({'Authorization': 'Bearer ' + str(access_token)})
    response = requests.request("POST", url, headers = headers, data = data)
    result = json.loads(((response.text).encode('utf-8')))
    email = result['kaccount_email']
    return email

#게임인지 확인
def isgaming(email):
    sql = "SELECT * FROM game_log WHERE token='%s';" % (email)
    cursor.execute(sql)
    datas = cursor.fetchall()
    if(len(datas) == 0):
        return False
    data = datas[len(datas) - 1]
    if(data[2] == 'start'):
        return True
    else:
        return False

#Timestamp 몇시간 몇분으로 바꿔줌
def timestampToString(stamp):
    hour = int(stamp / 1000 / 60 / 60)
    minute = int(stamp / 1000 / 60 % 60)
    return hour + " 시간 " + minute + "분"

#공부중인지 체크
def isstudy(email):
    sql = "SELECT * FROM study_log WHERE token='%s';" % (email)
    cursor.execute(sql)
    datas = cursor.fetchall()

    if (len(datas) == 0):
        return False
    data = datas[len(datas) - 1]

    if (data[2] == 'start'):
        return True
    else:
        return False

# @param dates    그 주 월요일
# @param email    이메일
# @param type     테이블 이름
# 그주 시간 전부다 가져옴
def getWeekTime(email, dates, type):
    total = 0
    cal = dates
    for i in range(0,6):
        cal = cal + timedelta(days=i)
        sql = "SELECT * FROM %s WHERE token='%s' AND date='%s';" % (type, email, cal.strftime('%Y-%m-%d'))
        cursor.execute(sql)
        datas = cursor.fetchall()
        
        if (len(datas) == 0):
            continue

        for data in datas:
            total += data[5].timestamp()
    return total


# @param date     날자 (date형)
# @param email    이메일
# @param type     테이블 이름
# 그날 시간을 전부다 가져옴
def getDayTime(email, date, type):
    total = 0
    sql = "SELECT * FROM %s WHERE token='%s' AND date='%s';" % (type, email, date.strftime('%Y-%m-%d'))
    cursor.execute(sql)
    datas = cursor.fetchall()

    if(len(datas)):
        return 0

    for data in datas:
        total += data[5].timestamp()
    return total


# @param date     날자 (date형)
# @param email    이메일
# @param type     테이블 이름
# @param value    월요일 부터 값
# 월요일 부터 value 만큼 지난 일까지 시간 다 더함
def getWeekToTime(email, dates, type, value):
    total = 0
    cal = dates
    for i in range(0, value - 1):
        cal = cal + timedelta(days=i)
        sql = "SELECT * FROM %s WHERE token='%s' AND date='%s';" % (type, email, cal.strftime('%Y-%m-%d'))
        cursor.execute(sql)
        datas = cursor.fetchall()

        if ( len(datas) == 0):
            continue

        for data in datas:
            total += data[5].timestamp()
    return total
def SecondStudyLogToStudy(email):
    sql = "SELECT studydate FROM second_study_log WHERE email='%s' ORDER BY studydate DESC LIMIT 2;" %  (email)
    cursor.execute(sql)
    data = cursor.fetchall()
    
    print(data)

    start = data[0][0]
    #print(start)
    end = data[1][0]
    #print(end)
    delta = start - end
    #print(delta) 
    if end.date() == start.date():
        sql = "SELECT time FROM study_log WHERE email='%s' AND day=subdate(current_date, 0);"  % (email)
        cursor.execute(sql)
        data = cursor.fetchone()

        if cursor.rowcount > 0:
            sql = "UPDATE study_log SET time = '%s' WHERE email='%s' AND day=subdate(current_date, 0);" % (data[0]+delta,email)
            cursor.execute(sql)
            conn.commit()
        else:
            sql = "INSERT INTO study_log VALUES(NULL, '%s', '%s', NOW()); " % (email,delta)
            print(sql)
            cursor.execute(sql)
            conn.commit()
    else:
        sql = "SELECT time FROM study_log WHERE email='%s' AND day = subdate(current_date, 1);"  % (email)
        cursor.execute(sql)
        data = cursor.fetchone()

        if cursor.rowcount > 0:
            sql = "UPDATE study_log SET time = '%s' WHERE email='%s' AND day=subdate(current_date, 1);" % (data[0]+delta,email)
            cursor.execute(sql)
            conn.commit()
        else:
            sql = "INSERT INTO study_log VALUES(NULL, '%s', '%s', subdate(current_date, 1)); " % (email,delta)
            print(sql)
            cursor.execute(sql)
            conn.commit()    
        sql = "INSERT INTO study_log VALUES(NULL, '%s', '%s', NOW()); " % (email,delta)
        cursor.execute(sql)
        conn.commit()
        
def dateOfSUN(date):
    print(date.weekday())
    print(date- timedelta(days=[1,2,3,4,5,6,0][date.weekday()]))
    return date - timedelta(days=[1,2,3,4,5,6,0][date.weekday()])

def dateOfSAT(date):
    print(date+ timedelta(days=6-[1,2,3,4,5,6,0][date.weekday()]))
    return date + timedelta(days=[1,2,3,4,5,6,0][date.weekday()]+6)

def getWeekStudy(email,Somedate):
    Sun = dateOfSUN(Somedate)
    Sat = dateOfSAT(Somedate)
    sql = "SELECT * FROM study_log WHERE email ='%s' AND day BETWEEN '%s' and '%s' ORDER BY day ASC;" % (email,Sun,Sat)
    cursor.execute(sql)
    datas = cursor.fetchall()

    studyArray = {
        Sun.isoformat(): time(),
        (Sun+timedelta(days=1)).isoformat(): time(),
        (Sun+timedelta(days=2)).isoformat(): time(),
        (Sun+timedelta(days=3)).isoformat(): time(),
        (Sun+timedelta(days=4)).isoformat(): time(),
        (Sun+timedelta(days=5)).isoformat(): time(),
        (Sun+timedelta(days=6)).isoformat(): time()
    }

    for data in datas:
        studyArray[data[3].isoformat()] = data[2]
    
    
    #for i in range(len(datas)-1,6):
     #   studyArray.append(time(0,0,0,0).isoformat(timespec='seconds'))

    return studyArray

def getWeekGame(email,Somedate):
    Sun = dateOfSUN(Somedate)
    Sat = dateOfSAT(Somedate)
    sql = "SELECT * FROM game_log WHERE token ='%s' AND type='total' AND date BETWEEN '%s' and '%s' ORDER BY date ASC;" % (email,Sun,Sat)
    cursor.execute(sql)
    datas = cursor.fetchall()

    studyArray = {
        Sun.isoformat(): time(),
        (Sun+timedelta(days=1)).isoformat(): time(),
        (Sun+timedelta(days=2)).isoformat(): time(),
        (Sun+timedelta(days=3)).isoformat(): time(),
        (Sun+timedelta(days=4)).isoformat(): time(),
        (Sun+timedelta(days=5)).isoformat(): time(),
        (Sun+timedelta(days=6)).isoformat(): time()
    }

    for data in datas:
        studyArray[data[4].isoformat()] = data[5].time()
    
    return studyArray

# @param email      이메일
# @param dates      날자 (date형)
# @param type       상태 ( notdo, did )
# 리스트 가지고 오기
def getToDoList(email, dates, type):
    sql = "SELECT * FROM todolog WHERE token='%s' AND date='%s' AND type='%s';" % (email, dates.strftime('%Y-%m-%d'), type)
    cursor.execute(sql)
    datas = cursor.fetchall()
    return datas
