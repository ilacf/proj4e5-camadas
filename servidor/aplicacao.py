from enlace import *
import time
import base64
import numpy as np
from datetime import datetime
from crc import Crc16, Calculator

serialName = "COM5"

crc = Calculator(Crc16.CCITT)

def arquivo(nome, head, pl, eop, env_receb, tipo_de_erro=''):
    data_hora = datetime.now()
    # tipo = int.from_bytes(head[0], byteorder='big')
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
        print("-------------------------")
        print("\nIniciou o main\n")
        print("-------------------------")
        com1 = enlace(serialName)
        com1.enable()
        print("\nAbriu a comunicação\n")
        print("-------------------------")
        print("\nEsperando Mensagem\n")
        print("-------------------------")
        _, _ = com1.getData(1)
        com1.rx.clearBuffer()
        time.sleep(1)

        eop = b'\xaa\xbb\xcc\xdd'

        ocioso = True
        
        head, _ = com1.getData(10)
        pl, _ = com1.getData(head[5])
        eop_receb, _ = com1.getData(4)

        arquivo('arquivo1.txt', head, pl, eop_receb, 'receb')

        while ocioso:
            if head[0] == 1 and head[1] == 1:
                print("\nRecebeu mensagem tipo 1\n")
                print("-------------------------")
                ocioso = False
            time.sleep(1)

        numPckg = head[3]

        recebido = ''

        h0_t2 = (2).to_bytes(1, byteorder="big")
        h1 = b'\x00'
        h2 = b'\x00'
        h3_t2 = (1).to_bytes(1, byteorder="big")
        h4_t2 = b'\x00'
        h5_t2 = (1).to_bytes(1, byteorder="big")
        h6_t2 = b'\x00'
        h7_t2 = (1).to_bytes(1, byteorder="big")
        h8_t2 = b'\x00'
        h9_t2 = b'\x00'

        head_t2 = h0_t2 + h1 + h2 + h3_t2 + h4_t2 + h5_t2 + h6_t2 + h7_t2 + h8_t2 + h9_t2

        pl_t2 = b'\x00'

        msg_t2 = head_t2 + pl_t2 + eop

        com1.sendData(np.asarray(msg_t2))
        time.sleep(0.1)
        print("\nMensagem tipo 2 enviada\n")
        print("-------------------------")

        arquivo('arquivo1.txt', head_t2, pl_t2, eop, 'envio')

        cont = 0

        print("\nIniciando recebimento de mensagem tipo 3\n")
        print("-------------------------")

        lista_packages = [-1]

        while cont <= numPckg:
            timer_1 = time.time()
            timer_2 = time.time()

            while ocioso == False:
                print(f"\nEsperando pacote de número {cont}\n")
                print("-------------------------")

                head_receb, _ = com1.getData(10)
                print(f"\nRecebeu head \n")
                for i in head_receb:
                    print(i)

                pl_receb, _ = com1.getData(head_receb[5])
                print(f"\nRecebeu payload\n")

                eop_receb, _ = com1.getData(4)
                print(f"\nRecebeu eop\n")

                print(f"\nPacote de número {cont} recebido\n")
                print("-------------------------")

                checando_crc = crc.checksum(pl_receb)

                print(f"\n{checando_crc}\n")
                print(f'\n{(head_receb[8]).to_bytes(2,byteorder="big")}\n')

                if head_receb[0] == 3 and eop_receb == eop and checando_crc == (head_receb[8]):
                    # if payload correto e num pacote esperado correto
                    if head_receb[4] >= 0 and head_receb[4] <= head_receb[3] and head_receb[4] not in lista_packages and head_receb[4] == lista_packages[-1] + 1:
                        arquivo('arquivo1.txt', head_receb, pl_receb, eop_receb, 'receb')
                        
                        print(f"\nMensagem tipo 3 recebida corretamente, pacote de número {head_receb[4]}\n")
                        print("-------------------------")

                        recebido += pl_receb

                        lista_packages.append(head_receb[4])
                        # aa = recebeu certo, bb = recebeu errado, cc = recebeu ultimo
                        h0_t4 = (4).to_bytes(1, byteorder="big")
                        h1_t4 = b'\x00'
                        h2_t4 = b'\xaa'
                        h3_t4 = (1).to_bytes(1, byteorder="big")
                        h4_t4 = b'\x00'
                        h5_t4 = (1).to_bytes(1, byteorder="big")
                        h6_t4 = b'\x00'
                        h7_t4 = (head_receb[4]).to_bytes(1, byteorder="big")
                        h8_t4 = b'\x00'
                        h9_t4 = b'\x00'

                        pl_t4 = b'\xaa'

                        head_t4 = h0_t4 + h1_t4 + h2_t4 + h3_t4 + h4_t4 + h5_t4 + h6_t4 + h7_t4 + h8_t4 + h9_t4
                        
                        msg_t4 = head_t4 + pl_t4 + eop
                        print(f"\nMensagem tipo 4: {msg_t4}\n")

                        com1.sendData(np.asarray(msg_t4))
                        time.sleep(0.1)

                        arquivo('arquivo1.txt', head_t4, pl_t4, eop, 'envio')

                        print(f"\nMensagem tipo 4 enviada, pacote de número {head_receb[4]}\n")

                        cont += 1
                        break

                    elif (head_receb[4] < 0 or head_receb[4] > head_receb[3]):
                        arquivo('arquivo2.txt', head_receb, pl_receb, eop_receb, 'receb')
                        
                        print(f"\nMensagem tipo 3 recebida com erro 1\n")
                        print("-------------------------")
                        
                        h0_t6 = (6).to_bytes(1, byteorder="big") 
                        h1_t6 = b'\x00'
                        h2_t6 = b'\xbb'
                        h3_t6 = (1).to_bytes(1, byteorder="big")
                        h4_t6 = b'\x00'
                        h5_t6 = (1).to_bytes(1, byteorder="big")
                        h6_t6 = (lista_packages[-1] + 1).to_bytes(1, byteorder="big")
                        h7_t6 = (lista_packages[-1]).to_bytes(1, byteorder="big")
                        h8_t6 = b'\x00'
                        h9_t6 = b'\x00'

                        pl_t6 = b'\xbb'

                        head_t6 = h0_t6 + h1_t6 + h2_t6 + h3_t6 + h4_t6 + h5_t6 + h6_t6 + h7_t6 + h8_t6 + h9_t6

                        com1.sendData(np.asarray(head_t6 + pl_t6 + eop))
                        time.sleep(0.1)

                        arquivo('arquivo2.txt', head_t6, pl_t6, eop, 'envio')

                        print(f"\nMensagem tipo 6 enviada\n")
                        break

                    else:
                        if head_receb[4] in lista_packages:
                            arquivo('arquivo2.txt', head_receb, pl_receb, eop_receb, 'receb')

                            print(f"\nMensagem tipo 3 recebida com erro 2\n")

                            h0_t6 = (6).to_bytes(1, byteorder="big")
                            h1_t6 = b'\x00'
                            h2_t6 = b'\xbb'
                            h3_t6 = (1).to_bytes(1, byteorder="big")
                            h4_t6 = b'\x00'
                            h5_t6 = (1).to_bytes(1, byteorder="big")
                            h6_t6 = (lista_packages[-1] + 1).to_bytes(1, byteorder="big")
                            h7_t6 = (lista_packages[-1]).to_bytes(1, byteorder="big")
                            h8_t6 = b'\x00'
                            h9_t6 = b'\x00'

                            pl_t6 = b'\xcc'

                            head_t6 = h0_t6 + h1_t6 + h2_t6 + h3_t6 + h4_t6 + h5_t6 + h6_t6 + h7_t6 + h8_t6 + h9_t6

                            com1.sendData(np.asarray(head_t6 + pl_t6 + eop))
                            time.sleep(0.1)

                            arquivo('arquivo2.txt', head_t6, pl_t6, eop, 'envio')

                            print(f"\nMensagem tipo 6 enviada\n")
                            break
                            
                        elif head_receb[4] != lista_packages[-1] + 1:
                            arquivo('arquivo2.txt', head_receb, pl_receb, eop_receb, 'receb')

                            print(f"\nMensagem tipo 3 recebida com erro 3\n")

                            h0_t6 = (6).to_bytes(1, byteorder="big")
                            h1_t6 = b'\x00'
                            h2_t6 = b'\xaa'
                            h3_t6 = (1).to_bytes(1, byteorder="big")
                            h4_t6 = b'\x00'
                            h5_t6 = (1).to_bytes(1, byteorder="big")
                            h6_t6 = (lista_packages[-1] + 1).to_bytes(1, byteorder="big")
                            h7_t6 = (lista_packages[-1]).to_bytes(1, byteorder="big")
                            h8_t6 = b'\x00'
                            h9_t6 = b'\x00'

                            pl_t6 = b'\xcc'

                            head_t6 = h0_t6 + h1_t6 + h2_t6 + h3_t6 + h4_t6 + h5_t6 + h6_t6 + h7_t6 + h8_t6 + h9_t6

                            com1.sendData(np.asarray(head_t6 + pl_t6 + eop))
                            time.sleep(0.1)

                            arquivo('arquivo2.txt', head_t6, pl_t6, eop, 'envio')

                            print(f"\nMensagem tipo 6 enviada\n")
                            break
                else:
                    time.sleep(1)

                    print("\nMensagem recebida não foi do tipo 3\n")
                    print("-------------------------")

                    if timer_2 <= 20:
                        if timer_1 > 2:
                            h0_t4 = (4).to_bytes(1, byteorder="big")
                            h1_t4 = b'\x00'
                            h2_t4 = b'\xaa'
                            h3_t4 = (1).to_bytes(1, byteorder="big")
                            h4_t4 = b'\x00'
                            h5_t4 = (1).to_bytes(1, byteorder="big")
                            h6_t4 = b'\x00'
                            h7_t4 = (head_receb[4]).to_bytes(1, byteorder="big")
                            h8_t4 = b'\x00'
                            h9_t4 = b'\x00'

                            pl_t4 = b'\xaa'

                            head_t4 = h0_t4 + h1_t4 + h2_t4 + h3_t4 + h4_t4 + h5_t4 + h6_t4 + h7_t4 + h8_t4 + h9_t4

                            com1.sendData(np.asarray(head_t4 + pl_t4 + eop))

                            arquivo('arquivo4.txt', head_t4, pl_t4, eop, 'envio')

                            timer_1 = time.time()
                    else:
                        ocioso = True

                        head_t5 = (5).to_bytes(1, byteorder="big") + b'\x00'*4 + (1).to_bytes(1, byteorder="big") + b'\x00'*4
                        
                        pl_5 = b'\x00'

                        com1.sendData(np.asarray(head_t5 + pl_5 + eop))

                        arquivo('arquivo3.txt', head_t5, pl_5, eop, 'envio')

                        print("\nMensagem tipo 5 enviada\n")
                        print("Time Out\n")

                        break
        
        if cont == numPckg:
            print("\nTodas as mensagens recebidas com sucesso\n")
            print("-------------------------")

            head_termino = b'x00' + numPckg + (1).to_bytes(1, byteorder="big") + b'\xaa'*9
            com1.sendData(head_termino + b'\xdd' + eop)
            time.sleep(0.1)

            arquivo('arquivo1.txt', head_termino, b'\xdd', eop, 'envio')

            with open('output.png', 'wb') as image_file:
                image_file.write(recebido)

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
