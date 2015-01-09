#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import os
import time

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

entrada = sys.argv

if len(entrada) != 4:
    print "Usage: python uaclient.py config method option"
    raise SystemExit
# Cliente UDP simple.

# Dirección IP del servidor.
CONFIG = entrada[1]
METODO = entrada[2].upper()
OPTION = entrada[3]


def log(log_w):
    fichero = listaXML[4][1]['path']
    fich = open(fichero, 'a')
    hora = time.time()
    fich.write(time.strftime('%Y%m%d%H%M%S', time.gmtime(hora)))
    fich.write(" " + log_w + '\r\n')
    fich.close()


class XML(ContentHandler):

    def __init__(self):

        self.taglist = []
        self.etiquetas = [
            'account', 'uaserver', 'rtpaudio', 'regproxy', 'log', 'audio']
        self.atribs = {
            'account': ["username", "passwd"],
            'uaserver': ["ip", "puerto"],
            'rtpaudio': ["puerto"],
            'regproxy': ["ip", "puerto"],
            'log': ["path"],
            'audio': ["path"]}

    def startElement(self, name, attrs):
        self.dict = {}
        if name in self.etiquetas:
            for atributo in self.atribs[name]:
                self.dict[atributo] = attrs.get(atributo, "")
            self.taglist.append([name, self.dict])

    def get_tags(self):
        return self.taglist

parser = make_parser()
xmlHandler = XML()
parser.setContentHandler(xmlHandler)
parser.parse(open(CONFIG))
print xmlHandler.get_tags()
listaXML = xmlHandler.get_tags()

log_w = "Starting..."
log(log_w)

# Contenido que vamos a enviar
if METODO == 'REGISTER':
    LINE = METODO + " sip:" + listaXML[0][1]['username'] + (':')
    LINE += listaXML[1][1]['puerto'] + ' SIP/2.0\r\n' + "Expires: " + OPTION
    LINE += '\r\n\r\n'
    print LINE
elif METODO == 'INVITE':
    LINE = METODO + " sip:" + OPTION + ' SIP/2.0\r\n'
    LINE += "Content-Type: application/sdp\r\n\r\n"
    LINE += "v=0\r\n" + "o= " + listaXML[0][1]['username']
    LINE += " " + listaXML[1][1]['ip'] + ' \r\n'
    LINE += "s=misesion\r\n" + "t=0\r\n" + "m=audio "
    LINE += listaXML[2][1]['puerto'] + " RTP"
elif METODO == 'BYE':
    LINE = METODO + " sip:" + OPTION + ' SIP/2.0\r\n\r\n'
else:
    print "Error: Invalid Method"
    raise SystemExit
print listaXML[3][1]['ip']
print listaXML[3][1]['puerto']

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((listaXML[3][1]['ip'], int(listaXML[3][1]['puerto'])))
try:
    my_socket.send(LINE)
    data = my_socket.recv(1024)
    log_w = "Sent to " + listaXML[3][1]['ip'] + (':')
    log_w += str(listaXML[3][1]['puerto']) + (": ") + LINE.replace("\r\n", " ")
    log(log_w)
    print "Enviando: " + LINE
except socket.error:
    print "20101018160243 Error: No server listening at " + listaXML[3][1]['ip'] + " port " + listaXML[3][1]['puerto']
    log_w = "Error: " + "No server listening at " + listaXML[3][1]['ip']
    log_w += " port " + listaXML[3][1]['puerto']
    log(log_w)
    raise SystemExit

print 'Recibido -- ', data
log_w = "Received from " + listaXML[3][1]['ip'] + (':')
log_w += str(listaXML[3][1]['puerto']) + (": ") + data.replace("\r\n", " ")
log(log_w)

if data != "SIP/2.0 404 User Not Found\r\n\r\n":

    data_troz = data.split('\r\n\r\n')

    if METODO == "INVITE" and data_troz[2] == 'SIP/2.0 200 OK':
        data_sdp = data_troz[4].split('\r\n')
        data_o = data_sdp[1].split(' ')
        data_audio = data_sdp[4].split(' ')
        username = data_o[0]
        ip = data_o[2]
        port_audio = data_audio[1]
        LINE = "ACK" + " sip:" + OPTION + ' SIP/2.0\r\n\r\n'
        log_w = "Sent to " + listaXML[3][1]['ip'] + (':')
        log_w += str(listaXML[3][1]['puerto']) + (": ")
        log_w += LINE.replace("\r\n", " ")
        log(log_w)
        print "Enviando: " + LINE
        my_socket.send(LINE)
        data = my_socket.recv(1024)
        AUDIO = listaXML[5][1]['path']
        aEjecutar = './mp32rtp -i ' + ip + ' -p ' + port_audio + ' < ' + AUDIO
        os.system('chmod 755 mp32rtp')
        print "vamos a ejecutar...", aEjecutar
        os.system(aEjecutar)


print "Terminando socket..."

# Cerramos todo
log_w = "Finishing"
log(log_w)
my_socket.close()
print "Fin."
