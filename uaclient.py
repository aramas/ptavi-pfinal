#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys

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

# Contenido que vamos a enviar
if METODO == 'REGISTER':
    LINE = METODO + " sip:" + listaXML[0][1]['username'] + (':')
    LINE += listaXML[1][1]['puerto'] + ' SIP/2.0\r\n' + "Expires: " + OPTION
    print LINE
elif METODO == 'INVITE':
    LINE = METODO + " sip:" + OPTION + ' SIP/2.0\r\n'
    LINE += "Content-Type: application/sdp\r\n\r\n"
    LINE += "v=0\r\n" + "o= " + listaXML[0][1]['username']
    LINE += " " + listaXML[1][1]['ip'] + '\r\n'
    LINE += "s=misesion\r\n" + "t=0\r\n" + "m=audio"
elif METODO == 'BYE':
    LINE = METODO + " sip:" + OPTION + 'SIP/2.0\r\n\r\n'
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
        print "Enviando: " + LINE
except socket.error:
        print "20101018160243 Error: No server listening at " + listaXML[3][1]['ip'] + " port " + listaXML[3][1]['puerto']
        raise SystemExit

print 'Recibido -- ', data

#data_troz = data.split('\r\n\r\n')

#if METODO == "INVITE" and data_troz[2] == 'SIP/2.0 200 OK':
#        LINE = "ACK" + " sip:" + SPLIT_PORT[0] + ' SIP/2.0\r\n\r\n'
#        print "Enviando: " + LINE
#        my_socket.send(LINE)
#        data = my_socket.recv(1024)


print "Terminando socket..."

# Cerramos todo
my_socket.close()
print "Fin."
