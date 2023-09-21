#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
#Carareto
#17/02/2018
#  Camada de Enlace
####################################################

# Importa pacote de tempo
import time

# Threads
import threading

# Class
class RX(object):
  
    def __init__(self, fisica):
        self.fisica      = fisica
        self.buffer      = bytes(bytearray())
        self.threadStop  = False
        self.threadMutex = True
        self.READLEN     = 1024

    def thread(self): 
        while not self.threadStop:
            if(self.threadMutex == True):
                rxTemp, nRx = self.fisica.read(self.READLEN)
                if (nRx > 0):
                    self.buffer += rxTemp  
                time.sleep(0.01)

    def threadStart(self):       
        self.thread = threading.Thread(target=self.thread, args=())
        self.thread.start()

    def threadKill(self):
        self.threadStop = True

    def threadPause(self):
        self.threadMutex = False

    def threadResume(self):
        self.threadMutex = True

    def getIsEmpty(self):
        if(self.getBufferLen() == 0):
            return(True)
        else:
            return(False)

    def getBufferLen(self):
        return(len(self.buffer))
    # pega quantidade de bytes armazenados no buffer no momento

    def getAllBuffer(self, len):
        self.threadPause()
        b = self.buffer[:]
        self.clearBuffer()
        self.threadResume()
        return(b)
    # no geral pega todos os bytes que estao armazenados no buffer para ler:
    # primeiro pausa a passagem de dados para o buffer, depois guarda todos os bytes armazenados
    # na variavel b, limpa o buffer, apagando todos os bytes e depois resume a passagem de dados
    # para o buffer, alem de retornar a variavel b

    def getBuffer(self, nData):
        self.threadPause()
        b           = self.buffer[0:nData]
        self.buffer = self.buffer[nData:]
        self.threadResume()
        return(b)
    # no geral pega uma certa quantidade de bytes:
    # primeiro pausa a transmissao de bytes para o buffer, salva todos os bytes do inicio ate um 
    # certo indice (recebido na chamada da funcao) na variavel b, guarda so o resto dos bytes de volta
    # no buffer, resume o thread e retorna b 

    def getNData(self, size):
        while(self.getBufferLen() < size):
            time.sleep(0.05)                 
        return(self.getBuffer(size))
    # enquanto o buffer nao tiver a quantidade de bytes recebida na chamada da funcao (param )size, 
    # o buffer fica recebendo mais bytes ate chegar no tamanho certo. A funcao retorna so a quantidade 
    # de bytes escolhido. (nao o valor da quantidade, os bytes em si)

    def clearBuffer(self):
        self.buffer = b""


