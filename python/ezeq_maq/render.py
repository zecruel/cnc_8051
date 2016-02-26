import math
import array
import setup

class wireframe:
	def __init__(self):
		self.list_princ = array.array('f') # lista de objetos principal
		self.num = 0 # numero de itens na lista principal
		
		#variaveis de visualizacao na tela
		self.offset_x = 0
		self.offset_y = 0
		self.zoom = 1.0
		
		self.esc_cor = 1.0 #escala de cor - afeta a velocidade maxima
		
		# angulos de rotacao ao longo do eixo - variaveis tipo inteiro 0-360
		self.rot_x = 0
		self.rot_y = 0
		self.rot_z = 0
		
		# velocidades
		self.v_max = setup.vel_max
		self.v_min = 0.1 * setup.vel_max
		
		# ponto de observacao para calcular a projecao no plano 2D
		self.olho_x = 0.0
		self.olho_y = 0.0
		self.olho_z = 100.0
		
		# ponto de deslocamento 3D do cursor
		self.cursor_x = 0.0
		self.cursor_y = 0.0
		self.cursor_z = 0.0
		
		# tabelas de seno e cosseno para melhorar a velocidade
		self.sen = array.array('f', 
		[math.sin(x*math.pi/180) for  x in range(0,361)])
		self.cos = array.array('f', 
		[math.cos(x*math.pi/180) for  x in range(0,361)])
		
		# objeto que representa os eixos na visualizacao
		self.eixos = array.array('f', [0,0,0,1,0,0,0, # x
		0,0,0,0,1,0,1, # y
		0,0,0,0,0,1,2]) # z
		
		# objeto que representa o cursor na visualizacao
		self.cursor = array.array('f', [0,0,0,0,-0.5,1,2, # ln1
		0,0,0,0.35,0.35,1,2, # ln2
		0,0,0,-0.35,0.35,1,2]) # ln3
		
	
	def limpa(self):
		self.list_princ = array.array('f') # reinicia a lista
		self.num = 0 # zera os itens na lista principal
		
	def add_lin(self, pt1, pt2, vel):
		''' adiciona linha a lista principal '''
		self.list_princ.append(pt1.x)
		self.list_princ.append(pt1.y)
		self.list_princ.append(pt1.z)
		self.list_princ.append(pt2.x)
		self.list_princ.append(pt2.y)
		self.list_princ.append(pt2.z)
		self.list_princ.append(vel)
		self.num += 1
	
	def draw(self, img):
		img_w = img.largura
		img_h = img.altura
		inf = 4e-10
		
		a = int((self.rot_z +180) % 360)  #degrees to rotate about z-axis
		b = int(self.rot_y % 360)  #degrees to rotate about y-axis
		c = int(self.rot_x % 360)  #degrees to rotate about x-axis

		xx = self.cos[a]*self.cos[b] #calc xx constant
		xy = -self.sen[a]*self.cos[b] #calc xy constant
		xz = -self.sen[b] #calc xz constant 
	
		yx = self.sen[a]*self.cos[c] - self.cos[a]*self.sen[b]*self.sen[c] #calc yx constant
		yy = self.cos[a]*self.cos[c] + self.sen[a]*self.sen[b]*self.sen[c] #calc yy constant
		yz = -self.cos[b]*self.sen[c] #calc yz constant 
	
		zx = self.sen[a]*self.sen[c] + self.cos[a]*self.sen[b]*self.cos[c] #calc zx constant
		zy = self.cos[a]*self.sen[c] - self.sen[a]*self.sen[b]*self.cos[c] #calc zy constant
		zz = self.cos[b]*self.cos[c] #calc zz constant
		
		for i in range(self.num):
			x1 = self.list_princ[i*7] * xx + self.list_princ[i*7+1] * xy + self.list_princ[i*7+2] * xz + self.olho_x
			y1 = self.list_princ[i*7] * yx + self.list_princ[i*7+1] * yy + self.list_princ[i*7+2] * yz + self.olho_y
			z1 = self.list_princ[i*7] * zx + self.list_princ[i*7+1] * zy + self.list_princ[i*7+2] * zz - self.olho_z
			
			x2 = self.list_princ[i*7+3] * xx + self.list_princ[i*7+4] * xy + self.list_princ[i*7+5] * xz + self.olho_x
			y2 = self.list_princ[i*7+3] * yx + self.list_princ[i*7+4] * yy + self.list_princ[i*7+5] * yz + self.olho_y
			z2 = self.list_princ[i*7+3] * zx + self.list_princ[i*7+4] * zy + self.list_princ[i*7+5] * zz - self.olho_z
			
			p1x = int(self.zoom*((x1 / (z1 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
			p1y = int(self.zoom*((y1 / (z1+ inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			p2x = int(self.zoom*((x2 / (z2 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
			p2y = int(self.zoom*((y2 / (z2 + inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			img.line(p1x, p1y, p2x, p2y, self.rgb(self.list_princ[i*7+6]))
		
		#desenha os eixos para orientacao
		cor_eixo = [(255,0,0), (0,255,0), (0,0,255)]
		for i in range(3):
			x1 = self.eixos[i*7] * xx + self.eixos[i*7+1] * xy + self.eixos[i*7+2] * xz + 4
			y1 = self.eixos[i*7] * yx + self.eixos[i*7+1] * yy + self.eixos[i*7+2] * yz + 4
			z1 = self.eixos[i*7] * zx + self.eixos[i*7+1] * zy + self.eixos[i*7+2] * zz - 10
			
			x2 = self.eixos[i*7+3] * xx + self.eixos[i*7+4] * xy + self.eixos[i*7+5] * xz + 4
			y2 = self.eixos[i*7+3] * yx + self.eixos[i*7+4] * yy + self.eixos[i*7+5] * yz + 4
			z2 = self.eixos[i*7+3] * zx + self.eixos[i*7+4] * zy + self.eixos[i*7+5] * zz - 10
			
			p1x = int((x1 / (z1 + inf)) * img_w + img_w/2)
			p1y = int((y1 / (z1+ inf)) * img_h + img_h/2)
			
			p2x = int((x2 / (z2 + inf)) * img_w + img_w/2)
			p2y = int((y2 / (z2 + inf)) * img_h + img_h/2)
			
			img.line(p1x, p1y, p2x, p2y, cor_eixo[int(self.eixos[i*7+6])])
		
		#desenha o cursor
		esc = 0.1 # a escala do cursor nunca pode ser maior ou igual a 1.0
		for i in range(3):
			xc1 = self.cursor_x + self.cursor[i*7] * esc * abs(self.olho_z)
			yc1 = self.cursor_y + self.cursor[i*7+1] * esc * abs(self.olho_z)
			zc1 = self.cursor_z + self.cursor[i*7+2] * esc * abs(self.olho_z)
			
			x1 = xc1 * xx + yc1 * xy + zc1 * xz + self.olho_x
			y1 = xc1 * yx + yc1 * yy + zc1 * yz + self.olho_y
			z1 = xc1 * zx + yc1 * zy + zc1 * zz - self.olho_z
			
			xc1 = self.cursor_x + self.cursor[i*7+3] * esc * abs(self.olho_z)
			yc1 = self.cursor_y + self.cursor[i*7+4] * esc * abs(self.olho_z)
			zc1 = self.cursor_z + self.cursor[i*7+5] * esc * abs(self.olho_z)
			
			x2 = xc1 * xx + yc1 * xy + zc1 * xz + self.olho_x
			y2 = xc1 * yx + yc1 * yy + zc1 * yz + self.olho_y
			z2 = xc1 * zx + yc1 * zy + zc1 * zz - self.olho_z
			
			p1x = int(self.zoom*((x1 / (z1 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
			p1y = int(self.zoom*((y1 / (z1+ inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			p2x = int(self.zoom*((x2 / (z2 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
			p2y = int(self.zoom*((y2 / (z2 + inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			img.line(p1x, p1y, p2x, p2y, (0,0,0))
	
	def rgb(self, mag):
		"""
		These functions, when given a magnitude mag between cmin and cmax, return
		a colour tuple (red, green, blue). Light blue is cold (low magnitude)
		and yellow is hot (high magnitude). Return a tuple of strings to be used in Tk plots.
		"""
		try:
			# normalize to [0,1]
			x = (mag - self.esc_cor*self.v_min)/(self.esc_cor*self.v_max -
										self.esc_cor* self.v_min)
		except:
			# cmax = cmin
			x = 0.5
		blue = 4*(0.75-x)
		if blue < 0.: blue=0.
		if blue > 1.: blue=1.
		red  = 4*(x-0.25)
		if red < 0.: red=0.
		if red > 1.: red=1.
		green= 4*math.fabs(x-0.5)-1.0
		if green < 0.: green=0.
		if green > 1.: green=1.
		return (int(red*255), int(blue*255), int(green*255))
		

class bitmap:
	def __init__(self, largura=10, altura=10, fundo=(255,255,255)):
		self.largura = largura
		self.altura = altura
		self.fundo = fundo
		self.bitarray = array.array('B')
		for i in range(self.largura*self.altura):
			self.bitarray.append(self.fundo[0])
			self.bitarray.append(self.fundo[1])
			self.bitarray.append(self.fundo[2])
	
	def limpa(self):
		for i in range(self.largura*self.altura):
			self.bitarray[i*3:i*3+3] = array.array(
			'B',[self.fundo[0], self.fundo[1], self.fundo[2]])
	
	def set_pt(self, x, y, cor):
		if (0 < x < self.largura) & (0< y < self.altura):
			y = self.altura - y
			pos = 3*(x + y*self.largura)
			self.bitarray[pos:pos+3] = array.array(
			'B',[cor[0], cor[1], cor[2]])
		
	def line(self, x0, y0, x1, y1, cor):
		dx = abs(x1 - x0)
		dy = abs(y1 - y0)
		x, y = x0, y0
		sx = -1 if x0 > x1 else 1
		sy = -1 if y0 > y1 else 1
		
		if abs(dx+dy) > 0:
			'''otimizacao para linhas verticais e horizontais.
			traduzido da linguagem C da pagina
			http://www.willperone.net/Code/codeline.php'''
			if dx == 0:  # verticais
				#print 'linha vertical'
				if 0 <= x < self.largura:
					if (dy*sy) > 0:
						#y = y0
						while y <= y1:
							self.set_pt(x, y, cor)
							y += 1
					else:
						y = y1
						while y <= y0:
							self.set_pt(x, y, cor)
							y += 1
			elif dy == 0:  # horizontais
				#print 'linha horizontal'
				if 0 <= y < self.altura:
					if (dx*sx) > 0:
						#x = x0
						while x <= x1:
							self.set_pt(x, y, cor)
							x += 1
					else:
						x = x1
						while x <= x0:
							self.set_pt(x, y, cor)
							x += 1
			else:
				'''Bresenham's line algorithm
				http://rosettacode.org/wiki/Bitmap/Bresenham%27s_line_algorithm#Python'''
				#print 'linha em angulo'
				if dx > dy:
					err = dx / 2.0
					while x != x1:
						self.set_pt(x, y, cor)
						err -= dy
						if err < 0:
							y += sy
							err += dx
						x += sx
				else:
					err = dy / 2.0
					while y != y1:
						self.set_pt(x, y, cor)
						err -= dx
						if err < 0:
							x += sx
							err += dy
						y += sy        
				self.set_pt(x, y, cor)
	
	def ret_ppm(self):
		ppm = 'P6 ' + str(self.largura) + ' ' + str(self.altura) + ' 255 \r'
		ppm += self.bitarray.tostring()
		return ppm

if __name__ == "__main__":
	print 'Modulo que renderiza um wireframe 3D em uma projecao 2D. O resultado eh um bitmap PPM binario'