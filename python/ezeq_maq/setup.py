# especificacao da comunicacao serial
porta = '/dev/ttyUSB0'
end_modbus = 17
baud = 4800
timeout = 0.15

# numeros de calculo para a placa de controle (seus limitadores)
soma = 16843009 # numero para corrigir a contagem de ticks
inf = 4e-10 # numero infinitesimal, para evitar a divisao por zero
max_num = 2130640638 # maior numero possivel para contagem da placa
negativo =  2147483648 #  bit alto da palavra de 32bits - indica sentido reverso
ms_tick = 4.0	# quantos interrupcoes acontecem na placa por ms

# tempo de passo minimo milisegundos (especificacao do motor de passo)
t_passo_min = 7.5

# passos por revolucao (especificacao do motor de passo)
passos_rev = 200.0

# milimetros por revolucao (especif. eixo roscado)
mm_rev = 15.0

# calculo da velocidade maxima da maquina
vel_max = 1000 * mm_rev / (passos_rev * t_passo_min) #mm por s