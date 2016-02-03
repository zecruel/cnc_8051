# -*- coding: cp1252 -*-
from Tkinter import *
import tkFileDialog
import tkMessageBox
from math import *		#importa as funcoes matematicas
import copy
import re
import time
import threading
import minimalmodbus
import struct

vel_max = 2000
vel_min = 10.0
contador = 0
exec_pronto = 0
maq_stat = None
tempo_rest = 0

instr = minimalmodbus.Instrument('/dev/ttyUSB0', 17) # port name, slave address (in decimal)
instr.serial.baudrate = 4800
instr.debug = False
instr.serial.timeout = 0.15

def conv_32_16(val):
	a = struct.unpack('>HH', struct.pack('>L',val)) #eh uma tupla
	return [a[0], a[1]]
	
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

def background(parar,trava):
	global instr
	global maq_stat
	global tempo_rest
	soma = 16843009
	inf = 4e-10
	max_num = 2130640638

	ms_tick = 4.0	#quantos interrupcoes acontecem na placa por ms
	t_passo_min = 7.5 #tempo de passo minimo milisegundos
	passos_rev = 200.0 #passos por revolucao
	mm_rev = 15.0 #milimetros por revolucao
	
	while not parar.is_set():
		trava. acquire()
		try:
			maq_stat = instr.read_register(0) #status da maquina
		except:
			maq_stat = None
			#print 'erro'
		else:
			if testBit(maq_stat ,8):
				a = conv_16_32(instr.read_registers(1,2) )
				if a != 0:
					tempo_rest = (a - soma)/(1000 * ms_tick)
		trava.release()
		time.sleep(0.15)
		
def executa_geral(parar,trava, principal, codigo, tela):
	global instr
	global maq_stat
	global tempo_rest
	
	soma = 16843009
	ms_tick = 4.0	#quantos interrupcoes acontecem na placa por ms
	
	trava. acquire()
	while principal.executa and (principal.iter < principal.visual_gcode.size()) and principal.continua and (maq_stat!=None):
		
		codigo.linha = principal.visual_gcode.get(principal.iter) 	#pega a linha atual
		codigo.interpreta()						#e interpreta
		
		for i in range(len(codigo.lista)):			#cada objeto da lista interpretada eh adicionado ao desenho
			pt1 = codigo.lista[i].pt1
			pt2 = codigo.lista[i].pt2
			if ((pt2.x-pt1.x)!=0) or ((pt2.y-pt1.y)!=0) or ((pt2.z-pt1.z)!=0):
				dados = converte_maq(pt2.x-pt1.x,pt2.y-pt1.y,pt2.z-pt1.z,codigo.lista[i].vel)
				manda_exec(dados.t, dados.x, dados.y, dados.z)
				while True:
					try:
						#time.sleep(0.05)
						maq_stat, t_h, t_l = instr.read_registers(0,3) #status da maquina
					except:
						maq_stat = None
						print 'erro Leitura'
						#break
					else:
						#time.sleep(0.05)
						if testBit(maq_stat ,11): 
							#continue
							a = conv_16_32([t_h,t_l])
							if a != 0:
								tempo_rest = (a - soma)/(1000 * ms_tick)
						else:
							break				
				cor = rgb(codigo.lista[i].vel,vel_min, vel_max)
				tela.lista_orig.append(linha(pt1, pt2, cor))
				tela.transforma()
				#time.sleep(0.1)
				#principal.redesenha()
		
		principal.iter = principal.iter + 1 #passa para a proxima
	else: 
		principal.simulacao = 0
		principal.executa = 0
	trava.release()
		
		
def manda_exec(tick_t, tick_x, tick_y, tick_z):
	global instr
	global maq_stat
	#trava.acquire()
	try:
		tempo = conv_32_16(tick_t) # tempo
		eixo_x = conv_32_16(tick_x) #eixo x
		eixo_y = conv_32_16(tick_y)#eixo y
		eixo_z = conv_32_16(tick_z) #eixo z
		comando = [1]
		mens = comando + tempo + eixo_x + eixo_y + eixo_z
		#print mens
		
		instr.write_registers(0,mens) #executa
	except:
		print 'Erro envio comando'
	else:
		pass
		#tempo = 20000 + soma
		#time.sleep(0.15)
	#atualiza o status da maquina
	try:
		a= instr.read_register(0) #status da maquina
	except:
		maq_stat = None
		print 'Deu errado!'
	else:
		maq_stat = a
		#time.sleep(0.05)
	#trava.release()


def rgb(mag, cmin, cmax):
	"""
	These functions, when given a magnitude mag between cmin and cmax, return
	a colour tuple (red, green, blue). Light blue is cold (low magnitude)
	and yellow is hot (high magnitude). Return a tuple of strings to be used in Tk plots.
	"""
	try:
		# normalize to [0,1]
		x = float(mag-cmin)/float(cmax-cmin)
	except:
		# cmax = cmin
		x = 0.5
	blue = min((max((4*(0.75-x), 0.)), 1.))
	red  = min((max((4*(x-0.25), 0.)), 1.))
	green= min((max((4*fabs(x-0.5)-1., 0.)), 1.))
	return "#%02x%02x%02x" % (red*255, green*255, blue*255)

class ponto:
	def __init__(self, x = 0.0, y = 0.0, z = 0.0):
		self.x = x
		self.y = y
		self.z = z

class linha:
	def __init__(self, pt1 = ponto(), pt2 = ponto(), cor = 'yellow'):
		self.pt1 = copy.deepcopy(pt1)
		self.pt2 = copy.deepcopy(pt2)
		self.cor = cor
		
class l_usin:
	def __init__(self, pt1 = ponto(), pt2 = ponto(), vel = 0.0):
		self.pt1 = copy.deepcopy(pt1)
		self.pt2 = copy.deepcopy(pt2)
		self.vel = vel
		
class d_maq:
	def __init__(self, t, x, y, z):
		self.x = x
		self.y = y
		self.z = z
		self.t = t

def converte_maq(x=0.0,y=0.0,z=0.0,vel=1.0):
	soma = 16843009
	inf = 4e-10
	max_num = 2130640638
	negativo =  2147483648

	ms_tick = 4.0	#quantos interrupcoes acontecem na placa por ms
	t_passo_min = 7.5 #tempo de passo minimo milisegundos
	passos_rev = 200.0 #passos por revolucao
	mm_rev = 15.0 #milimetros por revolucao

	vel_max = 1000 * mm_rev / (passos_rev * t_passo_min) #mm por s
	#print 'velocidade maxima=' , vel_max, 'mm/s'
	#print 'resolucao da maquina=', mm_rev/passos_rev, 'mm'

	dist = sqrt(x**2 + y**2 + z**2)
	
	tempo = dist/vel_max
	if vel<=vel_max: tempo = dist/vel

	tick_t = int(round(tempo * 1000 * ms_tick))
	
	#print 'tempo=', tempo, 's, vel=', vel, 'mm/s'
	
	vel_x = abs(x / tempo)
	vel_y = abs(y / tempo)
	vel_z = abs(z / tempo)

	tick_x = abs(int(round(ms_tick *1000 * mm_rev / (passos_rev * vel_x + inf))))
	tick_y = abs(int(round(ms_tick *1000 * mm_rev / (passos_rev * vel_y + inf))))
	tick_z = abs(int(round(ms_tick *1000 * mm_rev / (passos_rev * vel_z + inf))))

	#print tick_t /tick_x
	#print tick_t /tick_y
	#print tick_t /tick_z

	if tick_t < max_num:
		tick_t = tick_t +soma
	else:
		tick_t = max_num +soma

	if tick_x < max_num:
		tick_x = tick_x +soma
	else:
		tick_x = max_num +soma

	if tick_y < max_num:
		tick_y = tick_y +soma
	else:
		tick_y = max_num +soma

	if tick_z < max_num:
		tick_z = tick_z +soma
	else:
		tick_z = max_num +soma
	
	if x < 0:
		tick_x = tick_x + negativo
		
	if y < 0:
		tick_y = tick_y + negativo
	
	if z < 0:
		tick_z = tick_z + negativo
	
	return d_maq(tick_t, tick_x, tick_y, tick_z)
		
class grafico:
	lista_orig = []
	lista_trans = []
	olho = ponto(0.0,0.0,300.0)
	rotacao = ponto()
	
	def transforma(self):
		
		a = pi / 180.0 * self.rotacao.z  #degrees to rotate about z-axis
		b = pi / 180.0 * self.rotacao.y  #degrees to rotate about y-axis
		c = pi / 180.0 * self.rotacao.x  #degrees to rotate about x-axis

		xx = cos(a)*cos(b)                      #calc xx constant
		xy = -sin(a)*cos(b)                     #calc xy constant
		xz = -sin(b)                           #calc xz constant 
	
		yx = sin(a)*cos(c) - cos(a)*sin(b)*sin(c) #calc yx constant
		yy = cos(a)*cos(c) + sin(a)*sin(b)*sin(c) #calc yy constant
		yz = -cos(b)*sin(c)                     #calc yz constant 
	
		zx = sin(a)*sin(c) + cos(a)*sin(b)*cos(c) #calc zx constant
		zy = cos(a)*sin(c) - sin(a)*sin(b)*cos(c) #calc zy constant
		zz = cos(b)*cos(c)                      #calc zz constant
		
		self.lista_trans = []
		
		for i in range(len(self.lista_orig)):
			if self.lista_orig[i].__class__.__name__=='linha':
				
				pt1 = self.lista_orig[i].pt1
				pt2 = self.lista_orig[i].pt2
				cor = self.lista_orig[i].cor
				
				a1 = pt1.x * xx + pt1.y * xy + pt1.z * xz - self.olho.x
				b1 = pt1.x * yx + pt1.y * yy + pt1.z * yz - self.olho.y
				c1 = pt1.x * zx + pt1.y * zy + pt1.z * zz - self.olho.z
				
				a2 = pt2.x * xx + pt2.y * xy + pt2.z * xz - self.olho.x
				b2 = pt2.x * yx + pt2.y * yy + pt2.z * yz - self.olho.y
				c2 = pt2.x * zx + pt2.y * zy + pt2.z * zz - self.olho.z
				
				self.lista_trans.append(linha(ponto(a1,b1,c1),ponto(a2,b2,c2), cor))
class Gcode:
	pre_x = 0.0
	pre_y = 0.0
	pre_z = 0.0
	x = pre_x
	y = pre_y
	z = pre_z
	s = 0
	l = 1
	estilo = 200
	movimento = 0
	plano = 'xy'
	unidade = 'mm'
	modo = 'absoluto'
	
	x_max = None
	y_max = None
	z_max = None
	f_max = None
	
	x_min = None
	y_min = None
	z_min = None
	f_min = None

	lista = []
	velocidade = vel_max

	def limpa(self):
		self.pre_x = 0.0
		self.pre_y = 0.0
		self.pre_z = 0.0
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0
		self.s = 0
		self.l = 1
		self.estilo = 200
		self.movimento = 0
		self.plano = 'xy'
		self.unidade = 'mm'
		self.modo = 'absoluto'
		
		self.x_max = None
		self.y_max = None
		self.z_max = None
		self.f_max = None
		
		self.x_min = None
		self.y_min = None
		self.z_min = None
		self.f_min = None
		
		self.lista = []
		self.velocidade = vel_max
		
	
	#--------- Rotina de interpretação do arquivo Gcode -------------------------
	def interpreta(self):
		comando = 200 #um inteiro que nao representa nenhum comando
		inf = 4e-10	#um nimero infinitesimal, para evitar a divisao por zero
		self.lista = []
		flag = 0
		raio = 0
		self.pre_x = self.x
		self.pre_y = self.y
		self.pre_z = self.z
		
		i=0
		j=0
		k=0
		r=0
		
		self.linha = re.sub('\(([^\)]+)\)', '', self.linha) #retira os comentarios entre parenteses
		self.linha = re.sub(';.+', '', self.linha) #retira os comentarios depois de ponto e virgula
		
		chaves = re.finditer("([a-zA-Z]{1})(\-?\.?\d+\.?\d*)", self.linha)
		for chave in chaves:
			
			#-----------procura codigos chave padrao Gcode-------------
			#print chave.group(1,2)
			
			#--------comandos gcode principais ----------------
			if (chave.group(1) == 'g') or (chave.group(1) == 'G'):
				comando = float(chave.group(2))
				self.movimento = 0
				if (comando >= 0 and comando < 4): self.estilo = comando
				elif comando == 17: self.plano = 'xy'
				elif comando == 18: self.plano = 'xz'
				elif comando == 19: self.plano = 'yz'
				elif comando == 20: self.unidade = 'pol'
				elif comando == 21: self.unidade = 'mm'
				elif comando == 90: self.modo = 'absoluto'
				elif comando == 91.0: self.modo = 'relativo'
			
			#-------- coordenadas---------------------
			#XXXXXXXXXX
			elif (chave.group(1) == 'x') or (chave.group(1) == 'X'):
				self.x = float(chave.group(2))
				if self.unidade == 'pol': self.x = self.x * 25.4
				if self.modo == 'relativo': self.x = self.x + self.pre_x
				flag = 1
				if self.x_max:
					self.x_max = max(self.x_max, self.x)
					self.x_min = min(self.x_min, self.x)
				else:
					self.x_max = self.x
					self.x_min = self.x
			#YYYYYYYYYYY
			elif (chave.group(1) == 'y') or (chave.group(1) == 'Y'):
				self.y = float(chave.group(2))
				if self.unidade == 'pol': self.y = self.y * 25.4
				if self.modo == 'relativo': self.y = self.y + self.pre_y
				flag = 1
				if self.y_max:
					self.y_max = max(self.y_max, self.y)
					self.y_min = min(self.y_min, self.y)
				else:
					self.y_max = self.y
					self.y_min = self.y
			#ZZZZZZZZZZZZZ
			elif (chave.group(1) == 'z') or (chave.group(1) == 'Z'):
				self.z = float(chave.group(2))
				if self.unidade == 'pol': self.z = self.z * 25.4
				if self.modo == 'relativo': self.z = self.z + self.pre_z
				flag = 1
				if self.z_max:
					self.z_max = max(self.z_max, self.z)
					self.z_min = min(self.z_min, self.z)
				else:
					self.z_max = self.z
					self.z_min = self.z
			
			# ---------- parametros de movimento circular
			#---------offsets para o centro ----------------
			#IIIIIIIIIIIIIII
			elif (chave.group(1) == 'i') or (chave.group(1) == 'I'):
				i = float(chave.group(2))
				if self.unidade == 'pol': i = i * 25.4
			#JJJJJJJJJJJJJJJ
			elif (chave.group(1) == 'j') or (chave.group(1) == 'J'):
				j = float(chave.group(2))
				if self.unidade == 'pol': j = j * 25.4
			#KKKKKKKKKKKK
			elif (chave.group(1) == 'k') or (chave.group(1) == 'K'):
				k = float(chave.group(2))
				if self.unidade == 'pol': k = k * 25.4
			#raio do arco
			#RRRRRRRRRRR
			elif (chave.group(1) == 'r') or (chave.group(1) == 'R'):
				r = float(chave.group(2))
				if self.unidade == 'pol': r = r * 25.4
				raio = 1
				
			#---------- velocidade de usinagem
			elif (chave.group(1) == 'f') or (chave.group(1) == 'F'):
				#a velocidade é dada em unid/min
				self.velocidade = float(chave.group(2))/60 #transforma em unid/s
				if self.unidade == 'pol': self.velocidade = self.velocidade * 25.4 #transforma em mm/s
				if self.f_max:
					self.f_max = max(self.f_max, self.velocidade)
					self.f_min = min(self.f_min, self.velocidade)
				else:
					self.f_max = self.velocidade
					self.f_min = self.velocidade
			
			#--------parametros gcode----------------
			elif (chave.group(1) == 's') or (chave.group(1) == 'S'):
				s = float(chave.group(2))
			
			#--------comandos gcode secundarios ----------------
			elif (chave.group(1) == 'm') or (chave.group(1) == 'M'):
				if int(chave.group(2))==0:
					self.movimento = 0
					#print 'parada'
				
		#------Movimentos lineares ---------------
		if(self.estilo == 1 or self.estilo == 0):
			self.movimento = 1
			vel = vel_max
			if(flag & self.movimento):
				if (self.estilo == 1): vel= self.velocidade
				self.lista.append(l_usin(ponto(self.pre_x,self.pre_y,self.pre_z),ponto(self.x,self.y,self.z), vel))
				
		#-------- Movimentos circulares -------------
		elif(self.estilo == 2 or self.estilo == 3) and flag:
			
			#-------------------------------------------------------------------------------------------
			#---- transforma o arco em segmentos de reta, criando um polígono regular inscrito
			#----------------------------------------------------------------------------------------------
			n = 32 #numero de vertices do polígono regular que aproxima o circulo ->bom numero 

			sentido = 1				#o sentido padrão do algoritmo eh contra relógio (G03)
			if (self.estilo == 2): sentido = -1 # para sentido do relógio (G02) sentido eh negativo

			pre_x = self.pre_x
			pre_y = self.pre_y
			pre_z = self.pre_z
			
			atual_x = self.x
			atual_y = self.y
			atual_z = self.z
			
			centro_x = pre_x + i		#encontra o centro via offsets
			centro_y = pre_y + j
			angulo = 0.0
			
			#---------encontra o centro via raio do arco---------------
			if (raio):			#pega o valor via parametro passado no codigo

				if ((pre_x - atual_x) == 0) and ((pre_y - atual_y) != 0):
					centro_y = pre_y + (atual_y - pre_y)/2
					centro_x = atual_x
					angulo = pi
					ang_ini = atan2((pre_y - centro_y),(pre_x - centro_x))
					if ((ang_ini < 0) & (sentido>inf)): ang_ini = (2*pi) + ang_ini
				
				elif ((pre_y - atual_y) == 0) and ((pre_x - atual_x) != 0):
					centro_x = pre_x + (atual_x - pre_x)/2
					centro_y = atual_y
					angulo = pi
					ang_ini = atan2((pre_y - centro_y),(pre_x - centro_x))
					if ((ang_ini < 0) & (sentido>inf)): ang_ini = (2*pi) + ang_ini
				
				else:				
					#solução do sistema de equações quadraticas para encontrar o centro do arco
					C = 2*atual_x - 2*pre_x
					D = 2*atual_y - 2*pre_y
					E = (pre_y)**2+(pre_x)**2-(atual_x)**2-(atual_y)**2
					
					alfa = (D/C)**2 + 1
					beta = 2*pre_x*D/C+2*D*E/(C**2)-2*pre_y
					gama = pre_x**2+2*pre_x*E/C+(E/C)**2+pre_y**2-r**2

					delta = sqrt(beta**2-(4*alfa*gama))
					
					ang=[]
					ang_i=[]
					cx=[]
					cy=[]
					#são encontradas duas soluções
					# usa um laço para processar as duas soluções
					for iter in [-1.0, 1.0]: 
						c_y = (-beta + iter*delta)/(2*alfa)
						c_x = (-E-D*c_y)/C
						cx.append(c_x)
						cy.append(c_y)
						#---------angulo inicial obtido das coordenadas iniciais
						ang_ini = atan2((pre_y - c_y),(pre_x - c_x))
						if ((ang_ini < 0) & (sentido>inf)): ang_ini = (2*pi) + ang_ini
						ang_i.append(ang_ini)
				
						#--------angulo final obtido das coordenadas
						ang_final = atan2((atual_y - c_y),(atual_x -c_x))
						if ((ang_final < 0) & (sentido>0)): ang_final = (2*pi) + ang_final
				
						angulo = (ang_final-ang_ini) * sentido #angulo do arco
						if angulo <= 0: angulo = angulo + 2*pi
						ang.append(angulo)
					
					# escolhe uma solução, conforme a polaridade do parametro r
					if r>0: 
						angulo = min(ang) # se r for positivo, então fica com o menor arco
						
					else:
						angulo = max(ang)  # se r for negativo, então fica com o maior arco
					
					# retorna as coordenadas do centro e o angulo inicial,
					# correnspondentes ao angulo escolhido
					centro_x = cx[ang.index(angulo)]
					centro_y = cy[ang.index(angulo)]
					ang_ini = ang_i[ang.index(angulo)]
					
			else:
				r=sqrt(i**2+j**2) #calcula a partir os offsets, ou
				
				#---------encontra o centro via offsets---------------
				#---------angulo inicial obtido das coordenadas iniciais
				ang_ini = atan(j/(i - inf))
				if ((pre_x - centro_x)<-inf)| ((round(180/pi*ang_ini)==90)&((pre_y - centro_y)<0)): ang_ini = ang_ini + pi
				if ((ang_ini < -inf) & (sentido>0)): ang_ini = (2*pi) + ang_ini
			
				#--------angulo final obtido das coordenadas
				ang_final = atan((atual_y - centro_y)/(atual_x -centro_x + inf))
				if ((atual_x - centro_x)<-inf) | ((round(180/pi*ang_final)==90)&((atual_y - centro_y)<0)):  ang_final = ang_final + pi
				if ((ang_final < -inf) & (sentido>0)): ang_final = (2*pi) + ang_final
			
				angulo = (ang_final-ang_ini) * sentido #angulo do arco
				if angulo <= 0: angulo = angulo + 2*pi
			
			passo = angulo*n/(2*pi)	#descobre quantos passos para o laço a seguir

			passos = abs(int(passo)) #numero de vertices do arco

			passo_z = (atual_z - pre_z)/abs(passo) #se houver cood. Z, faz interpolação helicoidal
			
			#print ang_ini
			#já começa do segundo vértice
			for i in range(1,passos):

				px = centro_x + r * cos(2 * pi * i * sentido/ n + ang_ini)
				py = centro_y + r * sin(2 * pi * i * sentido/ n + ang_ini)
				
				pz = pre_z + passo_z
				
				self.lista.append(l_usin(ponto(pre_x,pre_y,pre_z),ponto(px,py,pz), self.velocidade))
				pre_x=px
				pre_y=py
				pre_z=pz
			# o ultimo vertice do arco eh o ponto final, nao calculado no laço
			self.lista.append(l_usin(ponto(pre_x,pre_y,pre_z),ponto(atual_x,atual_y,atual_z), self.velocidade))
	
tela = grafico()
codigo =Gcode()

#-------------------------------------------------------------------------------------------------------------------------------------------------------
#--------- Constroi a GUI  --------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------------
class Janela:
	#------------- Tamanho da Área de desenho---------------
	altura = 400
	largura = 400
	#------------------------------------------------------------
	iter = 0 #iterador
	iter_antigo = -1 #iterador
	iter2 = 0
	iter2_antigo = -1
	continua = 0
	executa = 0
	simulacao = 0

	
	
	# -----------------------------------------
	#Comando de abrir arquivo
	#------------------------------------------
	def abrir_arq(self):
		global vel_max
		global vel_min
		arquivo = tkFileDialog.askopenfilename(title='Abrir')
		if arquivo != "":
			self.limpa()
			self.visual_gcode.delete(0,END)
			with open(arquivo) as f:
				codigo.limpa()
				for line in f:
					line = line.replace('\r', ' ') #retira os separadores de linha e os substitui por espaços
					line = line.replace('\n', ' ')
					self.visual_gcode.insert(END,line)
					#---------interpreta previamente
					#--------- para determinar os limites e ajuste da tela
					codigo.linha = line
					codigo.interpreta()
					
				a = (2*(max(codigo.x_max, codigo.y_max, codigo.z_max) - min(codigo.x_min, codigo.y_min, codigo.z_min)))
				self.trans_z.delete(0,"end")
				self.trans_z.insert(0,a-1)
				self.trans_z.invoke('buttonup')
			
				b = ((codigo.x_max - codigo.x_min)/2) + codigo.x_min
				self.trans_x.delete(0,"end")
				self.trans_x.insert(0,-b-1)
				self.trans_x.invoke('buttonup')
			
				c = ((codigo.y_max - codigo.y_min)/2) + codigo.y_min
				self.trans_y.delete(0,"end")
				self.trans_y.insert(0,c-1)
				self.trans_y.invoke('buttonup')
				
				#print 'x min=', codigo.x_min, 'x max=', codigo.x_max
				#print 'y min=', codigo.y_min, 'y max=', codigo.y_max
				#print 'z min=', codigo.z_min, 'z max=', codigo.z_max
				#print 'f min=', codigo.f_min, 'f max=', codigo.f_max
				if codigo.f_max:
					vel_max = 2 * codigo.f_max
					vel_min = codigo.f_min
				else:
					vel_max = vel_min = 1.0
				
				codigo.limpa()
	
	#------------------------------------------
	#Comando de fechar arquivo
	#--------------------------------------------
	def fechar_arq(self):
		if tkMessageBox.askokcancel("Fechar", "Deseja fechar o arquivo?"):
			self.visual_gcode.delete(0,END)
	
	#------------------------------------------
	#Informações do programa
	#------------------------------------------
	def sobre(self):
		label = tkMessageBox.showinfo("Sobre o programa", "Interpretador, simulador de Gcode \n\n Copyright \n BeerWare")
	
	
	#------------------------------------------
	#rotina temporal
	#--------------------------------------------
	def temporal(self):
		global contador
		global exec_pronto
		global maq_stat
		global tempo_rest
		
		#------------------------- rotina de simulacao----------------------------------------------------------------------------------------
		if self.simulacao and (self.iter < self.visual_gcode.size()) and self.continua:
			#print int(self.simulacao)
			self.visual_gcode.selection_clear(0,END)  		#limpa a linha de codigo selecionada anterior
			self.visual_gcode.selection_set(self.iter)  		#e mostra a linha atual
			if (self.iter%23 == 0): 					#se a linha selecionada esta proxima do final da exibicao
				self.visual_gcode.yview(self.iter)		#rearranja a exibição da lista (rola automaticamente)
			
			codigo.linha = self.visual_gcode.get(self.iter) 	#pega a linha atual
			codigo.interpreta()						#e interpreta
			
			for i in range(len(codigo.lista)):			#cada objeto da lista interpretada eh adicionado ao desenho
				pt1 = codigo.lista[i].pt1
				pt2 = codigo.lista[i].pt2	
				cor = rgb(codigo.lista[i].vel,vel_min, vel_max) 	#faz a escala de cores de acordo com a velocidade de avanco
				tela.lista_orig.append(linha(pt1, pt2, cor))

			tela.transforma()	#reexibe o desenho completo
			self.redesenha()
			
			self.iter = self.iter + 1 #passa para a proxima
			
		#--------------------------------rotina de execucao---------------------------------------------------------------------------------
		elif self.executa and (self.iter < self.visual_gcode.size()) and self.continua and (maq_stat!=None):
			
			if self.iter != self.iter_antigo: 		#verifica se o iterador mudou
				self.iter_antigo = self.iter
				self.visual_gcode.selection_clear(0,END)  		#limpa a linha de codigo selecionada anterior
				self.visual_gcode.selection_set(self.iter)  		#e mostra a linha atual
				if (self.iter%23 == 0): 					#se a linha selecionada esta proxima do final da exibicao
					self.visual_gcode.yview(self.iter)		#rearranja a exibição da lista (rola automaticamente)
				self.redesenha()
				
		self.e.delete(0, END) #teste
		self.e2.delete(0, END) #teste
		
		if maq_stat != None:
		#print maq_stat
			if testBit(maq_stat ,8):
				a= 'maquina executando'
				#print 'tempo restante =', tempo_rest
			elif testBit(maq_stat ,9):
				a= 'emergencia maquina'
			elif testBit(maq_stat ,10):
				a= 'maquina parada'
			else:
				a= maq_stat
		else:
			a= 'maquina desligada'
		
		self.e.insert(0, a) #teste
		self.e2.insert(0, tempo_rest) #teste
		
		self.desenho.after(100, self.temporal) # reagenda
	
	
	#------------------------------------------
	#Comando de simular GCODE
	#--------------------------------------------
	def simula(self):
		self.limpa()
		self.continua = 1
		self.simulacao = 1
		
	def pausa(self):
		self.continua = 0
		#self.trava.acquire() #teste
			
	def exc(self):
		self.limpa()
		self.executa=1
		self.continua = 1
		exec_back = threading.Thread(target=executa_geral, args = (parar,trava, self, codigo, tela))
		exec_back.start()
		
	def limpa(self):
		self.desenho.delete("all")
		self.continua = 0
		self.executa=0 
		self.iter = 0
		self.iter_antigo = -1
		codigo.limpa()
		tela.lista_orig = []
		tela.transforma()
		self.redesenha()
		
	#-------------------------------------------
	#Comando de redesenhar a tela
	#-------------------------------------------	
	def redesenha(self):
		self.desenho.delete("all")
		inf=4e-10
		for i in range(len(tela.lista_trans)):
			if tela.lista_trans[i].__class__.__name__=='linha':
				pt1 = tela.lista_trans[i].pt1
				pt2 = tela.lista_trans[i].pt2
				cor = tela.lista_trans[i].cor
				
				ax = (pt1.x / (pt1.z + inf)) * self.largura + self.largura/2
				ay = (pt1.y / (pt1.z + inf)) * self.altura + self.altura/2
				
				bx = (pt2.x / (pt2.z + inf)) * self.largura + self.largura/2
				by = (pt2.y / (pt2.z + inf)) * self.altura + self.altura/2
				
				self.desenho.create_line(ax, ay, bx, by, fill=cor)
	
	#-------------------------------------------
	#Comando do slider de rotação x
	#-------------------------------------------
	def roda_x(self, valor):
		tela.rotacao.x = float(valor)
		tela.transforma()
		self.redesenha()

	#-------------------------------------------
	#Comando do slider de rotação y
	#-------------------------------------------
	def roda_y(self, valor):
		tela.rotacao.y = float(valor) + 180.0
		tela.transforma()
		self.redesenha()
		
	#-------------------------------------------
	#Comando do slider de rotação z
	#-------------------------------------------
	def roda_z(self, valor):
		tela.rotacao.z = float(valor)
		tela.transforma()
		self.redesenha()
		
	#-------------------------------------------
	#Comando do spinbox de translação x
	#-------------------------------------------
	def olho_x(self):
		tela.olho.x = float(self.trans_x.get())
		tela.transforma()
		self.redesenha()
		
	#-------------------------------------------
	#Comando do spinbox de translação x
	#-------------------------------------------
	def olho_y(self):
		tela.olho.y = float(self.trans_y.get())
		tela.transforma()
		self.redesenha()

	#-------------------------------------------
	#Comando do spinbox de translação x
	#-------------------------------------------
	def olho_z(self):
		tela.olho.z = float(self.trans_z.get())
		tela.transforma()
		self.redesenha()

	def __init__(self,toplevel,parar, trava):
		self.trava = trava
		#------------------------------------------
		#Cria o visualizador de códico e sua barra de rolagem
		#------------------------------------------
		self.visual_gcode = Listbox(toplevel, width=40, height=10, selectmode=SINGLE)
		self.visual_gcode.grid(row=0, column=0, columnspan=2, rowspan=2, sticky=W+E+N+S)
		self.vis_barra = Scrollbar(toplevel)
		self.vis_barra.grid(row=0, column=2, rowspan=2, sticky=W+E+N+S)
		self.vis_barra.configure(command=self.visual_gcode.yview)
		self.visual_gcode.configure(yscrollcommand=self.vis_barra.set)
		
		#------------------------------------------
		#Cria a área de desenho
		#------------------------------------------
		self.desenho = Canvas(toplevel, width=self.largura, height=self.altura, bd=5, relief=RIDGE)
		self.desenho.grid(row=0, column=3, columnspan=4, rowspan=2, sticky=W+E+N+S)
		self.desenho.after(50, self.temporal)
		
		#------------------------------------------
		#Cria os comandos de rotação do desenho
		#------------------------------------------
		Label(toplevel, text='Rotacao X:').grid(row=2, column=3, sticky=E)
		self.rot_x = Scale(toplevel, orient=HORIZONTAL, resolution=1.0, to=360.0, command=self.roda_x)
		self.rot_x.grid(row=2, column=4, sticky=W+E+N+S)
		self.rot_x.set(30)
		
		Label(toplevel, text='Rotacao Y:').grid(row=3, column=3, sticky=E)
		self.rot_y = Scale(toplevel, orient=HORIZONTAL, resolution=1.0, to=360.0, command=self.roda_y)
		self.rot_y.grid(row=3, column=4, sticky=W+E+N+S)
		
		Label(toplevel, text='Rotacao Z:').grid(row=4, column=3, sticky=E)
		self.rot_z = Scale(toplevel, orient=HORIZONTAL, resolution=1.0, to=360.0, command=self.roda_z)
		self.rot_z.grid(row=4, column=4, sticky=W+E+N+S)
		self.rot_z.set(30)
		
		#------------------------------------------
		#Cria os comandos de translação do desenho
		#------------------------------------------
		Label(toplevel, text='Pos. X:').grid(row=2, column=5, sticky=E)
		self.trans_x = Spinbox(toplevel, from_=-10000, to=10000.0, width=10, command=self.olho_x, format='%.2f')
		self.trans_x.grid(row=2, column=6)
		self.trans_x.delete(0,"end")
		self.trans_x.insert(0,-1)
		self.trans_x.invoke('buttonup')
		
		Label(toplevel, text='Pos. Y:').grid(row=3, column=5, sticky=E)
		self.trans_y = Spinbox(toplevel, from_=-10000, to=10000.0, width=10, command=self.olho_y, format='%.2f')
		self.trans_y.grid(row=3, column=6)
		self.trans_y.delete(0,"end")
		self.trans_y.insert(0,-1)
		self.trans_y.invoke('buttonup')
		
		Label(toplevel, text='Pos. Z:').grid(row=4, column=5, sticky=E)
		self.trans_z = Spinbox(toplevel, from_=-10000, to=10000.0, width=10, command=self.olho_z, format='%.2f')
		self.trans_z.grid(row=4, column=6)
		self.trans_z.delete(0,"end")
		self.trans_z.insert(0,2)
		self.trans_z.invoke('buttonup')
		
		#------------------------------------------
		#Cria os botões
		#------------------------------------------
		self.b_simula = Button(toplevel, text='Simula GCODE', command=self.simula)
		self.b_simula.grid(row=2, column=1)
		
		self.b_pausa = Button(toplevel, text='Pausa', command=self.pausa)
		self.b_pausa.grid(row=4, column=1)
		
		self.b_exec = Button(toplevel, text='Executa', command=self.exc)
		self.b_exec.grid(row=3, column=1)
		
		#------------------------------------------
		#Cria o menu da janela
		#------------------------------------------
		self.menu = Menu(toplevel)
		toplevel.config(menu=self.menu)
		self.arq_menu = Menu(self.menu)
		self.menu.add_cascade(label="Arquivo", menu=self.arq_menu)
		self.arq_menu.add_command(label="Abrir...", command=self.abrir_arq)
		self.arq_menu.add_command(label="Fecha", command=self.fechar_arq)
		self.arq_menu.add_separator()
		self.arq_menu.add_command(label="Sair", command=toplevel.destroy)
		self.aj_menu = Menu(self.menu)
		self.menu.add_cascade(label="Ajuda", menu=self.aj_menu)
		self.aj_menu.add_command(label="Sobre...", command=self.sobre)
		
		
		
		self.e = Entry(toplevel)
		self.e.grid(row=3, column=0)
		self.e.delete(0, END)
		self.e.insert(0, "a default value")
		
		self.e2 = Entry(toplevel)
		self.e2.grid(row=4, column=0)
		self.e2.delete(0, END)
		self.e2.insert(0, "0")
		
	
raiz=Tk()

parar = threading.Event()
trava = threading.RLock()

Janela(raiz, parar, trava)

tarefa = threading.Thread(target=background, args = (parar,trava))
tarefa.start()

raiz.mainloop()

parar.set()
#trava.release()