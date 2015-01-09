#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import SocketServer
import socket
import sys
import os
import time

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

entrada = sys.argv
if len(entrada) != 2:
    print "Usage: python proxy_registrar.py config"
    raise SystemExit

CONFIG = entrada[1]


def log(log_w):
    fichero = listaXML[2][1]['path']
    fich = open(fichero, 'a')
    hora = time.time()
    fich.write(time.strftime('%Y%m%d%H%M%S', time.gmtime(hora)))
    fich.write(" " + log_w + "\r\n")
    fich.close()


class XML(ContentHandler):

    def __init__(self):

        self.taglist = []
        self.etiquetas = [
            'server', 'database', 'log']
        self.atribs = {
            'server': ["name", "ip", "puerto"],
            'database': ["path", "passwdpath"],
            'log': ["path"]}

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


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """
    dic_client = {}
    datos_cliente = []

    def register2file(self):
        """
        Metodo para copiar los datos de los usuarios a un archivo
        """
        fich = open("registered.txt", "w")
        CAMPOS = "User" + '\t' + "IP" + '\t' + "Puerto" + '\t' "Expires"
        CAMPOS += '\r\n'
        fich.write(CAMPOS)
        for Usuario in self.dic_client.keys():
            fich.write(Usuario + '\t' + self.dic_client[Usuario][0] + '\t'
                       + self.dic_client[Usuario][1] + '\t'
                       + time.strftime('%Y-%m-%d %H:%M:%S',
                       time.gmtime(self.dic_client[Usuario][2])) + '\r\n')
        fich.close()

    def handle(self):
        """
        Metodo para manejar los datos de los usuarios
        """
        print self.client_address
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            mensaje = self.rfile.read()
            if not mensaje:
                break
            else:
                log_w = "Receive from " + self.client_address[0] + (":")
                log_w += str(self.client_address[1]) + (": ")
                log_w += mensaje.replace("\r\n", " ")
                log(log_w)
                lista_mensaje = mensaje.split(" ")
                print lista_mensaje
            if lista_mensaje[0] == "REGISTER":
                datos_sip = lista_mensaje[1].split(":")
                print datos_sip
                sip = datos_sip[1]
                puerto = datos_sip[2]
                expires = lista_mensaje[3]
                ip = self.client_address[0]
                hora_exp = int(time.time()) + int(expires)
                self.datos_cliente = [ip, puerto, hora_exp]
                self.dic_client[sip] = self.datos_cliente
                mensaje = "SIP/2.0" + " 200 " + 'OK\r\n\r\n'
                self.wfile.write(mensaje)
                log_w = "Sent to " + ip + (":") + str(puerto) + (": ")
                log_w += mensaje.replace("\r\n", " ")
                log(log_w)
                # Borramos en caso de expires 0
                for Usuario in self.dic_client.keys():
                    if int(time.time()) >= self.dic_client[Usuario][2]:
                        del self.dic_client[Usuario]
            elif lista_mensaje[0] == "INVITE" or lista_mensaje[0] == "ACK" or lista_mensaje[0] == "BYE":
                datos_sip = lista_mensaje[1].split(":")
                print datos_sip
                sip = datos_sip[1]
                # Enviaremos el INVITE al UA que nos indique el mensaje.
                try:
                    IP_ENV = self.dic_client[sip][0]
                    PORT_ENV = self.dic_client[sip][1]
                    my_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM)
                    my_socket.setsockopt(
                        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_socket.connect((IP_ENV, int(PORT_ENV)))
                    my_socket.send(mensaje)
                    log_w = "Sent to " + IP_ENV + (":") + PORT_ENV + (": ")
                    log_w += mensaje.replace("\r\n", " ")
                    log(log_w)
                    # Recibimos si el reenvio es un INVITE
                    if lista_mensaje[0] == "INVITE" or lista_mensaje[0] == "BYE":
                        data = my_socket.recv(1024)
                        print "Recibido -- " + data
                        self.wfile.write(data)
                        log_w = "Sent to " + self.client_address[0] + (":")
                        log_w = str(self.client_address[1]) + (": ")
                        log_w += data.replace("\r\n", " ")
                        log(log_w)
                except:
                    mensaje = "SIP/2.0 404 User Not Found\r\n\r\n"
                    self.wfile.write(mensaje)
            print mensaje + '\r\n\r\n'
            print self.dic_client
            self.register2file()

PUERTO = listaXML[0][1]['puerto']
IP = listaXML[0][1]['ip']

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    serv = SocketServer.UDPServer((IP, int(PUERTO)), SIPRegisterHandler)
    print "Lanzando Registrar listening at port " + PUERTO
    serv.serve_forever()
