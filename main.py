#!/usr/bin/python3
# -*- coding: utf-8 -*-
#īśvaraḥ paramaḥ kṛṣṇaḥ
#sac-cid-ānanda-vigrahaḥ
#anādir ādir govindaḥ
#sarva-kāraṇa-kāraṇam
#----------------------------
#Om Namo Bhagavate Vasudevaya

import os
os.chdir('/home/pi/bin/salamigal')
#Setup logging
import logging
import logging.config
logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('root')
nologging = logging.NullHandler()
nologging.setLevel(logging.DEBUG)

#START load modules
logging.info("Loading modules...")

import time
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
import tornado.autoreload
from tornado.options import define, options
import traceback
import json
import uuid
import base64
import multiprocessing
from urllib.parse import urlparse
from tornado.escape import xhtml_escape
import salamigalnet
import RPi.GPIO as GPIO

logging.info("Modules loaded.")
#END load modules

#START deklarasi variable konfigurasi
clients = dict()
guests = dict()
sampah = dict()
#END deklarasi variable konfigurasi


logging.info("Starting server, please wait...")
#START deklarasi handler


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        try:
            #self.set_nodelay(True)
            self.sid = str(uuid.uuid4())
            self.name = 'Guest-{}'.format(len(guests))
            self.status = 'unauth'
            guests[self.sid] =    {
                    'client' : self,
                    'sid' : self.sid,
                    'name' : self.name,
                    'status': self.status,
                    'ip': self.request.remote_ip
            }
            logging.info(("{} opening websocket").format(guests[self.sid]['ip']))
        except Exception as err:
            logging.error("%s", traceback.format_exc())
        pass

    def on_message(self, message):
        try:

            #get queue fromt process networking
            queue_networkingProc = self.application.settings.get('queue_networkingProc')
            #authentication
            if(True):
                #Do dummy auth
                if(guests[self.sid]['sid'] not in clients):
                    clients[self.sid] = guests[self.sid]
                    clients[self.sid]['status'] = 'auth'
                    logging.info(("{} websocket connected!").format(guests[self.sid]['ip']))
                
                #Message parsing
                #print('Received: {}'.format(message))
                msg = json.loads(message)
                #Initialization
                if(msg['task'] == 'init'):
                    q = {
                        'init': {
                            'sid' : clients[self.sid]['sid']
                        }
                    }
                    self.write_message(q)
                
                #Command
                elif(msg['task'] == 'command'):
                    q = {
                        'task': 'command',
                        'cmd': msg['cmd'],
                        'arg': msg['arg'],
                        'sid': clients[self.sid]['sid'],
                        'mid': msg['$id']
                    }
                    queue_networkingProc.put(q)
            
        except Exception as err:
            logging.error(" %s", traceback.format_exc())
            pass

    def on_close(self):
        try:
            if self.sid in clients:
                logging.info(("Client {} closed websocket").format(clients[self.sid]['ip']))
                clients[self.sid]['status'] = 'die'
                sampah[self.sid] = clients[self.sid]
            if self.sid in guests:
                del guests[self.sid]
        except Exception as err:
            pass
            logging.error("%s", traceback.format_exc())

#END deklarasi handler



################################ MAIN ################################
def main():
    #Queue untuk prosess networking
    taskQ_networkingProc = multiprocessing.Queue()
    resultQ_networkingProc = multiprocessing.Queue()


    #instansiasi proses networking dengan multiprocessing
    networkingProc = salamigalnet.SalamigalNetworking(taskQ_networkingProc,
        resultQ_networkingProc)
    networkingProc.daemon = True
    networkingProc.start()

    #tunggu 0 detik untuk inisialisasi proses
    #time.sleep(0)

    logging.getLogger("tornado.access").addHandler(nologging)
    logging.getLogger("tornado.access").propagate = False
    tornado.options.parse_command_line()
    tornado.locale.load_gettext_translations('locale', 'messages')
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/ws", WebSocketHandler),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static'})
        ],  compiled_template_cache=False,
            queue_networkingProc=taskQ_networkingProc,
            debug=True,template_path='template'
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen('80','0.0.0.0')

    #fungsi untuk melakukan pembersihan rutin,
    #seperti penghapusan client-client yang sudah tidak bernyawa
    def routine_cleanUp():
        #clean up...
        try:
            for s in sampah:
                del clients[s]
            sampah.clear()
        except Exception as err:
            logging.error("%s", traceback.format_exc())
            pass

    #fungsi untuk mengecek result dari process networkingProc
    #(callback dari scheduler_networkingProc)
    def CR_networkingProc():
        try:
            if not resultQ_networkingProc.empty():
                result = resultQ_networkingProc.get()
                #komunikasi antar process
                if(result['to'] == 'sys'):
                    if(result['cmd'] == 'send#frame_proc'):
                        taskQ_frameProc.put(result['data']);

                else:
                    for c in clients:
                        #clean up client
                        if(clients[c]['status'] == 'die'):
                            logging.info("Memindahkan client %s(Status Die)",
                                 c)
                            #del clients[c]
                            sampah[c] = clients[c]
                        else:
                            if(clients[c]['status'] == 'auth'):
                                #broadcast ke semua client
                                if(not result['is_binary'] and result['to'] == '*'):
                                    clients[c]['client'].write_message(
                                        result['data'])
                                elif(result['is_binary'] and result['to'] == '*'):
                                    clients[c]['client'].write_message(
                                        result['data'], binary=True)                                
                            
                                #komunikasi dengan client tertentu
                                elif(not result['is_binary'] and result['to'] == clients[c]['sid']):
                                    clients[c]['client'].write_message(
                                        result['data'])
                            
                                elif(result['is_binary'] and result['to'] == clients[c]['sid']):
                                    clients[c]['client'].write_message(
                                        result['data'], binary=True)

        except Exception as err:
            logging.error("%s", traceback.format_exc())
            pass
            
    mainLoop = tornado.ioloop.IOLoop.instance()
    
    scheduler_networkingProc = tornado.ioloop.PeriodicCallback(
        CR_networkingProc, 5, io_loop = mainLoop)
    scheduler_networkingProc.start()
    
    scheduler_routineProc = tornado.ioloop.PeriodicCallback(
        routine_cleanUp, 100, io_loop = mainLoop)
    scheduler_routineProc.start()

    logging.info("*** Ready, server started!")   
    mainLoop.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        logging.info("*** Finish, server stopped!")   