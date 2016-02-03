# -*- coding: cp1252 -*-
from Tkinter import *
import tkFileDialog
import tkMessageBox
from math import *		#importa as funcoes matematicas
import copy
import re
import time
import threading
import ezeq_maq.gcode
import ezeq_maq.render
from ezeq_maq.bmp import*
from ezeq_maq.ponto import*


vel_max = 2000
vel_min = 10.0
contador = 0
exec_pronto = 0
movimentos = []
figura = ezeq_maq.render.bitmap(400,400,(255,255,255))
lista = ezeq_maq.render.wireframe()

def background(parar,trava):
	global contador
	global exec_pronto
	
	for i in range(0,10000):
		if parar.is_set(): break
		trava. acquire()
		contador = i
		time.sleep(.01)
		exec_pronto = 1
		trava.release()

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

	tick_t = tempo * 1000 * ms_tick 
	
	#print 'tempo=', tempo, 's, vel=', vel, 'mm/s'
	
	vel_x = x / tempo
	vel_y = y / tempo
	vel_z = z / tempo

	tick_x = ms_tick *1000 * mm_rev / (passos_rev * vel_x + inf)
	tick_y = ms_tick *1000 * mm_rev / (passos_rev * vel_y + inf)
	tick_z = ms_tick *1000 * mm_rev / (passos_rev * vel_z + inf)

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
	
	return d_maq(tick_t, tick_x, tick_y, tick_z)
		

codigo = ezeq_maq.gcode.Gcode()

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
	continua = 0
	executa = 0
	
	best_view_x = 0
	best_view_y = 0
	best_view_z = 100

	#Imagem = bmp._saveBitMapPPM( )
	photo = ''#PhotoImage(data= Imagem)
	
	# -----------------------------------------
	#Comando de abrir arquivo
	#------------------------------------------
	def abrir_arq(self):
		global vel_max
		global vel_min
		global movimentos
		global lista
		arquivo = tkFileDialog.askopenfilename(title='Abrir')
		if arquivo != "":
			self.limpa()
			self.visual_gcode.delete(0,END)
			with open(arquivo) as f:
				movimentos = []
				for num_linha, line in enumerate(f):
					line = line.replace('\r', ' ') #retira os separadores de linha e os substitui por espaços
					line = line.replace('\n', ' ')
					self.visual_gcode.insert(END,line)
					#---------interpreta previamente
					#--------- para determinar os limites e ajuste da tela
					codigo.linha = line
					codigo.interpreta()
					
					#--------------------------------teste
					
					for i in range(len(codigo.lista)):			#cada objeto da lista interpretada eh adicionado ao desenho
						pt1 = codigo.lista[i].pt1
						pt2 = codigo.lista[i].pt2
						if ((pt2.x-pt1.x)!=0) or ((pt2.y-pt1.y)!=0) or ((pt2.z-pt1.z)!=0):
							#movimentos.append((pt2.x-pt1.x, pt2.y-pt1.y, pt2.z-pt1.z, codigo.lista[i].vel, num_linha))
							movimentos.append({'pt1':pt1, 'pt2':pt2, 'vel':codigo.lista[i].vel, 'linha':num_linha})
							lista.add_lin(pt1,pt2,codigo.lista[i].vel)
					#--------------------------------------------------------------------------------------------------------------
			self.best_view_z = (1.3*(max(codigo.x_max, codigo.y_max, codigo.z_max) - min(codigo.x_min, codigo.y_min, codigo.z_min)))
			self.trans_z.set(0)
		
			self.best_view_x = ((codigo.x_max - codigo.x_min)/2) + codigo.x_min
			self.trans_x.set(0)
		
			self.best_view_y = ((codigo.y_max - codigo.y_min)/2) + codigo.y_min
			self.trans_y.set(0)
			
			lista.olho_x = self.best_view_x
			lista.olho_y = self.best_view_y
			if self.best_view_z > 0:
				lista.olho_z = self.best_view_z
			
			lista.rot_x = int(self.rot_x.get())
			lista.rot_y = int(self.rot_y.get())
			lista.rot_z = int(self.rot_z.get())

			if codigo.f_max:
				lista.vel_max = 2 * codigo.f_max
				lista.vel_min = codigo.f_min
			else:
				lista.vel_max = lista.vel_min = 1.0
			#print teste
			codigo.limpa()
			self.redesenha()
	
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
		global movimentos
		
		if  self.continua & (self.iter < len(movimentos)):
			self.visual_gcode.selection_clear(0,END)
			self.visual_gcode.selection_set(movimentos[self.iter]['linha'])
			if (movimentos[self.iter]['linha']%23 == 0): 
				self.visual_gcode.yview(movimentos[self.iter]['linha'])
			#codigo.linha = self.visual_gcode.get(self.iter)
			#codigo.interpreta()
			
			if self.executa:
				if len(movimentos) > 0:
					pt1 = movimentos[self.iter]['pt1']
					pt2 = movimentos[self.iter]['pt2']
					#vel_min = 10.0
					
					#teste
					if ((pt2.x-pt1.x)!=0) or ((pt2.y-pt1.y)!=0) or ((pt2.z-pt1.z)!=0):
						dados = converte_maq(pt2.x-pt1.x,pt2.y-pt1.y,pt2.z-pt1.z,movimentos[self.iter]['vel'])
						
					
					cor = rgb(movimentos[self.iter]['vel'],vel_min, vel_max)
					#tela.lista_orig.append(linha(pt1, pt2, cor))

					#tela.transforma()
					self.redesenha()
					
					self.iter = self.iter + 1
				
		self.e.delete(0, END) #teste
		self.e.insert(0, contador) #teste
		
		self.desenho.after(10, self.temporal) # reagenda
	
	
	#------------------------------------------
	#Comando de simular GCODE
	#--------------------------------------------
	def simula(self):
		self.limpa()
		self.continua = 1
		
	def pausa(self):
		self.continua = 0
		self.trava.acquire() #teste
			
	def exc(self):
		self.limpa()
		self.executa=1
		self.continua = 1
		tarefa = threading.Thread(target=background, args = (parar,trava))
		tarefa.start()
		
	def limpa(self):
		self.desenho.delete("all")
		self.continua = 0
		self.executa=0 
		self.iter = 0
		self.iter_antigo = -1
		codigo.limpa()
		lista.limpa()
		self.redesenha()
		
	#-------------------------------------------
	#Comando de redesenhar a tela
	#-------------------------------------------	
	def redesenha(self):
		self.desenho.delete("all")
		#bmp = BitMap( self.largura, self.altura, Color.WHITE )
		global figura
		global lista
		figura.limpa()
		#print lista.num
		lista.draw(figura)
		Imagem = figura.ret_ppm()
		self.photo = PhotoImage(data= Imagem)
		self.desenho.create_image(8,8, image=self.photo, anchor=NW)
	
	#-------------------------------------------
	#Comando do slider de rotação x
	#-------------------------------------------
	def roda_x(self, valor):
		lista.rot_x = float(valor)
		self.redesenha()

	#-------------------------------------------
	#Comando do slider de rotação y
	#-------------------------------------------
	def roda_y(self, valor):
		lista.rot_y = float(valor)
		self.redesenha()
		
	#-------------------------------------------
	#Comando do slider de rotação z
	#-------------------------------------------
	def roda_z(self, valor):
		lista.rot_z = float(valor)
		self.redesenha()
		
	#-------------------------------------------
	#Comando do spinbox de translação x
	#-------------------------------------------
	def olho_x(self, valor):		
		lista.olho_x = int(valor)*0.1*self.best_view_x + self.best_view_x
		self.redesenha()
		
		
	#-------------------------------------------
	#Comando do spinbox de translação y
	#-------------------------------------------
	def olho_y(self, valor):
		lista.olho_y = int(valor)*0.2*self.best_view_y +self.best_view_y
		self.redesenha()

	#-------------------------------------------
	#Comando do spinbox de translação z
	#-------------------------------------------
	def olho_z(self, valor):
		a = int(valor)*.2*self.best_view_z +self.best_view_z
		if a > 0:
			lista.olho_z = a
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
		self.rot_x.set(60)
		
		Label(toplevel, text='Rotacao Y:').grid(row=3, column=3, sticky=E)
		self.rot_y = Scale(toplevel, orient=HORIZONTAL, resolution=1.0, to=360.0, command=self.roda_y)
		self.rot_y.grid(row=3, column=4, sticky=W+E+N+S)
		
		Label(toplevel, text='Rotacao Z:').grid(row=4, column=3, sticky=E)
		self.rot_z = Scale(toplevel, orient=HORIZONTAL, resolution=1.0, to=360.0, command=self.roda_z)
		self.rot_z.grid(row=4, column=4, sticky=W+E+N+S)
		#self.rot_z.set(30)
		
		#------------------------------------------
		#Cria os comandos de translação do desenho
		#------------------------------------------
		Label(toplevel, text='Pos. X:').grid(row=2, column=5, sticky=E)
		self.trans_x = Scale(toplevel, from_=-20., to=20., orient=HORIZONTAL, command=self.olho_x)
		self.trans_x.grid(row=2, column=6)
		#self.trans_x.delete(0,"end")
		#self.trans_x.insert(0,-1)
		#self.trans_x.invoke('buttonup')
		
		Label(toplevel, text='Pos. Y:').grid(row=3, column=5, sticky=E)
		self.trans_y = Scale(toplevel, from_=-20., to=20., orient=HORIZONTAL, command=self.olho_y)
		self.trans_y.grid(row=3, column=6)
		#self.trans_y.delete(0,"end")
		#self.trans_y.insert(0,-1)
		#self.trans_y.invoke('buttonup')
		
		Label(toplevel, text='Pos. Z:').grid(row=4, column=5, sticky=E)
		self.trans_z = Scale(toplevel, from_=-20., to=20., orient=HORIZONTAL, command=self.olho_z)
		self.trans_z.grid(row=4, column=6)
		#self.trans_z.delete(0,"end")
		#self.trans_z.insert(0,2)
		#self.trans_z.invoke('buttonup')
		
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
		self.e.grid(row=4, column=0)
		self.e.delete(0, END)
		self.e.insert(0, "a default value")
	
raiz=Tk()

parar = threading.Event()
trava = threading.RLock()

Janela(raiz, parar, trava)

raiz.mainloop()

parar.set()
#trava.release()