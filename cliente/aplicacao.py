from enlace import *
from enlaceRx import *
import time
import numpy as np

#   python -m serial.tools.list_ports

serialName = "COM3"

def envio(eop, pedacos, head_receb):
    qntd_pacotes = head_receb[3]
    i = 0
    while i <= qntd_pacotes:
        head_pacote = (3).to_bytes(1, byteorder="big") + b'\x00\x00'


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
        h_h4 = (1).to_bytes(1, byteorder="big") # id do arquivo (1)
        h_h5 = b'\x00' # pacote sendo enviado
        h_h6 = b'\x00' # numero do pacote que tem q reenviar se der erro (igual numero do pacote sendo enviado)
        h_h7 = b'\x00' # numero do ultimo pacote que foi enviado corretamente
        h_h8 = b'\x00' # crc1
        h_h9 = b'\x00' # crc2
        h_head = h_h0 + h_h1 + h_h2 + h_h3 + h_h4 + h_h5 + h_h6 + h_h7 + h_h8 + h_h9

        h_payload = b'\x00' # eh o handshake, ent so envia 00

        com1.sendData(np.asarray(h_head + h_payload + eop))
        time.sleep(0.1)

        # receber quantidade de comandos recebida pelo server
        hd = False
        comeco = time.time()
        while time.time()-comeco < 5:
            if com1.rx.getIsEmpty() == False:
                head_receb, _ = com1.getData(12)
                pl_receb, _ = com1.getData(head_receb[2])
                eop_receb, _ = com1.getData(3)
                if pl_receb == b'\x01' and eop_receb == b'\xaa\xbb\xcc\xdd':
                    envio(eop, pedacos, head_receb)
        
        if hd == False:
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