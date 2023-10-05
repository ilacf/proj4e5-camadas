from enlace import *
from enlaceRx import *
import time
import numpy as np
from datetime import datetime
from crc import Crc16, Calculator

#   python -m serial.tools.list_ports

serialName = "COM6"
CRC = Calculator(Crc16.CCITT)

def envio(eop, pedacos, com1):
    qntd_pacotes = len(pedacos)
    i = 0
    x = 0
    
    # para simulacoes de erro, descomentar linha abaixo:
    # erro = True

    while i <= qntd_pacotes:

        if i != qntd_pacotes:

            # simulando erro de arquivo fora de ordem
            # if i == 1 and erro == True:
            #     i = 2

            # simulando erro de arquivo sendo enviado repetidamente
            # if i == 1 and erro == True:
            #     i = 0

            payload = pedacos[i]

            enviar_prox = False
            tamanho_pl = len(pedacos[i])
            h0 = (3).to_bytes(1, byteorder="big")
            h1 = b'\x00'
            h2 = b'\x00'
            h3 = (qntd_pacotes).to_bytes(1, byteorder='big')
            h4 = (i).to_bytes(1, byteorder='big')
            h5 = (tamanho_pl).to_bytes(1, byteorder='big')
            h6 = (x).to_bytes(1, byteorder='big')
            h7 = (x).to_bytes(1, byteorder='big')
            h8_9 = (CRC.checksum(payload)).to_bytes(2, byteorder='big') # crcs
            head_pacote = h0 + h1 + h2 + h3 + h4 + h5 + h6 + h7 + h8_9

            com1.sendData(np.asarray(head_pacote + payload + eop))
            time.sleep(0.1)
            arquivo('client1.txt', head_pacote, payload, eop, 'envio')

        timer2 = time.time()
        if time.time()-timer2 < 20:

            timer1 = time.time()
            while time.time()-timer1 < 5:
                if com1.rx.getIsEmpty() == False:
                    head_confirm, _ = com1.getData(10)
                    confirm, _ = com1.getData(head_confirm[5])
                    eop_confirm, _ = com1.getData(4)
                    if eop_confirm == eop and (head_confirm[0] == 4 or head_confirm[0] == 6):
                        # aa = recebeu certo, bb = recebeu errado, cc = recebeu ultimo
                        if confirm == b'\xaa':
                            print(f"\nconfirmou recebimento do pacote {i} corretamente")
                            arquivo('client1.txt', head_confirm, confirm, eop_confirm, 'receb')
                            x = i               
                            i += 1
                            enviar_prox = True
                            break
                        elif confirm == b'\xbb' and head_confirm[0] == 6: # recebeu mensagem t6 que arquivo foi corrompido
                            print(f"\nrecebeu pacote {i} corrompido")
                            enviar_prox = True
                            break
                        elif confirm == b'\xcc' and head_confirm[0] == 6: # recebeu mensagem t6 que o arquivo veio fora de ordem
                            print("\nrecebeu pacote fora de ordem ou repetido")
                            if (head_confirm[2]).to_bytes(1, byteorder='big') == b'\xaa':
                                arquivo('client2.txt', head_confirm, confirm, eop_confirm, 'receb', 'fora de ordem')
                            elif (head_confirm[2]).to_bytes(1, byteorder='big') == b'\xbb':
                                arquivo('client2.txt', head_confirm, confirm, eop_confirm, 'receb', 'repetido')

                            # durante simulacao de erro:
                            # erro = False

                            i = x + 1
                            enviar_prox = True
                            break
                        elif confirm == b'\xdd':
                            print(f"\nterminou de receber os pacotes corretamente")
                            return True
                        
            if enviar_prox == True:
                continue        
            print("\nservidor nao respondeu, reenviando pacote")

        else: # timeout
            print("\nservidor nao respondeu nenhuma das tentativas de envio do pacote. \n TIMEOUT")
            head_to = (5).to_bytes(1, byteorder="big") + b'\x00'*9
            pl_to = b'\x00'
            com1.sendData(head_to + pl_to + eop)
            time.sleep(0.1)
            arquivo('client3.txt', head_to, pl_to, eop, 'envio')
            return None
        
def arquivo(nome, head, pl, eop, env_receb, tipo_de_erro=''):
    data_hora = datetime.now()
    tipo = head[0]
    tamanho_bytes = len(head + pl + eop)
    conteudo = f"{data_hora} / {env_receb} / {tipo} / {tamanho_bytes}"
    if tipo == 3:
        conteudo += f" / {head[4]} / {head[3]} / crc"
        if tipo_de_erro != '':
            conteudo += f" / {tipo_de_erro}"
    elif tipo == 1 or tipo == 2:
        conteudo += " / handshake"
    with open(f"{nome}", "a") as file:
        file.write(conteudo)
        file.write("\n")

def main():
    try:
        print("Iniciou o main\n")

        com1 = enlace(serialName)
        com1.enable()

        # byte de sacrificio
        time.sleep(.2)
        com1.sendData(b'00')
        time.sleep(0.1)

        print("Abriu a comunicação\n")

        eop = b'\xaa\xbb\xcc\xdd'

        pedacos = []
        img = open('img.png', 'rb').read()
        x = len(img) / 144
        for pedaco in range(round(x)):
            pedacos.append(img[(pedaco*144):((pedaco*144)+144)])
        print(f"quantidade de pacotes: {len(pedacos)}\n")

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
        arquivo('client1.txt', h_head, h_payload, eop, 'envio')

        # receber quantidade de comandos recebida pelo server
        hd = False
        comeco = time.time()
        while time.time()-comeco < 5:
            if com1.rx.getIsEmpty() == False:
                hd = True
                head_receb, _ = com1.getData(10)
                pl_receb, _ = com1.getData(head_receb[5])
                eop_receb, _ = com1.getData(4)
                if head_receb[0] == 2 and eop_receb == b'\xaa\xbb\xcc\xdd':
                    arquivo('client1.txt', head_receb, pl_receb, eop_receb, 'receb')
                    resposta = envio(eop, pedacos, com1)
                    if resposta == True:
                        print("envio de dados terminado com sucesso")
                    else:
                        break
        
        if hd == False:
            # timeout
            print("reiniciar timer")
            head_to = (5).to_bytes(1, byteorder="big") + b'\x00'*9
            pl_to = b'\x00'
            datagrama = head_to + pl_to + eop
            com1.sendData(datagrama)
            time.sleep(0.1)
            print("TIMEOUT")
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