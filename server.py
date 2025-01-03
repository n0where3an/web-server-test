#!/usr/bin/python3

### File            : server.py
### Description     : Test pod for testing installed kubernetes
### Author          : Michael Yasko
### Version history :

from prometheus_client import start_http_server, Gauge, Counter, Histogram, generate_latest
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import sys
import os
import time
import json
import mysql.connector
import redis
import random
import threading

gb_configenv =  False
gb_configfile = False
gb_redisconnection = False
gb_redischeck      = False
gb_mysqlconnection = False
gb_mysqlcheck      = False

gs_web_mysql_host       = None
gs_web_redis_host       = None

gs_hostname=""

gi_metrics_counter=0
gi_healtcheck_counter=0
gi_readycheck_counter=0

go_rs_client={}
go_ms_client={}

#Метрики прометеус
# Создаем гистограмму для метрик времени запроса
REQUEST_TIME = Histogram ( 'n0whereman_http_server_requests_seconds', 'Duration of HTTP server request handling', ['method', 'endpoint', 'status', 'exception', 'outcome'] )
# Кастомные метрики
TEST_POD_PARAM_INT = Gauge('n0whereman_test_pod_param_int', 'Test pod param int')
TEST_POD_PARAM_FLOAT = Gauge('n0whereman_test_pod_param_float', 'Test pod param float')
TEST_POD_REDIS_CHECK = Gauge('n0whereman_test_pod_redis_check', 'Test pod Redis check (0 for false, 1 for true)')
TEST_POD_MYSQL_CHECK = Gauge('n0whereman_test_pod_mysql_check', 'Test pod MySQL check (0 for false, 1 for true)')
TEST_POD_CURRENT_TIME = Gauge('n0whereman_test_pod_current_time', 'Test pod current time in Unix format')
METRICS_COUNTER = Counter('n0whereman_test_pod_metrics_counter', 'Total number of metrics processed by the pod')
HEALTHCHECK_COUNTER = Counter('n0whereman_test_pod_healtcheck_counter', 'Total number of health checks performed by the pod')
READYCHECK_COUNTER = Counter('n0whereman_test_pod_readycheck_counter', 'Total number of ready checks performed by the pod')
STARTUPCHECK_COUNTER = Counter('n0whereman_test_pod_startupcheck_counter', 'Total number of startup checks performed by the pod')

def RedisCheck():
    global gb_redischeck
    global gb_redisconnection
    global gs_web_redis_host

    if not gb_redischeck :
#        print("Redis check disabled")
        return True

    if gs_web_redis_host == None :
        print("Redis undefined")
        return gb_redisconnection

    ls_keyname='web-server-'+gs_hostname
    # Save value
    lb_result=go_rs_client.set(ls_keyname, string_arg )
    if not lb_result:
        gb_redisconnection = False
        print("Redis write unsuccess")
        return gb_redisconnection
    else:
        print("Redis write success")

    # Read value
    value = go_rs_client.get(ls_keyname)
    print(value)

    if value.decode() == string_arg :
        gb_redisconnection = True
    else:
        gb_redisconnection = False
    print(value.decode())
    print(str(gb_redisconnection))
    return gb_redisconnection

def MysqlCheck(fb_init=False):
    global gb_mysqlcheck
    global gb_mysqlconnection
    global gs_web_mysql_host

    if not gb_mysqlcheck :
#        print("Mysql check disabled")
        return True

    if gs_web_mysql_host == None :
        print("Mysql undefined")
        return gb_mysqlconnection
    try:
        l_cursor = go_ms_client.cursor()
        print("Mysql cursor:", str(l_cursor))
    except mysql.connector.Error as err:
        gb_mysqlconnection = False
        print("Mysql cursor not open"+err)
        return gb_mysqlconnection

    ls_fquery = "select count(*) from web_server_test;"
    if fb_init :
        ls_fquery = "insert web_server_test (port) values ("+str(gi_server_port)+");"

    print (ls_fquery)
    try:
        l_cursor.execute(ls_fquery)
        print("Mysql cursor:", str(l_cursor))
    except mysql.connector.Error as err:
        gb_mysqlconnection = False
        print("Mysql cursor fail "+err)
        return gb_mysqlconnection

    if not fb_init :
        l_records = l_cursor.fetchall()
        print("Mysql execute result"+str(l_records))
    gb_mysqlconnection = True
    return gb_mysqlconnection

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    global gb_mysqlcheck
    global gb_mysqlconnection
    global gb_redischeck
    global gb_redisconnection
    global gi_metrics_counter
    global gi_healtcheck_counter
    global gi_readycheck_counter

    endpoint = self.path

    # Дополнительные метки
    exception = "None"
    outcome = "SUCCESS"

    match endpoint :
        case '/startupcheck':
            l_tmp=RedisCheck()
    #        print (str(l_tmp))
            l_tmp=MysqlCheck()
    #        print (str(l_tmp))
            li_retcode=200
            if not gb_configenv and not gb_configfile :
                li_retcode=503
            l_smysql='"mysql_connection":null'
            if gb_mysqlcheck :
                l_smysql='{"mysql_connection":'+str(gb_mysqlconnection)
                if  gb_mysqlconnection :
                    li_retcode=503
            l_sredis='"redis_connection":null'
            if  gb_redischeck :
                l_sredis='"redis_connection":'+str(gb_redisconnection)
                if gb_redisconnection :
                    li_retcode=503
            self.send_response(li_retcode)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            ls_tmp='{"query_number":'+ str(gi_readycheck_counter) +', "config_file":'+str(gb_configfile)+',"env_variables":'+str(gb_configenv)+','+l_smysql+','+l_sredis+'}'
            STARTUPCHECK_COUNTER.inc()
            self.wfile.write(ls_tmp.encode())
        case '/readycheck':
            l_tmp=RedisCheck()
    #        print (str(l_tmp))
            l_tmp=MysqlCheck()
    #        print (str(l_tmp))
            li_retcode=200
            if not gb_configenv and not gb_configfile :
                li_retcode=503
            l_smysql='"mysql_connection":null'
            if gb_mysqlcheck :
                l_smysql='{"mysql_connection":'+str(gb_mysqlconnection)
                if  gb_mysqlconnection :
                    li_retcode=503
            l_sredis='"redis_connection":null'
            if  gb_redischeck :
                l_sredis='"redis_connection":'+str(gb_redisconnection)
                if gb_redisconnection :
                    li_retcode=503
            self.send_response(li_retcode)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            ls_tmp='{"query_number":'+ str(gi_readycheck_counter) +', "config_file":'+str(gb_configfile)+',"env_variables":'+str(gb_configenv)+','+l_smysql+','+l_sredis+'}'
            READYCHECK_COUNTER.inc()
            self.wfile.write(ls_tmp.encode())
        case '/healthcheck':
            l_tmp=RedisCheck()
    #        print (str(l_tmp))
            l_tmp=MysqlCheck()
    #        print (str(l_tmp))
            li_retcode=200
            l_smysql='"mysql_connection":null'
            if gb_mysqlcheck :
                l_smysql='{"mysql_connection":'+str(gb_mysqlconnection)
                if  gb_mysqlconnection :
                    li_retcode=503
            l_sredis='"redis_connection":null'
            if  gb_redischeck :
                l_sredis='"redis_connection":'+str(gb_redisconnection)
                if gb_redisconnection :
                    li_retcode=503
            self.send_response(li_retcode)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            ls_tmp='{"query_number":'+ str(gi_healtcheck_counter) +','+l_smysql+','+l_sredis+'}'
            HEALTHCHECK_COUNTER.inc()
            self.wfile.write(ls_tmp.encode())
        case '/about':
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(b'<!doctype html><html><head><title>Test page</title><meta content="text/html; charset=utf-8" http-equiv="Content-Type"></head><body> ' + socket.gethostname().encode() + b'<br><br>')
            self.wfile.write(b'<b>Hello from hostname:</b> ' + socket.gethostname().encode() + b'<br><br>')
            self.wfile.write(b'<b>Interval: </b> ' + str(interval).encode() + b'<br><br>')
            self.wfile.write(b'<b>Desired count of print: </b> ' + str(desired_count).encode() + b'<br><br>')
            self.wfile.write(b'<b>Text arg: </b> ' + str(string_arg).encode() + b'<br><br>')
            count = 1
            while(count <= desired_count):
                self.wfile.write(b"<b>" + str(count).encode() + b".</b> " + b"<b>Current time: </b>" + str(time.strftime("%X")).encode() + b"<br>")
                time.sleep(interval)
                count+=1
            self.wfile.write(b"<br><b>End of loop.</b>")
            self.wfile.write(b'</body></html>')
        case "/metrics":
            status = report_metrics(self)
        case _:
            start = time.time()  # Начало замера времени
            try:
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write(b'<!doctype html><html><head><title>Test page</title><meta content="text/html; charset=utf-8" http-equiv="Content-Type"></head><body> ' + socket.gethostname().encode() + b'<br><br>')
                self.wfile.write(b"Hello, World!")
                self.wfile.write(b'</body></html>')
                status = 200
            except Exception as e:
                self.send_response(500)
                exception = str(type(e).__name__)  # Устанавливаем тип исключения
                outcome = "FAILURE"
                status = 500
            finally:
                # Замер времени и запись в гистограмму с дополнительными метками
                duration = time.time() - start
                REQUEST_TIME.labels(method="GET",endpoint=endpoint,status=str(status),exception=exception,outcome=outcome).observe(duration)

# Новый обработчик для /metrics на порту 9100
def report_metrics(self):
    from prometheus_client import generate_latest
    current_unix_time_millis = int(time.time() * 1000)
    TEST_POD_PARAM_INT.set(random.randint(1, 100))
    TEST_POD_PARAM_FLOAT.set(random.uniform(-500, 500))
    TEST_POD_REDIS_CHECK.set(int(gb_redisconnection))
    TEST_POD_MYSQL_CHECK.set(int(gb_mysqlconnection))
    TEST_POD_CURRENT_TIME.set(current_unix_time_millis)
 
    status = 200
    self.send_response(status)
    self.send_header("Content-Type", "text/plain; version=0.0.4")
    self.end_headers()
    self.wfile.write(generate_latest())
    METRICS_COUNTER.inc()
    return status

# Функция для запуска HTTP-сервера на порту 8000
def run_main_server():
    global gi_server_port
    httpd = HTTPServer(('0.0.0.0', gi_server_port), SimpleHTTPRequestHandler)
    print('Listening on port %s ...; gs_web_redis_host "%s" ; gs_web_mysql_host "%s" ; ' % (gi_server_port , gs_web_redis_host , gs_web_mysql_host))
    httpd.serve_forever()


if __name__ == '__main__':
    interval = int(sys.argv[1])
    desired_count = int(sys.argv[2])
    string_arg = sys.argv[3]

    gi_server_port          = 8000
    gi_metrics_port         = 9100  # Порт для метрик

    gi_web_mysql_port       = -1
    gs_web_mysql_username   = ""
    gs_web_mysql_password   = ""
    gs_web_mysql_dbname     = ""

    gi_web_redis_port       = -1
    gi_web_redis_db         = -1

    gb_configfile = True
    gb_configenv = True

    try:
        server_port        = os.getenv("SERVER_PORT")
        web_mysql_host     = os.getenv("WEB_MYSQL_HOST")
        web_mysql_port     = os.getenv("WEB_MYSQL_PORT")
        web_mysql_username = os.getenv("WEB_MYSQL_USERNAME")
        web_mysql_password = os.getenv("WEB_MYSQL_PASSWORD")
        web_mysql_dbname   = os.getenv("WEB_MYSQL_DBNAME")
        web_redis_host     = os.getenv("WEB_REDIS_HOST")
        web_redis_port     = os.getenv("WEB_REDIS_PORT")
        web_redis_db       = os.getenv("WEB_REDIS_DB")
    except Exception as err:
        print ("environment err"+str(err))
        gb_configenv = False

    if server_port is None:
        gb_configenv = False

    gs_web_config="/opt/configs/web-server.json"
    web_config={}
    try:
        with open(gs_web_config) as data_file:
            web_config = json.load(data_file)
        if server_port is None:
            gi_server_port     = web_config["server_port"  ]

        if gs_web_mysql_host is None:
            gs_web_mysql_host       = web_config["web_mysql_host"    ]
        if gi_web_mysql_port is None:
            gi_web_mysql_port       = int (web_config["web_mysql_port"    ])
        if gs_web_mysql_username is None:
            gs_web_mysql_username   = web_config["web_mysql_username"]
        if gs_web_mysql_password is None:
            gs_web_mysql_password   = web_config["web_mysql_password"]
        if gs_web_mysql_dbname is None:
            gs_web_mysql_dbname     = web_config["web_mysql_dbname"  ]

        if gs_web_redis_host is None:
            gs_web_redis_host       = web_config["web_redis_host"]
        if gi_web_redis_port is None:
            gi_web_redis_port       = int(web_config["web_redis_port"])
        if gi_web_redis_db is None:
            gi_web_redis_db         = int(web_config["web_redis_db"])

        gb_configfile = True
    except Exception as err:
        print ("conf err"+str(err))
        gb_configfile = False
        gi_server_port = 8000

    gs_hostname = socket.gethostname()
    # Redis connection
    gb_redischeck = gs_web_redis_host != None
    if gb_redischeck :
        try:
            go_rs_client = redis.StrictRedis(host=gs_web_redis_host, port=gi_web_redis_port, db=gi_web_redis_db)
    #    print (str(go_rs_client))
            RedisCheck()
        except redis.ConnectionError as e:
            print("Redis Error connection:", e)
            gb_redisconnection = False

    # mysql connection
    gb_mysqlcheck = gs_web_mysql_host != None
    if gb_mysqlcheck :
        try:
            go_ms_client = mysql.connector.connect(host=gs_web_mysql_host,port=gi_web_mysql_port,database=gs_web_mysql_dbname,user=gs_web_mysql_username,password=gs_web_mysql_password)
            print (str(go_ms_client))
            MysqlCheck(True)
        except mysql.connector.Error as err:
            print("Mysql Error connection:", err)
            gb_mysqlconnection = False

    #запускаем метрики
    # Функция для запуска HTTP-сервера на порту 9100 для метрик
    start_http_server(gi_metrics_port)
    print(f'Listening on port {gi_metrics_port} for /metrics ...')

    # Создаем поток для главного сервера
    main_thread = threading.Thread(target=run_main_server)

    # Запускаем потоки
    main_thread.start()

    # Ожидаем завершения потоков
    main_thread.join()
#EOF
