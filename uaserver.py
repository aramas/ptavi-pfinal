#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import SocketServer
import sys
import os
import time

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

entrada = sys.argv
if len(entrada) != 2:
    print "Usage: python uaserver.py config"
    raise SystemExit

CONFIG = entrada[1]


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

AUDIO = listaXML[5][1]['path']


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    Guardar_inv = {'ip': "", 'port_audio': 0}

    def handle(self):
    # Escribe dirección y puerto del cliente (de tupla client_address)
        metodos = ["INVITE", "ACK", "BYE"]
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            print line
            split_line = line.split(" ")
            metodo = split_line[0]
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            print "El cliente nos manda " + line
            log_w = "Received from " + listaXML[3][1]['ip'] + (':')
            log_w += str(listaXML[3][1]['puerto']) + (": ")
            log_w += line.replace("\r\n", " ")
            log(log_w)
            if metodo == "INVITE":
                self.Guardar_inv['ip'] = split_line[5]
                self.Guardar_inv['port_audio'] = split_line[7]
                Mensaje = 'SIP/2.0 100 Trying\r\n\r\n'
                Mensaje += 'SIP/2.0 180 Ring\r\n\r\n'
                Mensaje += 'SIP/2.0 200 OK\r\n\r\n'
                Mensaje += "Content-Type: application/sdp\r\n\r\n"
                Mensaje += "v=0\r\n" + "o= " + listaXML[0][1]['username']
                Mensaje += " " + listaXML[1][1]['ip'] + '\r\n'
                Mensaje += "s=misesion\r\n" + "t=0\r\n" + "m=audio "
                Mensaje += listaXML[2][1]['puerto'] + " RTP"
                print "Enviando: " + Mensaje
                self.wfile.write(Mensaje)
                log_w = "Sent to " + listaXML[3][1]['ip'] + (':')
                log_w += str(listaXML[3][1]['puerto']) + (": ")
                log_w += Mensaje.replace("\r\n", " ")
                log(log_w)
            elif metodo == "BYE":
                Mensaje = 'SIP/2.0 200 OK\r\n\r\n'
                print "Enviando: " + Mensaje
                self.wfile.write(Mensaje)
                log_w = "Sent to " + listaXML[3][1]['ip'] + (':')
                log_w += str(listaXML[3][1]['puerto']) + (": ")
                log_w += Mensaje.replace("\r\n", " ")
                log(log_w)
            elif metodo == "ACK":
                aEjecutar = './mp32rtp -i ' + self.Guardar_inv['ip'] + ' -p '
                aEjecutar += self.Guardar_inv['port_audio'] + ' < ' + AUDIO
                os.system('chmod 755 mp32rtp')
                print "vamos a ejecutar...", aEjecutar
                os.system(aEjecutar)
            elif metodo not in metodos:
                Mensaje = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(Mensaje)
                log_w = "Error: 405 Method Not Allowed"
                log(log_w)
            else:
                Mensaje = 'SIP/2.0 400 Bad Request\r\n\r\n'
                self.wfile.write(Mensaje)
                log_w = "Error: 400 Bad Request"
                log(log_w)

IP = listaXML[1][1]['ip']
PUERTO = listaXML[1][1]['puerto']

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    serv = SocketServer.UDPServer((IP, int(PUERTO)), EchoHandler)
    print "Listening..."
    serv.serve_forever()
