from enlace import *
from enlaceRx import *
import time
import numpy as np

#   python -m serial.tools.list_ports

serialName = "COM3"

def envio(eop, pedacos, head_receb, com1):
    qntd_pacotes = head_receb[3]
    i = 0
    x = 0
    timer2 = time.time()-0.15
    while i <= qntd_pacotes:
        enviar_prox = False
        tamanho_pl = len(pedacos[i])
        h0 = (3).to_bytes(1, byteorder="big")
        h1 = b'\x00'
        h2 = b'\x00'
        h3 = qntd_pacotes
        h4 = (i).to_bytes(1, byteorder='big')
        h5 = tamanho_pl
        h6 = (i).to_bytes(1, byteorder='big')
        h7 = (x).to_bytes(1, byteorder='big')
        h8 = b'\x00' # crc1
        h9 = b'\x00' # crc2
        head_pacote = h0 + h1 + h2 + h3 + h4 + h5 + h6 + h7 + h8 + h9

        payload = pedacos[i]

        com1.sendData(np.asarray(head_pacote + payload + eop))
        time.sleep(0.1)
        print("enviando pacote (mensagem t3)")

        if time.time()-timer2 < 20:

            timer1 = time.time()
            while time.time()-timer1 < 5:
                print("iniciou timer1 de 5 segundos")
                if com1.rx.getIsEmpty() == False:
                    head_confirm, _ = com1.getData(10)
                    confirm, _ = com1.getData(head_confirm[5])
                    eop_confirm, _ = com1.getData(4)
                    if eop_confirm == eop and head_confirm[0] == (4).to_bytes(1, byteorder='big'):
                        # aa = recebeu certo, bb = recebeu errado, cc = recebeu ultimo
                        if confirm == b'\xaa':
                            print(f"confirmou recebimento do pacote {i} corretamente")
                            i += 1
                            enviar_prox = True
                            break
                        elif confirm == b'\xbb': # recebeu mensagem t6
                            print(f"recebeu pacote {i} corrompido")
                            enviar_prox = True
                            break
                        elif confirm == b'\xcc':
                            print(f"terminou de receber os pacotes corretamente")
                            return True
            if enviar_prox == True:
                continue        
            print("servidor nao respondeu, reenviando pacote")

        else: # timeout
            print("servidor nao respondeu nenhuma das 4 tentativas de envio do pacote. \n TIMEOUT")
            head_to = (5).to_bytes(1, byteorder="big") + b'\x00'*9
            pl_to = b'\x00'
            com1.sendData(head_to + pl_to + eop)
            time.sleep(0.1)
            print("Mensagem de timeout (t5) enviada")
            return None

def main():
    try:
        print("Iniciou o main")

        com1 = enlace(serialName)
        com1.enable()

        # byte de sacrificio
        time.sleep(.2)
        com1.sendData(b'00')
        time.sleep(0.1)

        print("Abriu a comunicação")

        eop = b'\xaa\xbb\xcc\xdd'

        pedacos = []
        img = open('img.png', 'rb').read()
        x = len(img) / 144
        for pedaco in range(round(x)):
            pedacos.append(img[(pedaco*144):((pedaco*144)+144)])

        # montagem do handshake 
        h_h0 = (1).to_bytes(1, byteorder="big") # tipo da mensagem
        h_h1 = (1).to_bytes(1, byteorder="big") # numero do servidor (1)
        h_h2 = b'\x00' # livre (00)
        h_h3 = (len(pedacos)).to_bytes(1, byteorder="big") # total de pacotes
        h_h4 = b'\x00' # pacote sendo enviado
        h_h5 = (1).to_bytes(1, byteorder="big") # id do arquivo (1)
        h_h6 = b'\x00' # numero do pacote que tem q reenviar se der erro (igual numero do pacote sendo enviado)
        h_h7 = b'\x00' # numero do ultimo pacote que foi enviado corretamente
        h_h8 = b'\x00' # crc1
        h_h9 = b'\x00' # crc2
        h_head = h_h0 + h_h1 + h_h2 + h_h3 + h_h4 + h_h5 + h_h6 + h_h7 + h_h8 + h_h9

        h_payload = b'\x00' # eh o handshake, ent so envia 00

        com1.sendData(np.asarray(h_head + h_payload + eop))
        time.sleep(0.1)
        print("enviei msg t1")

        # receber quantidade de comandos recebida pelo server
        hd = False
        comeco = time.time()
        print("iniciando timer de 5 segundos")
        while time.time()-comeco < 5:
            if com1.rx.getIsEmpty() == False:
                hd = True
                head_receb, _ = com1.getData(10)
                pl_receb, _ = com1.getData(head_receb[2])
                eop_receb, _ = com1.getData(3)
                if pl_receb == b'\x01' and eop_receb == b'\xaa\xbb\xcc\xdd':
                    print("mensagem t2 (handshake) recebida com sucesso")
                    resposta = envio(eop, pedacos, head_receb, com1)
                    if resposta == True:
                        print("envio de dados terminado com sucesso")
                    else:
                        break
        
        if hd == False:
            # timeout
            print("reiniciar timer")
            head_to = (5).to_bytes(1, byteorder="big") + b'\x00'*9
            pl_to = b'\x00'
            com1.sendData(head_to + pl_to + eop)
            time.sleep(0.1)
            print("Mensagem de timeout (t3) enviada")
            com1.disable()
            main()

        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com1.disable()
        
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()
        
if __name__ == "__main__":
    main()