# -*- coding: cp1252 -*-
import Tkinter as tk
import threading
import tkFileDialog
import tkMessageBox
from ezeq_maq.ponto import*

#-----------------------------------------------------------------------------------------
#--------- Constroi a GUI  --------------------------------------
#------------------------------------------------------------------------------------------
class Janela(threading.Thread):
	def __init__(self, group=None, target=None, name=None,
				args=(), kwargs=None, verbose=None):
		''' Deriva a classe threading, permitindo a passagem
		de argumentos na inicializacao da classe '''
		threading.Thread.__init__(self, group=group, target=target,
							name=name, verbose=verbose)
		
		#os argumentos passados sao armaz. em variaveis internas
		#args eh uma tupla e kwargs eh um dicionario
		self.args = args
		self.kwargs = kwargs
		
		#------------- variaveis internas ---------------
		self.altura = 400 # Tamanho da Área de desenho
		self.largura = 400
		self.iter = 0 #iterador
		self.iter_antigo = -1 #iterador
		self.iter2 = 0
		self.continua = 0
		self.executa = 0
		self.simulacao = 0
		
		self.pt1 = ponto() #para calculo do cursor
		self.pt2 = ponto()
		self.t_cursor = 0
		
		self.best_view_x = 0
		self.best_view_y = 0
		self.best_view_z = 100
		
		self.vel_max = 2000
		self.vel_min = 10
		self.movimentos = []
		
		self.lista = self.args[0]
		self.figura = self.args[1]
		self.codigo = self.args[2]
		self.contador = self.args[3]
		self.libera = self.args[4]

		#Imagem = bmp._saveBitMapPPM( )
		self.photo = ''#PhotoImage(data= Imagem)
		#------------------------------------------------------------
		
		self.start()
	
	def sai(self):
		self.raiz.quit()

	def run(self):
		''' Modifica o metodo run da classe threading'''
		
		# constroi a GUI tk normalmente
		self.raiz = tk.Tk()
		self.raiz.protocol("WM_DELETE_WINDOW", self.sai)
		
		#self.trava = trava
		#------------------------------------------
		#Cria o visualizador de codigo e sua barra de rolagem
		#------------------------------------------
		self.visual_gcode = tk.Listbox(self.raiz, width=40,
							height=10,
							selectmode=tk.SINGLE)
		self.visual_gcode.grid(row=0, column=0, columnspan=2, 
						rowspan=2, 
						sticky=tk.W+tk.E+tk.N+tk.S)
		self.vis_barra = tk.Scrollbar(self.raiz)
		self.vis_barra.grid(row=0, column=2, rowspan=2, 
						sticky=tk.W+tk.E+tk.N+tk.S)
		self.vis_barra.configure(command=self.visual_gcode.yview)
		self.visual_gcode.configure(yscrollcommand=self.vis_barra.set)
		
		#------------------------------------------
		#Cria a área de desenho
		#------------------------------------------
		self.desenho = tk.Canvas(self.raiz, width=self.largura,
							height=self.altura, bd=5,
							relief=tk.RIDGE)
		self.desenho.grid(row=0, column=3, columnspan=4,
					rowspan=2, sticky=tk.W+tk.E+tk.N+tk.S)
		self.desenho.after(50, self.temporal)
		
		#------------------------------------------
		#Cria os comandos de rotação do desenho
		#------------------------------------------
		tk.Label(self.raiz, text='Rotacao X:').grid(row=2, column=3,
										sticky=tk.E)
		self.rot_x = tk.Scale(self.raiz, orient=tk.HORIZONTAL,
						resolution=1.0, to=360.0,
						command=self.roda_x)
		self.rot_x.grid(row=2, column=4,
					sticky=tk.W+tk.E+tk.N+tk.S)
		self.rot_x.set(60)
		
		tk.Label(self.raiz, text='Rotacao Y:').grid(row=3, column=3,
										sticky=tk.E)
		self.rot_y = tk.Scale(self.raiz, orient=tk.HORIZONTAL,
						resolution=1.0, to=360.0,
						command=self.roda_y)
		self.rot_y.grid(row=3, column=4, 
					sticky=tk.W+tk.E+tk.N+tk.S)
		
		tk.Label(self.raiz, text='Rotacao Z:').grid(row=4, column=3,
										sticky=tk.E)
		self.rot_z = tk.Scale(self.raiz, orient=tk.HORIZONTAL,
						resolution=1.0, to=360.0,
						command=self.roda_z)
		self.rot_z.grid(row=4, column=4,
					sticky=tk.W+tk.E+tk.N+tk.S)
		#self.rot_z.set(30)
		
		#------------------------------------------
		#Cria os comandos de translação do desenho
		#------------------------------------------
		tk.Label(self.raiz, text='Offset X:').grid(row=2, column=5,
									sticky=tk.E)
		self.trans_x = tk.Scale(self.raiz, from_=-100., to=100.,
						orient=tk.HORIZONTAL,
						command=self.offset_x)
		self.trans_x.grid(row=2, column=6)
		
		tk.Label(self.raiz, text='Offset Y:').grid(row=3, column=5,
									sticky=tk.E)
		self.trans_y = tk.Scale(self.raiz, from_=-100., to=100.,
						orient=tk.HORIZONTAL,
						command=self.offset_y)
		self.trans_y.grid(row=3, column=6)
		
		tk.Label(self.raiz, text='Zoom:').grid(row=4, column=5,
									sticky=tk.E)
		self.trans_z = tk.Scale(self.raiz, from_=10, to=500,
						orient=tk.HORIZONTAL,
						command=self.zoom)
		self.trans_z.grid(row=4, column=6)
		self.trans_z.set(100)
		
		#------------------------------------------
		#Cria o comando de escala de cores do desenho
		#------------------------------------------
		tk.Label(self.raiz, text='Esc. Cor:').grid(row=5, column=5,
									sticky=tk.E)
		self.esc_cor = tk.Scale(self.raiz, from_=10, to=500,
						orient=tk.HORIZONTAL,
						command=self.escala_cor)
		self.esc_cor.grid(row=5, column=6)
		self.esc_cor.set(100)
		
		#------------------------------------------
		#Cria os botões
		#------------------------------------------
		self.b_simula = tk.Button(self.raiz, text='Simula GCODE',
							command=self.simula)
		self.b_simula.grid(row=2, column=1)
		
		self.b_pausa = tk.Button(self.raiz, text='Pausa',
							command=self.pausa)
		self.b_pausa.grid(row=4, column=1)
		
		self.b_exec = tk.Button(self.raiz, text='Executa',
							command=self.exc)
		self.b_exec.grid(row=3, column=1)
		
		#------------------------------------------
		#Cria o menu da janela
		#------------------------------------------
		self.menu = tk.Menu(self.raiz)
		self.raiz.config(menu=self.menu)
		self.arq_menu = tk.Menu(self.menu)
		self.menu.add_cascade(label="Arquivo", menu=self.arq_menu)
		self.arq_menu.add_command(label="Abrir...",
								command=self.abrir_arq)
		self.arq_menu.add_command(label="Fecha",
								command=self.fechar_arq)
		self.arq_menu.add_separator()
		self.arq_menu.add_command(label="Sair",
								command=self.raiz.destroy)
		self.aj_menu = tk.Menu(self.menu)
		self.menu.add_cascade(label="Ajuda", menu=self.aj_menu)
		self.aj_menu.add_command(label="Sobre...",
							command=self.sobre)
		
		self.e = tk.Entry(self.raiz)
		self.e.grid(row=4, column=0)
		self.e.delete(0, tk.END)
		self.e.insert(0, "a default value")
		
		self.raiz.mainloop()	#entra no mainloop da Tk
	
	# -----------------------------------------
	#Comando de abrir arquivo
	#------------------------------------------
	def abrir_arq(self):
		arquivo = tkFileDialog.askopenfilename(title='Abrir')
		if arquivo:
			self.limpa()
			self.visual_gcode.delete(0,tk.END)
			with open(arquivo) as f:
				self.movimentos = []
				self.lista.limpa()
				for num_linha, line in enumerate(f):
					# retira os separadores de linha e os substitui por espaços
					line = line.replace('\r', ' ') 
					line = line.replace('\n', ' ')
					self.visual_gcode.insert(tk.END,line)
					# interpreta previamente para determinar
					# os limites e ajuste da tela
					self.codigo.linha = line
					self.codigo.interpreta()
					
					#--------------------------------teste
					
					for i in range(len(self.codigo.lista)):			#cada objeto da lista interpretada eh adicionado ao desenho
						pt1 = self.codigo.lista[i].pt1
						pt2 = self.codigo.lista[i].pt2
						if ((pt2.x-pt1.x)!=0) or (
						     (pt2.y-pt1.y)!=0) or (
						     (pt2.z-pt1.z)!=0):
							#movimentos.append((pt2.x-pt1.x, pt2.y-pt1.y, pt2.z-pt1.z, codigo.lista[i].vel, num_linha))
							self.movimentos.append(
								{'pt1':pt1, 'pt2':pt2,
								'vel':self.codigo.lista[i].vel,
								'linha':num_linha})
							self.lista.add_lin(pt1, pt2,
									self.codigo.lista[i].vel)
							#self.lista.cursor_x = pt1.x
							#self.lista.cursor_y = pt1.y
							#self.lista.cursor_z = pt1.z
					#------------------------------------------
			self.best_view_z = (1.3*(max(self.codigo.x_max,
							self.codigo.y_max,
							self.codigo.z_max) - 
							min(self.codigo.x_min,
							self.codigo.y_min,
							self.codigo.z_min)))
			self.trans_x.set(0)
			self.trans_y.set(0)
			self.trans_z.set(100)
			self.esc_cor.set(100)
			
		
			self.best_view_x = ((self.codigo.x_max -
					self.codigo.x_min)/2) + self.codigo.x_min
		
			self.best_view_y = ((self.codigo.y_max -
					self.codigo.y_min)/2) + self.codigo.y_min
			
			self.lista.olho_x = self.best_view_x
			self.lista.olho_y = self.best_view_y
			if self.best_view_z > 0:
				self.lista.olho_z = self.best_view_z
			
			self.lista.rot_x = int(self.rot_x.get())
			self.lista.rot_y = int(self.rot_y.get())
			self.lista.rot_z = int(self.rot_z.get())

			#self.lista.v_min = self.codigo.f_min
			
			self.codigo.limpa()
			self.redesenha()
	
	#------------------------------------------
	#Comando de fechar arquivo
	#--------------------------------------------
	def fechar_arq(self):
		if tkMessageBox.askokcancel("Fechar", 
							"Deseja fechar o arquivo?"):
			self.visual_gcode.delete(0,tk.END)
	
	#------------------------------------------
	#Informações do programa
	#------------------------------------------
	def sobre(self):
		label = tkMessageBox.showinfo("Sobre o programa",
				"Interpretador, simulador de Gcode")	
	
	#------------------------------------------
	#rotina temporal
	#--------------------------------------------
	def temporal(self):
		#global contador
		#global exec_pronto
		#global movimentos
		
		if self.simulacao and (self.iter < self.visual_gcode.size()) and self.continua:
			if self.iter != self.iter_antigo:
				self.iter_antigo = self.iter
				#self.iter2 = 0
				self.visual_gcode.selection_clear(0,tk.END)  		#limpa a linha de codigo selecionada anterior
				self.visual_gcode.selection_set(self.iter)  		#e mostra a linha atual
				if (self.iter%23 >= 22): 					#se a linha selecionada esta proxima do final da exibicao
					self.visual_gcode.yview(self.iter)		#rearranja a exibição da lista (rola automaticamente)
			self.redesenha()
		self.e.delete(0, tk.END) #teste
		self.e.insert(0, self.contador.get()) #teste
		#print self.contador.get()
		
		self.desenho.after(100, self.temporal) # reagenda
	
	
	#------------------------------------------
	#Comando de simular GCODE
	#--------------------------------------------
	def simula(self):
		self.limpa()
		self.continua = 1
		self.simulacao = 1
		with self.libera:
			self.libera.notify()
		
	def pausa(self):
		self.continua = 0
		self.trava.acquire() #teste
			
	def exc(self):
		self.limpa()
		self.executa=1
		self.continua = 1
		'''tarefa = threading.Thread(target=background,
							args = (parar,trava))
		tarefa.start()'''
		
	def limpa(self):
		self.desenho.delete("all")
		self.continua = 0
		self.executa=0 
		self.iter = 0
		self.iter_antigo = -1
		self.codigo.limpa()
		#self.lista.limpa()
		self.redesenha()
		
	#-------------------------------------------
	#Comando de redesenhar a tela
	#-------------------------------------------	
	def redesenha(self):
		self.desenho.delete("all")
		#bmp = BitMap( self.largura, self.altura, Color.WHITE )
		#global figura
		#global lista
		self.figura.limpa()
		#print lista.num
		self.lista.draw(self.figura)
		Imagem = self.figura.ret_ppm()
		self.photo = tk.PhotoImage(data= Imagem)
		self.desenho.create_image(8, 8, image=self.photo,
							anchor=tk.NW)
	
	#-------------------------------------------
	#Comando do slider de rotação x
	#-------------------------------------------
	def roda_x(self, valor):
		self.lista.rot_x = float(valor)
		self.redesenha()

	#-------------------------------------------
	#Comando do slider de rotação y
	#-------------------------------------------
	def roda_y(self, valor):
		self.lista.rot_y = float(valor)
		self.redesenha()
		
	#-------------------------------------------
	#Comando do slider de rotação z
	#-------------------------------------------
	def roda_z(self, valor):
		self.lista.rot_z = float(valor)
		self.redesenha()
		
	#-------------------------------------------
	#Comando do slider de translação x
	#-------------------------------------------
	def offset_x(self, valor):		
		#self.lista.olho_x = int(valor)*0.1*self.best_view_x + self.best_view_x
		self.lista.offset_x = int(valor)/100.0
		self.redesenha()
		
		
	#-------------------------------------------
	#Comando do slider de translação y
	#-------------------------------------------
	def offset_y(self, valor):
		#self.lista.olho_y = int(valor)*0.2*self.best_view_y +self.best_view_y
		self.lista.offset_y = int(valor)/100.0
		self.redesenha()

	#-------------------------------------------
	#Comando do slider de translação z
	#-------------------------------------------
	def zoom(self, valor):
		'''
		a = int(valor)*.2*self.best_view_z +self.best_view_z
		if a > 0:
			self.lista.olho_z = a'''
		self.lista.zoom = int(valor)/100.0
		self.redesenha()
	
	#-------------------------------------------
	#Comando do slider de escala de cor
	#-------------------------------------------
	def escala_cor(self, valor):
		self.lista.esc_cor = int(valor)/100.0
		self.redesenha()
		
if __name__ == "__main__":
	print 'Modulo que constroi a GUI Tk/Tcl do interpretador G-code'