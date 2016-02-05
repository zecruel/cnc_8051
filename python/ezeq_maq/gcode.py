# -*- coding: cp1252 -*-
import math		#importa as funcoes matematicas
import re
import ponto

vel_max = 20
class Gcode:
	def __init__(self):
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
		inf = 4e-10	#um numero infinitesimal, para evitar a divisao por zero
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
		
		chaves = re.finditer("([a-zA-Z]{1}) *(\-?\.?\d+\.?\d*)", self.linha)
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
				elif comando == 91: self.modo = 'relativo'
			
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
				self.lista.append(ponto.l_usin(ponto.ponto(self.pre_x,self.pre_y,self.pre_z),ponto.ponto(self.x,self.y,self.z), vel))
				
		#-------- Movimentos circulares -------------
		elif(self.estilo == 2 or self.estilo == 3) and flag:
			
			#-------------------------------------------------------------------------------------------
			#---- transforma o arco em segmentos de reta, criando um polígono regular inscrito
			#----------------------------------------------------------------------------------------------
			n = 32 #numero de vertices do polígono regular que aproxima o circulo ->bom numero 

			sentido = 1				#o sentido padrão do algoritmo eh contra relógio (G03)
			if (self.estilo == 2): sentido = -1 # para sentido do relógio (G02) sentido eh negativo
			if (self.plano == 'xz'):
				pre_x = self.pre_x
				pre_y = self.pre_z
				pre_z = self.pre_y
				
				atual_x = self.x
				atual_y = self.z
				atual_z = self.y
				
				offset_x = i
				offset_y = k
				corr_sent = -1  # o sentido de rotação do plano xz (G18) eh inverso aos outros
				
			elif (self.plano == 'yz'):
				pre_x = self.pre_y
				pre_y = self.pre_z
				pre_z = self.pre_x
				
				atual_x = self.y
				atual_y = self.z
				atual_z = self.x
				
				offset_x = j
				offset_y = k
				corr_sent = 1
				
			else:
				pre_x = self.pre_x
				pre_y = self.pre_y
				pre_z = self.pre_z
				
				atual_x = self.x
				atual_y = self.y
				atual_z = self.z
				
				offset_x = i
				offset_y = j
				corr_sent = 1
			
			centro_x = pre_x + offset_x		#encontra o centro via offsets
			centro_y = pre_y + offset_y
			angulo = 0.0
			
			#---------encontra o centro via raio do arco---------------
			if (raio):			#pega o valor via parametro passado no codigo

				if ((pre_x - atual_x) == 0) and ((pre_y - atual_y) != 0):
					centro_y = pre_y + (atual_y - pre_y)/2
					centro_x = atual_x
					angulo = math.pi
					ang_ini = math.atan2((pre_y - centro_y),(pre_x - centro_x))
					if ((ang_ini < 0) & (sentido>inf)): ang_ini = (2*math.pi) + ang_ini
				
				elif ((pre_y - atual_y) == 0) and ((pre_x - atual_x) != 0):
					centro_x = pre_x + (atual_x - pre_x)/2
					centro_y = atual_y
					angulo = math.pi
					ang_ini = math.atan2((pre_y - centro_y),(pre_x - centro_x))
					if ((ang_ini < 0) & (sentido>inf)): ang_ini = (2*math.pi) + ang_ini
				
				else:				
					#solução do sistema de equações quadraticas para encontrar o centro do arco
					C = 2*atual_x - 2*pre_x
					D = 2*atual_y - 2*pre_y
					E = (pre_y)**2+(pre_x)**2-(atual_x)**2-(atual_y)**2
					
					alfa = (D/C)**2 + 1
					beta = 2*pre_x*D/C+2*D*E/(C**2)-2*pre_y
					gama = pre_x**2+2*pre_x*E/C+(E/C)**2+pre_y**2-r**2

					delta = math.sqrt(beta**2-(4*alfa*gama))
					
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
						ang_ini = math.atan2((pre_y - c_y),(pre_x - c_x))
						if ((ang_ini < 0) & (sentido>inf)): ang_ini = (2*math.pi) + ang_ini
						ang_i.append(ang_ini)
				
						#--------angulo final obtido das coordenadas
						ang_final = math.atan2((atual_y - c_y),(atual_x -c_x))
						if ((ang_final < 0) & (sentido>0)): ang_final = (2*math.pi) + ang_final
				
						angulo = (ang_final-ang_ini) * sentido #angulo do arco
						if angulo <= 0: angulo = angulo + 2*math.pi
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
				#---------encontra o raio via offsets---------------
				r = math.sqrt(offset_x**2+offset_y**2) #calcula a partir os offsets, ou
				
				#---------angulo inicial obtido das coordenadas iniciais
				ang_ini = math.atan2(-offset_y,-offset_x)
				if (ang_ini < 0): ang_ini = (2*math.pi) + ang_ini
			
				#--------angulo final obtido das coordenadas
				ang_final = math.atan2((atual_y - centro_y),(atual_x -centro_x ))
				if (ang_final < 0): ang_final = (2*math.pi) + ang_final
			
				angulo = (ang_final-ang_ini) * sentido * corr_sent #angulo do arco
				if angulo <= 0: angulo = angulo + 2*math.pi
			
			passo = angulo*n/(2*math.pi)	#descobre quantos passos para o laço a seguir

			passos = abs(int(passo)) #numero de vertices do arco

			passo_z = (atual_z - pre_z)/abs(passo) #se houver cood. Z, faz interpolação helicoidal
			
			pre_x = self.pre_x
			pre_y = self.pre_y
			pre_z = self.pre_z
			
			atual_x = self.x
			atual_y = self.y
			atual_z = self.z
			#já começa do segundo vértice
			for i in range(1,passos):
				
				if (self.plano == 'xz'):
					px = centro_x + r * math.cos(2 * math.pi * i * sentido * corr_sent/ n + ang_ini)
					pz = centro_y + r * math.sin(2 * math.pi * i * sentido * corr_sent/ n + ang_ini)
					py = pre_y + passo_z
				elif (self.plano == 'yz'):
					py = centro_x + r * math.cos(2 * math.pi * i * sentido * corr_sent/ n + ang_ini)
					pz = centro_y + r * math.sin(2 * math.pi * i * sentido * corr_sent/ n + ang_ini)
					px = pre_x + passo_z
				else:
					px = centro_x + r * math.cos(2 * math.pi * i * sentido * corr_sent/ n + ang_ini)
					py = centro_y + r * math.sin(2 * math.pi * i * sentido * corr_sent/ n + ang_ini)
					pz = pre_z + passo_z
				
				self.lista.append(ponto.l_usin(ponto.ponto(pre_x,pre_y,pre_z),ponto.ponto(px,py,pz), self.velocidade))
				pre_x=px
				pre_y=py
				pre_z=pz
				
			# o ultimo vertice do arco eh o ponto final, nao calculado no laço
			self.lista.append(ponto.l_usin(ponto.ponto(pre_x,pre_y,pre_z),ponto.ponto(atual_x,atual_y,atual_z), self.velocidade))
			

if __name__ == "__main__":
	print 'Modulo que interpreta Gcode'