# -*- coding: cp1252 -*-
import struct
import math
from setup import *

#converte uma palavra de 32 bits em fuas de 16
def conv_32_16(val):
	a = struct.unpack('>HH', struct.pack('>L',val)) #eh uma tupla
	return [a[0], a[1]]

#converte duas palavras de 16bits em uma de 32
def conv_16_32(val):
	a = struct.unpack('>L', struct.pack('>HH',val[0],val[1])) #eh uma tupla
	return a[0]

# testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
def testBit(int_type, offset):
	mask = 1 << offset
	return(int_type & mask)

# setBit() returns an integer with the bit at 'offset' set to
def setBit(int_type, offset):
	mask = 1 << offset
	return(int_type | mask)

# clearBit() returns an integer with the bit at 'offset' cleared.

def clearBit(int_type, offset):
	mask = ~(1 << offset)
	return(int_type & mask)

# toggleBit() returns an integer with the bit at 'offset' inverted, 0 > 1 and 1 > 0.
def toggleBit(int_type, offset):
	mask = 1 << offset
	return(int_type ^ mask)
	
def maq_le(mens):
	a = conv_16_32(mens[0:2])
	tempo_rest = (a - soma)/(1000 * ms_tick)
	return tempo_rest

def maq_usina(x=0.0,y=0.0,z=0.0,vel=1.0):
	dist = math.sqrt(x**2 + y**2 + z**2) # distancia a ser percorrida
	
	tempo = dist/vel_max
	if dist == 0: # se a distancia for zero
		tempo = 1 # o tempo nao importa
	elif vel<=vel_max: 
		tempo = dist/vel # tempo total de movimento
	
	# velocidades de cada eixo
	vel_x = abs(x / tempo)
	vel_y = abs(y / tempo)
	vel_z = abs(z / tempo)
	
	# cada eixo eh convertido em quantidade de ticks para contagem da placa
	tick_x = abs(int(round(ms_tick *1000 * mm_rev / (passos_rev * vel_x + inf))))
	tick_y = abs(int(round(ms_tick *1000 * mm_rev / (passos_rev * vel_y + inf))))
	tick_z = abs(int(round(ms_tick *1000 * mm_rev / (passos_rev * vel_z + inf))))

	
	#verifica se as quantidades sao aceitaveis e corrige a contagem da placa
	if tick_x < max_num: tick_x = tick_x + soma
	else: tick_x = max_num + soma

	if tick_y < max_num: tick_y = tick_y + soma
	else: tick_y = max_num + soma

	if tick_z < max_num: tick_z = tick_z +soma
	else: tick_z = max_num + soma
	
	# sentidos dos eixos
	if x < 0: tick_x = tick_x + negativo
	if y < 0: tick_y = tick_y + negativo
	if z < 0: tick_z = tick_z + negativo
	
	# prepara a mensagem para envio, transformando em uma lista
	tempo = maq_tempo(tempo) # tempo
	eixo_x = conv_32_16(tick_x) #eixo x
	eixo_y = conv_32_16(tick_y)#eixo y
	eixo_z = conv_32_16(tick_z) #eixo z
	
	mens = tempo + eixo_x + eixo_y + eixo_z
	
	return mens

def maq_tempo(tempo):
	#o tempo em segundos eh convertido em quant de ticks p/ contagem da placa
	tick_t = int(round(tempo * 1000 * ms_tick))
	
	#verifica se as quantidades sao aceitaveis e corrige a contagem da placa
	if tick_t < max_num: tick_t = tick_t + soma
	else: tick_t = max_num + soma
	
	# prepara a mensagem para envio, transformando em uma lista
	t = conv_32_16(tick_t) # tempo
	
	return t

if __name__ == "__main__":
	print 'Modulo de funcoes de conversao de tipos de dados'
	mens = maq_usina( 0, 0, 0, 0)
	print mens[2:]
	mens = maq_usina( 10, 20, 30, 2)
	print mens
	print maq_le(mens)