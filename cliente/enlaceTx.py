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
class TX(object):
 
    def __init__(self, fisica):
        self.fisica      = fisica
        self.buffer      = bytes(bytearray())
        self.transLen    = 0
        self.empty       = True
        self.threadMutex = False
        self.threadStop  = False


    def thread(self):
        while not self.threadStop:
            if(self.threadMutex):
                self.transLen    = self.fisica.write(self.buffer)
                self.threadMutex = False

    def threadStart(self):
        self.thread = threading.Thread(target=self.thread, args=())
        self.thread.start()

    def threadKill(self):
        self.threadStop = True

    def threadPause(self):
        self.threadMutex = False

    def threadResume(self):
        self.threadMutex = True

    def sendBuffer(self, data):
        self.transLen   = 0
        self.buffer = data
        self.threadMutex  = True
    # zera o translen, que identifica a quantidade de bytes transmitidos, ara garantir que o valor
    # novo vai ser a quantidade certa de bytes que estao sendo transmitidos; adiciona os bytes entregues 
    # no buffer e depois resume a transmissao de bytes atraves da ativacao do threadmutex. Esse processo
    # leva à reatribuicao do valor de dados enviados para a variavel translen pq ativa a funcao thread,
    # e, apos a transmissao completa de todos os dados, desliga o threadmutex para parar de transmitir,
    # deixando assim que mais informacoes sejam carregadas ao buffer.

    def getBufferLen(self):
        return(len(self.buffer))

    def getStatus(self):
        return(self.transLen)
        
    def getIsBussy(self):
        return(self.threadMutex)

