import math
import array
import setup
import os
from ctypes import *

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
		#prisma
		'''#y = 0.2 - 2.43*abs(x)
		x1 = 0.14
		y1 = 0.14
		z1 = 1.0
		y2 = 0.2
		self.cursor = array.array('f', [0,0,0,0,y2,z1,2, # ln1
		0,0,0,x1,-y1,z1,2, # ln2
		-x1,-y1,z1,x1,-y1,z1,2,
		-x1,-y1,z1,0,y2,z1,2,
		x1,-y1,z1,0,y2,z1,2,
		0,0,0,-x1,-y1,z1,2]) # ln3'''
		#cone
		r = 0.2
		pz = 1.0
		pt_zero = [0.0, 0.0, 0.0]
		pt_ant = [r, 0.0, pz]
		self.cursor = array.array('f')
		for i in range(16):
			px = r * math.cos(2 * math.pi * (i+1)/16)
			py = r * math.sin(2 * math.pi * (i+1)/16)
			pt_atual = [px, py, pz]
			#cria a linha ate o zero
			for a in pt_zero:
				self.cursor.append(a)
			for a in pt_atual:
				self.cursor.append(a)
			self.cursor.append(2)
			
			#cria a linha do circulo base
			for a in pt_ant:
				self.cursor.append(a)
			for a in pt_atual:
				self.cursor.append(a)
			self.cursor.append(2)
			pt_ant = [px, py, pz]
		
	
	def limpa(self):
		self.list_princ = array.array('f') # reinicia a lista
		self.num = 0 # zera os itens na lista principal
		
	def add_pt(self, pt1, vel):
		''' adiciona ponto a lista principal '''
		self.list_princ.append(pt1.x)
		self.list_princ.append(pt1.y)
		self.list_princ.append(pt1.z)
		self.list_princ.append(vel)
		self.num += 1
	
	def draw(self, img):
		img_w = img.largura
		img_h = img.altura
		inf = 4e-10
		
		img.lib.SDL_SetRenderTarget(img.renderer, img.texture) #utiliza a imagem de fundo para desenho
		img.limpa() #limpa a imagem
		
		# calcula as constantes de rotacao e translacao
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
		
		#transforma e desenha a lista de movimentos
		#considera o ponto inicial  de cada linha -> pt final da anterior
		for i in range(self.num-1):
			#aplica as constantes aos pontos
			if i ==0:
				x1 = self.list_princ[i] * xx + self.list_princ[i+1] * xy + self.list_princ[i+2] * xz + self.olho_x
				y1 = self.list_princ[i] * yx + self.list_princ[i+1] * yy + self.list_princ[i+2] * yz + self.olho_y
				z1 = self.list_princ[i] * zx + self.list_princ[i+1] * zy + self.list_princ[i+2] * zz - self.olho_z
				p1x = int(self.zoom*((x1 / (z1 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
				p1y = int(self.zoom*((y1 / (z1+ inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			i1 = self.list_princ[i*4+4]
			i2 = self.list_princ[i*4+5]
			i3 = self.list_princ[i*4+6]
			
			x2 = i1 * xx + i2 * xy + i3 * xz + self.olho_x
			y2 = i1 * yx + i2 * yy + i3 * yz + self.olho_y
			z2 = i1 * zx + i2 * zy + i3 * zz - self.olho_z
			
			#calcula as projecoes no plano
			p2x = int(self.zoom*((x2 / (z2 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
			p2y = int(self.zoom*((y2 / (z2 + inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			img.line(p1x, p1y, p2x, p2y, self.rgb(self.list_princ[i*4+7]))
			
			p1x = p2x
			p1y = p2y
		
		#desenha os eixos para orientacao
		cor_eixo = [(255,0,0), (0,255,0), (0,0,255)]
		for i in range(3):
			#aplica as constantes aos pontos
			x1 = self.eixos[i*7] * xx + self.eixos[i*7+1] * xy + self.eixos[i*7+2] * xz + 4
			y1 = self.eixos[i*7] * yx + self.eixos[i*7+1] * yy + self.eixos[i*7+2] * yz + 4
			z1 = self.eixos[i*7] * zx + self.eixos[i*7+1] * zy + self.eixos[i*7+2] * zz - 10
			
			x2 = self.eixos[i*7+3] * xx + self.eixos[i*7+4] * xy + self.eixos[i*7+5] * xz + 4
			y2 = self.eixos[i*7+3] * yx + self.eixos[i*7+4] * yy + self.eixos[i*7+5] * yz + 4
			z2 = self.eixos[i*7+3] * zx + self.eixos[i*7+4] * zy + self.eixos[i*7+5] * zz - 10
			
			#calcula as projecoes no plano
			p1x = int((x1 / (z1 + inf)) * img_w + img_w/2)
			p1y = int((y1 / (z1+ inf)) * img_h + img_h/2)
			
			p2x = int((x2 / (z2 + inf)) * img_w + img_w/2)
			p2y = int((y2 / (z2 + inf)) * img_h + img_h/2)
			
			img.line(p1x, p1y, p2x, p2y, cor_eixo[int(self.eixos[i*7+6])])
		
		#desenha o cursor
		self.draw_cursor(img)
	
	def draw_cursor(self,img):
		#desenha o cursor
		
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
		
		esc = 0.1 # a escala do cursor nunca pode ser maior ou igual a 1.0
		
		img.lib.SDL_SetRenderTarget(img.renderer, None) #utiliza camada de desenho superior, e nao a imagem de fundo
		img.lib.SDL_RenderCopy(img.renderer, img.texture, None, None) #carrega a imagem de fundo para desenhar em cima
		
		for i in range(32):
			#aplica as constantes aos pontos
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
			
			#calcula as projecoes no plano
			p1x = int(self.zoom*((x1 / (z1 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
			p1y = int(self.zoom*((y1 / (z1+ inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			p2x = int(self.zoom*((x2 / (z2 + inf)) * img_w) + img_w/2 + self.zoom*self.offset_x*img_w)
			p2y = int(self.zoom*((y2 / (z2 + inf)) * img_h) + img_h/2 + self.zoom*self.offset_y*img_h)
			
			#cor do cursor depende do fundo
			img.line(p1x, p1y, p2x, p2y, (255-img.fundo[0], 255-img.fundo[1], 255-img.fundo[2]))
			
		img.lib.SDL_RenderPresent(img.renderer) # atualiza todo o desenho na tela
		img.lib.SDL_SetRenderTarget(img.renderer, img.texture)
	
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
		
		self.dir = os.path.dirname(os.path.abspath(__file__)).replace('\\','/') + '/'
		#------------------------------------------------------------------------------------
		# Cria um binding para o SDL 2.0
		
		# Carrega  o dll
		self.lib = CDLL(self.dir + 'SDL2.dll')
		
		#-------------------------------------------------------------------------------------
		# definicao da funcoes SDL 2.0 a serem chamadas	
		
		#----geral
		'''int SDL_Init(Uint32 flags)'''
		self.lib.SDL_Init.restype = c_int
		self.lib.SDL_Init.argtypes = [c_uint]
		
		'''void SDL_Quit(void)'''
		
		'''int SDL_PollEvent(SDL_Event* event)'''
		#self.lib.SDL_PollEvent.restype = c_int
		#self.lib.SDL_PollEvent.argtypes = [POINTER(evento)]
		
		#----window
		'''SDL_Window* SDL_CreateWindow(const char* title,
                             int         x,
                             int         y,
                             int         w,
                             int         h,
                             Uint32      flags)'''
		self.lib.SDL_CreateWindow.restypes = [c_void_p]
		self.lib.SDL_CreateWindow.argtypes = [c_char_p, c_int, c_int, c_int, c_int, c_uint]
		
		'''void SDL_DestroyWindow(SDL_Window* window)'''
		self.lib.SDL_DestroyWindow.argtypes = [c_void_p]
		
		'''void SDL_SetWindowPosition(SDL_Window* window,
                           int         x,
                           int         y)'''
		self.lib.SDL_SetWindowPosition.argtypes = [c_void_p, c_int, c_int]
		
		#----renderer
		'''SDL_Renderer* SDL_CreateRenderer(SDL_Window* window,
                                 int         index,
                                 Uint32      flags)'''
		self.lib.SDL_CreateRenderer.restypes = [c_void_p]
		self.lib.SDL_CreateRenderer.argtypes = [c_void_p, c_int, c_uint]
		
		'''void SDL_DestroyRenderer(SDL_Renderer* renderer)'''
		self.lib.SDL_DestroyRenderer.argtypes = [c_void_p]
		
		'''int SDL_SetRenderDrawColor(SDL_Renderer* renderer,
                           Uint8         r,
                           Uint8         g,
                           Uint8         b,
                           Uint8         a)'''
		self.lib.SDL_SetRenderDrawColor.restype = c_int
		self.lib.SDL_SetRenderDrawColor.argtypes = [c_void_p, c_uint, c_uint, c_uint, c_uint]
		
		'''int SDL_RenderClear(SDL_Renderer* renderer)'''
		self.lib.SDL_RenderClear.restype = c_int
		self.lib.SDL_RenderClear.argtypes = [c_void_p]
		
		'''void SDL_RenderPresent(SDL_Renderer* renderer)'''
		self.lib.SDL_RenderPresent.argtypes = [c_void_p]
		
		'''int SDL_RenderDrawLine(SDL_Renderer* renderer,
                       int           x1,
                       int           y1,
                       int           x2,
                       int           y2)'''
		self.lib.SDL_RenderDrawLine.restype = c_int
		self.lib.SDL_RenderDrawLine.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
		
		#---- Misto
		'''int SDL_CreateWindowAndRenderer(int            width,
                                int            height,
                                Uint32         window_flags,
                                SDL_Window**   window,
                                SDL_Renderer** renderer)'''
		self.lib.SDL_CreateWindowAndRenderer.restype = c_int
		self.lib.SDL_CreateWindowAndRenderer.argtypes = [c_int, c_int, c_uint, c_void_p, c_void_p]
		
		#---- Texture
		
		'''SDL_Texture* SDL_CreateTexture(SDL_Renderer* renderer,
                               Uint32        format,
                               int           access,
                               int           w,
                               int           h)'''
		#formato RGBA8888 = 373694468
		self.lib.SDL_CreateTexture.restypes = [c_void_p]
		self.lib.SDL_CreateTexture.argtypes = [c_void_p, c_uint, c_int, c_int, c_int]
		
		'''int SDL_SetRenderTarget(SDL_Renderer* renderer,
                        SDL_Texture*  texture)'''
		# criar a textura com acesso = 2
		self.lib.SDL_SetRenderTarget.restype = c_int
		self.lib.SDL_SetRenderTarget.argtypes = [c_void_p, c_void_p]
		
		'''int SDL_RenderCopy(SDL_Renderer*   renderer,
                   SDL_Texture*    texture,
                   const SDL_Rect* srcrect,
                   const SDL_Rect* dstrect)'''
		self.lib.SDL_RenderCopy.restype = c_int
		self.lib.SDL_RenderCopy.argtypes = [c_void_p, c_void_p,c_void_p, c_void_p]
		
		'''void SDL_DestroyTexture(SDL_Texture* texture)'''
		self.lib.SDL_DestroyTexture.argtypes = [c_void_p]
		
		#------------------------------------
		#inicializacao e criacao da janela SDL
		
		self.lib.SDL_Init(32)
		#cria as entidades SDL basicas
		self.window = self.lib.SDL_CreateWindow('G-code Viewer', 536805376, 536805376, self.largura, self.altura, 0) #janela com posicao indeterminada
		self.renderer = self.lib.SDL_CreateRenderer(self.window, -1, 0) #tela principal
		self.texture = self.lib.SDL_CreateTexture(self.renderer, 373694468, 2, self.largura, self.altura) #imagem de fundo
		
		#limpa a imagem de fundo com a cor determinada
		self.lib.SDL_SetRenderTarget(self.renderer, self.texture)
		self.lib.SDL_SetRenderDrawColor(self.renderer, self.fundo[0], self.fundo[1], self.fundo[2], 255)
		self.lib.SDL_RenderClear(self.renderer)
		
		#exibe a imagem de fundo na tela
		self.lib.SDL_SetRenderTarget(self.renderer, None)
		self.lib.SDL_RenderCopy(self.renderer, self.texture, None, None)
		self.lib.SDL_RenderPresent(self.renderer)
	
	def limpa(self):
		#limpa a imagem de fundo com a cor determinada
		self.lib.SDL_SetRenderTarget(self.renderer, self.texture)
		self.lib.SDL_SetRenderDrawColor(self.renderer, self.fundo[0], self.fundo[1], self.fundo[2], 255)
		self.lib.SDL_RenderClear(self.renderer)
		
	def line(self, x0, y0, x1, y1, cor):
		#desenha uma linha SDL na cor determinada
		self.lib.SDL_SetRenderDrawColor(self.renderer, cor[0], cor[1], cor[2], 0)
		self.lib.SDL_RenderDrawLine(self.renderer, x0, self.altura-y0, x1, self.altura-y1)
	
	def sai(self):
		#saida segura do SDL
		self.lib.SDL_DestroyTexture(self.texture)
		self.lib.SDL_DestroyRenderer(self.renderer)
		self.lib.SDL_DestroyWindow(self.window)
		self.lib.SDL_Quit()

if __name__ == "__main__":
	print 'Modulo que renderiza um wireframe 3D em uma projecao 2D. O resultado eh uma janela SDL2.0'