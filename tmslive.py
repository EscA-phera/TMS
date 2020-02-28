# -*- coding: utf-8 -*-

# Copyright (c) 2019 TooMuchSpeaker
# See the file LICENSE for copying permission.
# TooMuchSpeaker v1.0

import json
import sys
import os
from os import urandom

from datetime import time, datetime, timedelta, date
import requests
from flask import Flask, send_file, jsonify, render_template, redirect, url_for, request, session, escape
from flask import Response as res
from flask_restful import Resource, Api, reqparse
from flaskext.mysql import MySQL
from werkzeug.utils import secure_filename

from nugu.functions import *


# app key & CSRFProtect
app = Flask(__name__)
app.secret_key = urandom(24)

# session cookie management
app.config.update(
    session_cookie_secure = True,
    session_cookie_httponly = True,
    session_cookie_samesite = 'LAX'
)

# API key
api = Api(app)

# MySQL config
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root' # Database username
app.config['MYSQL_DATABASE_PASSWORD'] = '' # Database password
app.config['MYSQL_DATABASE_DB'] = 'tms' # Database table name
app.config['MYSQL_DATABASE_HOST'] = '' # Database hosts name
app.config['MYSQL_DATABASE_PORT'] = 3306 # Database port
mysql.init_app(app)

# mainpage
@app.route('/', methods = ['GET'])
def mainpage():
    if request.method == 'GET':
        if 'email' in session:
            true = 'true'
            return render_template('index.html', data = true)
        elif 'email' not in session:
            false = 'false'
            return render_template('index.html', data = false)
        else:
            return redirect(url_for('error'))

# inner resource image
@app.route('/images/<filename>')
def showimage(filename):
    return send_file("images/"+filename, mimetype = 'image/jpeg', attachment_filename = filename, as_attachment = True)

# to send reward_image
@app.route('/rewardImages/<filename>')
def showRewardimage(filename):
    return send_file("RewardImages/"+filename, mimetype='image/jpeg')

# error page
@app.route('/error')
def error():
    return render_template('error.html')

# ToDolist page
@app.route('/todo')
def todo():
    #csrf.init_app(app)
    if 'email' in session:
        return render_template('todo.html')
    else:
        return redirect(url_for('error'))

# to start studying without NUGU speaker
@app.route('/study', methods = ['POST'])
def study():
    if request.method == 'POST' and 'email' in session:
        email = session['email']
        conn = mysql.connect()
        cursor = conn.cursor()
        sql = "SELECT type FROM second_study_log WHERE email = %s ORDER BY studydate DESC;"
        cursor.execute(sql,(email))
       
        if cursor.rowcount>0:
            data = cursor.fetchone()[0]
        else:
            data =""
           
        if data=="start":
            sql = "INSERT INTO second_study_log VALUES(%s, %s, NOW());"
            cursor.execute(sql, (email, 'end'))
            conn.commit()
            SecondStudyLogToStudy(email)
            return redirect(url_for('study'))
 
        else:
            sql = "INSERT INTO second_study_log VALUES(%s, %s, NOW());"
            cursor.execute(sql, (email, 'start'))
            conn.commit()
            return redirect(url_for('study'))
 
    else:
        return redirect(url_for('error'))

@app.route('/study', methods = ['GET'])
def getstudy():
    if request.method == 'GET' and 'email' in session:
        email = session['email']
        conn = mysql.connect()
        cursor = conn.cursor()
        sql = "SELECT type FROM second_study_log WHERE email = %s ORDER BY studydate DESC;"
        cursor.execute(sql,(email))
        if cursor.rowcount > 0:
            data = cursor.fetchone()[0]
        else:
            data =""
       
        if data=="end":
            return render_template('study.html', state = 'end')
        elif data=="start":
            return render_template('study.html', state = 'start')
        else:
             return render_template('study.html', state = 'null')
    else:
        return redirect(url_for('error'))

# to redirect another server
@app.route('/research', methods=['GET'])
def portal():
    if request.method == 'GET':
        if 'email' in session:
            try:
                email = session['email']
                conn = mysql.connect()
                cursor = conn.cursor()
                sql = "SELECT date FROM register WHERE email = %s;"
                cursor.execute(sql,(email))
                data = cursor.fetchall()

                data = data[0]
                temp_date = data[0] + timedelta(days = 30)
                return temp_date

            except Exception as e:
                {'error': str(e)}

            if datetime.today().strftime('%Y-%m-%d') >= temp_date:
                return redirect(url_for('research', name = email))
            else:
                return redirect(url_for('error'))
        else:
            return redirect(url_for('error'))
    else:
        return redirect(url_for('error'))


# analyze study_time && game_time
@app.route('/research/<name>', methods=['GET'])
def research(name):
    if request.method == 'GET':
        if 'email' in session and 'email' == name:
            email = session['email']
            form = {
                'email': email
            }
            data = requests.post(url = 'https://tmslive.kr/research', json = form)
        else:
            return redirect(url_for('error'))

@app.route('/license', methods = ['GET'])
def li():
    return render_template('license.html')

# to update ToDolist with MySQL
@app.route('/UPDATE', methods = ['POST'])
def update():
    if request.method == 'POST' and 'email' in session:
        email = session['email']
        
        conn = mysql.connect()
        cursor = conn.cursor()

        sql = "SELECT * FROM ToDolist WHERE email = %s;"

        cursor.execute(sql,(email))
        if cursor.rowcount > 0:
            sql = "UPDATE ToDolist SET JSON = %s WHERE email = %s;"
            cursor.execute(sql,(request.data, email)) 
            conn.commit()
        else:
            sql = "INSERT INTO ToDolist VALUES(NULL, %s, %s);"
            cursor.execute(sql,(email, request.data)) 
            conn.commit()
        return jsonify('{200}')       
    else:
        return redirect(url_for('error'))
    #그럼 누구에서 등록한거 어캐봄
    #MYSQL todolist
    #@param token varchar ( email )
    #@param type varchar ( did, notdo )
    #@param name varchar 
    #@param date DATE
    #@param favorite BOOL
 
# to send data to ToDolist html
@app.route('/GET', methods = ['POST'])
def get():
    if request.method == 'POST' and 'email' in session:
        email = session['email']
        conn = mysql.connect()
        cursor = conn.cursor()

        sql = "SELECT * FROM ToDolist WHERE email = %s;"

        cursor.execute(sql, (email))
        if cursor.rowcount > 0:  
            data = cursor.fetchone()  
            return jsonify(data[2])
        else:
            sql = "INSERT INTO ToDolist VALUES(NULL, %s ,'');" 
            cursor.execute(sql,(email))
            return jsonify('[]') 

    else:
        return redirect(url_for('error'))

# reward webpage
@app.route('/reward', methods = ['POST', 'GET'])
def reward():
    if request.method == 'GET':
        if 'email' in session:
            email = session['email']
            conn = mysql.connect()
            cursor = conn.cursor()
            sql ="SELECT * FROM reward WHERE email=%s AND date BETWEEN %s and %s;"
            cursor.execute(sql,(email , dateOfSUN(datetime.now().date()) ,dateOfSAT(datetime.now().date())))
            
            if cursor.rowcount == 0:
                return render_template('reward.html')

            else:    
                data = cursor.fetchall()[0]
                name = data[0]
                image = data[1]
                toemail = data[3]
                kind = data[4]
                time = data[5]
                date = data[6]

                return render_template('reward.html', state = 'Quest', name = name, image = image, toemail = toemail, kind = kind, time = time)
            
        else:
            return redirect(url_for('error'))
    
    elif request.method == 'POST':
        if 'email' in session:
            email = session['email']
            
            name = request.form['name']
            kind = request.form['kind']
            time = request.form['time']
            toemail = request.form['toemail']
            image = request.files['image']

            split = secure_filename(image.filename).split('.')
            image.save("rewardImages/"+secure_filename(email+"_"+split[0]+"."+split[len(split)-1]))
            url = secure_filename(email+"_"+split[0]+"."+split[len(split)-1])

            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "INSERT INTO reward VALUES(%s, %s, %s, %s, %s, %s, NOW());"
            cursor.execute(sql, (name, url, email, toemail, kind, time))
            conn.commit()

            return redirect(url_for('reward'))

        else:
            return redirect(url_for('reward'))
    
    else:
        return redirect(url_for('error'))

# to get reward in webpage
@app.route('/rewardreceive', methods = ['GET'])
def rewardreceive():
    if 'email' in session:
        if request.method == 'GET':

            email = session['email']
            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "SELECT * FROM reward WHERE toemail = %s AND date BETWEEN %s and %s; "
            cursor.execute(sql,(email, dateOfSUN(datetime.now().date()) ,dateOfSAT(datetime.now().date())))

            state = "none"
            week_time = []
            goal_time = timedelta()
            sumtime = timedelta()
            path = ""
            able = "false"

            if cursor.rowcount > 0:
                data = cursor.fetchone()

                state = data[4]
                goal_time = timedelta(hours = int(data[5]))

                if state == "study":
                    week_time = getWeekStudy(email, datetime.now().date())
                else:
                    week_time = getWeekGame(email, datetime.now().date())

                for pre_time in week_time:
                        element = week_time[pre_time]

                        if isinstance(element, time):
                            sumtime += timedelta(hours = element.hour,minutes = element.minute,seconds = element.second)

                        else:
                            sumtime += element
            
            lastweek = datetime.now() - timedelta(days = 7)
            sql = "SELECT * FROM reward WHERE toemail = %s AND date BETWEEN %s and %s; " 
            cursor.execute(sql,(email, dateOfSUN(lastweek.date()) ,dateOfSAT(lastweek.date())))

            if cursor.rowcount > 0:
                data = cursor.fetchone()
                prestate = data[4]
                rewardtime = timedelta(hours = int(data[5]))

                if prestate == "study":
                    pre_week_time = getWeekStudy(email, lastweek.date())

                else:
                    pre_week_time = getWeekGame(email, lastweek.date())

                sumtime = timedelta()
                array_time = []
                for pre_time in pre_week_time:
                    element = pre_week_time[pre_time]

                    if isinstance(element, time):
                        sumtime += timedelta(hours = element.hour,minutes = element.minute,seconds = element.second)
                        array_time.append(element.isoformat(timespec = 'seconds'))

                    else:
                        sumtime += element
                        array_time.append(str(element))
                
                if prestate == "study" and sumtime/rewardtime >= 1:
                    able = "true"
                    path = data[1]

                elif prestate == "game" and sumtime/rewardtime <= 1:
                    able = "true"
                    path = data[1]

            return render_template('receivereward.html', state = state, goal = goal_time, week_time = sumtime, ReceiveAble = able, ReceivePath = path)

        else:
            return redirect(url_for('error'))

    else:
        return redirect(url_for('error'))

# checking day_time of game and study
@app.route('/day', methods = ['GET'])
def agame():
    if 'email' in session and request.method == 'GET':
        email = session['email']
        sql = "SELECT time FROM study_log WHERE email=%s AND day=subdate(current_date, 0);"
        cursor.execute(sql,(email))
        Daystudy = time(hour = 0, minute = 0, second = 0)
        
        if cursor.rowcount > 0:
            Daystudy = cursor.fetchone()[0]

        sql = "SELECT time FROM game_log WHERE token= %s AND type='total' AND date=subdate(current_date, 0);"
        cursor.execute(sql,(email))
        Daygame = time(hour = 0, minute = 0, second = 0)

        if cursor.rowcount > 0:
            Daygame = cursor.fetchone()[0].time()
        
        Weekstudy = getWeekStudy(email,datetime.now().date())
        Weekgame= getWeekGame(email,datetime.now().date())

        study_time = []
        for pre_time in Weekstudy:
            element = Weekstudy[pre_time]
            if isinstance(element,time):
                study_time.append(element.isoformat(timespec='seconds'));
            else:
                study_time.append(str(element))

        game_time = []
        for pre_time in Weekgame:
            element = Weekgame[pre_time]
            if isinstance(element,time):
                game_time.append(element.isoformat(timespec='seconds'));
            else:
                game_time.append(str(element))
        

        return render_template('oneday.html', studytime = Daystudy, gametime = Daygame ,weekStudyTime = study_time,weekGameTime=game_time)

    else:
        return redirect(url_for('error'))

# Privacy Policy
@app.route('/ad')
def blacknut():
    return render_template('body.html')

# User_login and session and send user data to MySQL
@app.route('/oauth')
def oauth():
    code = str(request.args.get('code'))
    url = "https://kauth.kakao.com/oauth/token"
    payload = "grant_type=authorization_code&client_id=aa87fd1414c63edd82ba52f286193004&redirect_url=https://tmslive.co.kr/oauth&code="+ str(code)
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache"
    }
    data = {
        'property_keys': '["kakao_account.email"]'
    }
    response = requests.request("POST", url, data = payload, headers = headers)
    access_token = json.loads(((response.text).encode('utf-8')))['access_token']
    
    url = "https://kapi.kakao.com/v1/user/signup"
    headers.update({'Authorization': 'Bearer ' + str(access_token)})
    response = requests.request("POST", url, headers = headers)

    url = "https://kapi.kakao.com/v2/user/me"
    response = requests.request("POST", url, headers = headers,data= data)

    result = json.loads(((response.text).encode('utf-8')))
    session['email'] = result['kakao_account']['email']
    email = session['email']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "SELECT * FROM register WHERE email = %s;"
    cursor.execute(sql,(email))
    data = cursor.fetchone()

    if data:
        return redirect(url_for('mainpage'))

    else:
        sql = "INSERT INTO register VALUES(%s, NOW())"
        cursor.execute(sql, (email))
        sql = "INSERT INTO ToDolist VALUES(NULL, '%s' ,'');"
        cursor.execute(sql, (email))

        conn.commit()
        return redirect(url_for('mainpage'))

# session out
@app.route('/logout')
def sign_out():
    code = str(request.args.get('code'))

    if 'email' in session:
        session.pop('email')
        return redirect(url_for('mainpage'))
    else:
        return redirect(url_for('mainpage'))

# membership withdrawal
@app.route('/unlink')
def unlink():
    code = str(request.args.get('code'))
    url = "https://kauth.kakao.com/oauth/token"
    payload = "grant_type=authorization_code&client_id=aa87fd1414c63edd82ba52f286193004&redirect_url=https://tmslive.co.kr/oauth&code="+code
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache"
    }
    data = {
        'property_keys': '["kakao_account.email"]'
    }
    response = requests.request("POST", url, data = payload, headers = headers)
    access_token = json.loads(((response.text).encode('utf-8')))['access_token']
    
    url = "https://kapi.kakao.com/v2/user/me"
    headers.update({'Authorization': 'Bearer ' + str(access_token)})
    response = requests.request("POST", url, headers = headers,data= data)
    result = json.loads(((response.text).encode('utf-8')))
    email = result['kakao_account']['email']

    session.pop('email')

    url = "https://kapi.kakao.com/v1/user/unlink"
    response = requests.request("POST", url, headers = headers)
    result = json.loads(((response.text).encode('utf-8')))

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "DELETE FROM register WHERE email = %s;" 
    cursor.execute(sql,(email))
    conn.commit()

    return redirect(url_for('mainpage'))

# if game is started
class GameOn(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('token', type = str)
            parser.add_argument('userid', type = str)
            parser.add_argument('gamename', type = str)
            args = parser.parse_args()

            _id = args['userid']
            _token = args['token']
            _gamename = args['gamename']

            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "INSERT INTO game_log VALUES(%s, %s, 'start', %s, %s, NOW());"
            cursor.execute(sql, (_token, _id, _gamename, datetime.today().strftime('%Y-%m-%d')))
            conn.commit()
            data = cursor.fetchall()

            # 성공 시
            if len(data) is 0:
                return {'StatusCode': '200', 'Message': 'Successfully Generated.'}
            else:
                return {'StatusCode': '1000', 'Message': str(e)}

        # 실패 시
        except Exception as e:
            return {'error': str(e)}


# if game is end
class GameOff(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('token', type = str)
            parser.add_argument('userid', type = str)
            parser.add_argument('gamename', type = str)
            args = parser.parse_args()

            _token = args['token']
            _id = args['userid']
            _gamename = args['gamename']

            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "INSERT INTO game_log VALUE(%s, %s, 'end', %s, %s, NOW());"
            cursor.execute(sql, (_token, _id, _gamename, datetime.today().strftime('%Y-%m-%d')))
            conn.commit()

            sql = "SELECT * FROM game_log WHERE userid=%s AND type='start';" 
            cursor.execute(sql,(_id))
            datas = cursor.fetchall()
            data = datas[len(datas) - 1]

            realtime = datetime.today().timestamp() - data[5].timestamp()
            temp = datetime.fromtimestamp(realtime)

            sql = "INSERT INTO game_log VALUE(%s,%s, 'total', %s, %s,%s);"
            cursor.execute(sql,(_token, _id, _gamename, datetime.today().strftime('%Y-%m-%d'), temp.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            data = cursor.fetchall()

            # 성공 시
            if len(data) is 0:
                conn.commit()
                return {'StatusCode': '200', 'Message': 'Successfully Generated.'}
            else:
                return {'StatusCode': '1000', 'Message': str(data[0])}

        # 실패 시
        except Exception as e:
            return {'error': str(e)}
# NUGU
class gametime(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=str)
            parser.add_argument('event', type=str)
            parser.add_argument('context', type=str)
            args = parser.parse_args()

            token = args['context']['session']['accessToken']
            parmeters = args['action']['parameters']
            month = parameters['month']
            month = month['value']
            day = parameters['day']
            day = day['value']

            cal = '2019-' + month + '-' + day
            sql = "SELECT * FROM game_log WHERE token='%s' AND date='%s';" % (token, cal)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql)
            datas = cursor.fetchall()
            total = 0

            for data in datas:
                total += data[5].timestamp()

            hour = int(total / 3600)
            minute = int(total / 60)

            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "month": str(month),
                    "day": str(day),
                    "hour": str(hour),
                    "minute": str(minute)
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class gamenow(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('version', type=str)
        parser.add_argument('action', type=str)
        parser.add_argument('event', type=dict)
        parser.add_argument('context', type=str)

        args = parser.parse_args()
        token = args['context']['session']['accessToken']
        token = getemail(token)
        if (not isgaming(token) and not isstudy(token)):
            message = "지금 게임, 공부를 하고있지 않아요! 공부 했으면 좋겠어요.."

        if (not isgaming(token) and isstudy(token)):
            message = "지금 게임이 아니라 공부를 열심히 하고 있네요!"
        if (isgaming(token)):
            # game_log 현제 플레이중인 게임이름, 게임 시간 뽑아주셈
            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "SELECT * FROM game_log WHERE token = %s AND type='start' ORDER BY date ASC;"
            cursor.execute(sql, (token))
            data = cursor.fetchone()
            gameTime = datetime.now() - data[5]

            minute = gameTime.minute
            hour = gameTime.hour
            # minute = int((datetime.today() - data[5].timestamp()) / 1000 / 60) % 60
            # hour = int(minute / 60)
            message = "지금 현재 " + data[3] + " 를 " + hour + " 시간 " + minute + "분 플레이 하고 있습니다!"

        return {
            'version': '2.0',
            'resultCode': 'OK',
            'output': {
                'message': message
            }
        }


class GameYes(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=str)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            token = args['context']['session']['accessToken']
            cal = date.today() - timedelta(days=1)
            cal = cal.strftime("%Y-%m-%d")

            sql = "SELECT * FROM game_log WHERE token='%s' AND date='%s';" % (getemail(token), cal)
            cursor.execute(sql)
            datas = cursor.fetchall()
            total = 0
            for data in datas:
                total += data[5].timestamp()
            minute = int(total / 1000 / 60 % 60)
            hour = int(total / 1000 / 60 / 60)

            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "hours": str(hour),
                    "minutes": str(minute)
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class LastBreeping(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)
            isInStudy = False
            isDeGame = False
            args = parser.parse_args()
            token = args['context']['session']['accessToken']
            token = getemail(token)
            monday = date.today() - timedelta(days=date.today().weekday())
            last_week_game = sumWeekGame(token, monday)
            last_week_study = sumWeekStudy(token, monday)
            last2_week_game = sumWeekGame(token, monday - timedelta(days=7))
            last2_week_study = sumWeekStudy(token, monday - timedelta(days=7))

            message = "저번주에는 " + timestampToString(last_week_game) + " 게임했으며, " + timestampToString(
                last_week_game) + " 공부했습니다. 지난주에 비해 공부시간은 "

            if (last_week_study >= last2_week_study):
                message += timestampToString(last_week_study - last2_week_study) + " 증가했으며 게임시간은"
                isInStudy = True
            if (last_week_study < last2_week_study):
                message += timestampToString(last2_week_study - last_week_study) + " 감소했으며 게임시간은"
                stat = "공부를 좀 더 하고,"
            if (last_week_game < last2_week_game):
                message += timestampToString(last2_week_game - last_week_game) + " 감소했어요!"
                stat += "화이팅 하세요!"
                isDeGame = True
            if (last_week_game >= last2_week_game):
                message += timestampToString(last_week_game - last2_week_game) + " 증가했어요!"
                stat += "게임 좀 줄이셨으면 좋겠어요."
            if (isInStudy and isDeGame):
                message = message + " 앞으로도 이렇게만 최선을 다해주세요! 파이팅! 잘했어요."
            else:
                message = message + stat

            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class GameToday(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()

            token = args['context']['session']['accessToken']

            sql = "SELECT * FROM game_log WHERE token='%s' AND date='%s';" % (
            getemail(token), date.today().strftime("%Y-%m-%d"))
            cursor.execute(sql)
            datas = cursor.fetchall()
            total = 0
            for data in datas:
                total += data[5].timestamp()
            minute = int(total / 1000 / 60 % 60)
            hour = int(total / 1000 / 60 / 60)

            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "hourss": str(hour),
                    "minutess": str(minute)
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


@app.route('/action/study.start', methods=['POST'])
def StudyStart():
    try:
        req = request.json
        print(req)
        token = req['context']['session']['accessToken']
        email = getemail(token)

        if (isstudy(email)):
            message = "이미 공부 타이머가 시작되었어요!"
        elif (not ( isstudy(email) ) and isgaming(email)):
            message = "게임을 하고 있는데 뭔 공부를 시작해요! 게임먼저 끄세요!"
        elif (not (isstudy(email)) and not (isgaming(email))):
            message = "공부 시작했어요! 열심히 공부하세요! ASMR 들으면서 공부 해봐요!"
            sql = "INSERT INTO second_study_log VALUES(%s, %s, NOW());"
            cursor.execute(sql, (email, 'start'))
            conn.commit()
        return {
            'version': '2.0',
            'resultCode': 'OK',
            "output": {
                "message": message
            }

         }
    except Exception as e:
        print(str(e))
        return {
            'error': str(e),
            "resultCode": "OK",
            "output": {
                "message": str(e)
            }
       }


class StudyEnd(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            #token = args['context']
            #token = token['session']
            #token = token['accessToken']
            token = args['context']['session']['accessToken']
            token = getemail(token)

            if (isstudy(token)):
                message = "공부 타이머를 시작한 적이 없어요.."
            else:
                sql = "INSERT INTO second_study_log VALUES(%s, %s, NOW());"
                cursor.execute(sql, (token, 'end'))
                conn.commit()
                SecondStudyLogToStudy(token)
                message = "공부 타이머를 종료할게요! 오늘은" + timestampToString(
                    datetime.today().timestamp() - data[5].timestamp()) + " 공부했어요!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }

            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class boring(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            token = args['context']['session']['accessToken']
            email = getemail(token)
            if (isstudy(email)):
                message = "음.. 공부 중 이신데, 공부에 집중할 수 있는 음악을 들어 보시는 건 어떠신가요?"
            elif (isgaming(email)):
                message = "게임… 하시고 계신데.. 다른 체육활동을 해보는 건 어떠세요?"
            else:
                message = "음.. 공부 많이 하시고, 쉬엄쉬엄 게임하세요! 무리하지 마세요!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }

            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class ToDoLeft(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            token = args['context']['session']['accessToken']
            datas = getToDoList(getToDoList(getemail(token), date.today(), 'notdo'))
            if (len(datas) == 0):
                message = "남은 과목 없어요! 축하해요! 일이 있으면 추가로 등록해봐요!"
            else:
                message = "현재 남은 공부는 "
                for data in datas:
                    message += data[2] + ", "
                message += "공부 입니다!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class ToDoDoneList(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            token = args['context']['session']['accessToken']
            datas = getToDoList(getToDoList(getemail(token), date.today(), 'did'))
            if (len(datas) == 0):
                message = "한 과목 없어요! 축하해요! 일이 있으면 추가로 등록해봐요!"
            else:
                message = "오늘 한 공부는 "
                for data in datas:
                    message += data[2] + ", "
                message += "공부 입니다!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class ToDoInsert(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()

            parameters = context['action']['parameters']

            subject = parameters['subject']
            subject = subject['value']
            token = args['context']['session']['accessToken']
            sql = "SELECT * FROM todolist WHERE token='%s' AND name='%s' AND date='%s';" % (
            getemail(token), subject, date.today().strftime('%Y-%m-%d'))
            cursor.execute(sql)
            datas = cursor.fetchall()
            if (len(datas) == 0):
                sql = "INSERT INTO todolist VALUES(%s,'notdo',%s, %s , 'false');"
                cursor.execute(sql, (getemail(token), subject, date.today().strftime('%Y-%m-%d')))
                message = "등록되었습니다! 꼭 이 공부 하시길 바래요!"
            else:
                message = "이미 등록되어있는 공부예요!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class ToDoDone(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            event = args['event']
            context = args['action']
            parameters = context['parameters']

            subject = parameters['subject']
            subject = subject['value']
            token = args['context']['session']['accessToken']
            sql = "SELECT * FROM todolist WHERE token='%s' AND name='%s' AND date='%s';" % (
                getemail(token), subject, date.today().strftime('%Y-%m-%d'))
            cursor.execute(sql)
            datas = cursor.fetchall()
            if (len(datas) == 0):
                message = "등록된 것이 없어요."
            else:
                data = datas[0]
                if (data[1] == 'notdo'):
                    sql = "UPDATE todolist SET type = 'did' WHERE token='%s' AND name='%s' AND date='%s' AND type='notdo';" % (
                        getemail(token), subject, date.today().strftime('%Y-%m-%d'))
                    message = "완료 처리 했습니다!"
                else:
                    message = "이미 완료된 공부이예요! 다른 공부를 해봐요!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class ToDoRemove(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            event = args['event']
            context = args['action']
            parameters = context['parameters']
            print(parameters)
            subject = parameters['subject']
            subject = subject['value']
            print(subject)
            token = args['context']['session']['accessToken']
            sql = "SELECT * FROM todolist WHERE token='%s' AND name='%s' AND date='%s';" % (
                getemail(token), subject, date.today().strftime('%Y-%m-%d'))
            cursor.execute(sql)
            datas = cursor.fetchall()
            if (len(datas) == 0):
                message = "등록된 것이 없어요."
            else:
                data = datas[0]
                sql = "DELETE FROM todolist WHERE token='%s' AND name='%s' AND date='%s';" % (
                    getemail(token), subject, date.today().strftime('%Y-%m-%d'))
                message = "삭제 처리 했습니다!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class ToDoNotDone(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()
            event = args['event']
            context = args['action']
            parameters = context['parameters']

            subject = parameters['subject']
            subject = subject['value']
            token = args['context']['session']['accessToken']
            sql = "SELECT * FROM todolist WHERE token='%s' AND name='%s' AND date='%s';" % (
                getemail(token), subject, date.today().strftime('%Y-%m-%d'))
            cursor.execute(sql)
            datas = cursor.fetchall()
            if (len(datas) == 0):
                message = "등록된 것이 없어요."
            else:
                data = datas[0]
                if (data[1] == 'did'):
                    sql = "UPDATE todolist SET type = 'notdo' WHERE token='%s' AND name='%s' AND date='%s' AND type='did';" % (
                        getemail(token), subject, date.today().strftime('%Y-%m-%d'))
                    message = "미완료 처리 했습니다!"
                else:
                    message = "아직 안한 공부예요.. 빨리 빨리 공부해요!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


class SayQuest(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('version', type=str)
            parser.add_argument('action', type=dict)
            parser.add_argument('event', type=dict)
            parser.add_argument('context', type=dict)

            args = parser.parse_args()


            token = args['context']['session']['accessToken']
            token = getemail(token)

            sql = "SELECT * FROM reward WHERE toemail=%s AND date BETWEEN %sand %s;"
            cursor.execute(sql, (token, dateOfSUN(datetime.now().date()), dateOfSAT(datetime.now().date())))
            if (cursor.rowcount == 0):
                message = "등록된 퀘스트가 없습니다! 부모님에게 퀘스트 등록을 제안해 보세요!"
            else:
                data = cursor.fetchone()
                message = "현제 진행중인 퀘스트의 진행도는 "
                kind = data[4]
                Rewardtime = datetime(hour=0, minute=0, second=0) + timedelta(hours=int(data[5]))

                if kind == "study":
                    message += "공부시간은 "
                    studytime = datetime(hour=0, minute=0, second=0) + sumWeekStudy(token, date.today())
                    if studytime.timestamp() < time.timestamp():
                        message += timestampToString(Rewardtime.timestamp() - studytime.timestamp()) + " 부족합니다 "
                    if studytime.timestamp() >= time.timestamp():
                        message += timestampToString(
                            studytime.timestamp() - Rewardtime.timestamp()) + " 초과되었습니다! 축하해요! "
                else:
                    gametime = time(hour=0, mintue=0, second=0) + sumWeekGame(token, date.today())
                    message += "게임시간은 "
                    if gametime.timestamp() > time.timestamp():
                        message += timestampToString(
                            gametime.timestamp() - Rewardtime.timestamp()) + " 초과되었기에, 이번주 퀘스트 달성이 불가능 해요. 다음에는 게임을 줄이고 열심히 해봐요!"
                    if gametime.timestamp() <= time.timestamp():
                        message += timestampToString(
                            Rewardtime.timestamp() - gametime.timestamp()) + " 남았습니다. 이번주 퀘스트 달성이 가능해요! 열심히 해서 퀘스트 달성 파이팅!"
            return {
                'version': '2.0',
                'resultCode': 'OK',
                "output": {
                    "message": message
                }
            }
        except Exception as e:
            print(str(e))
            return {
                'error': str(e),
                "resultCode": "OK",
                "output": {
                    "message": str(e)
                }
            }


api.add_resource(gametime, '/action/game.find')
api.add_resource(GameYes, '/action/game.yesterday')
api.add_resource(gamenow, '/action/game.now')
api.add_resource(GameToday, '/action/game.todayhour')
api.add_resource(LastBreeping, '/action/breeping')
api.add_resource(boring, '/action/boring')
api.add_resource(StudyEnd, '/action/study.end')
api.add_resource(ToDoNotDone, '/action/todo.donotdone')
api.add_resource(ToDoRemove, '/action/todo.remove')
api.add_resource(ToDoDone, '/action/todo.dodone')
api.add_resource(ToDoInsert, '/action/todo.insert')
api.add_resource(ToDoLeft, '/action/todo.show')
api.add_resource(ToDoDoneList, '/action/todo.done')
api.add_resource(SayQuest, '/action/reward')
api.add_resource(GameOn, '/startgame')
api.add_resource(GameOff, '/endgame')



# server is running!
if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = False)

# Copyright (c) 2019 TooMuchSpeaker

    # See the file LICENSE for copying permission.
# TooMuchSpeaker v1.0
########## Too Much Speaker's New Server ##########
