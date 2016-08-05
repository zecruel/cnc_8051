# -*- coding: cp1252 -*-
import Tkinter as tk
import threading
import tkFileDialog
import tkMessageBox
from ponto import*
from render import bitmap

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
		self.altura = 600 # Tamanho da Área de desenho
		self.largura = 600
		self.iter = 0 #iterador
		self.iter_antigo = -1 #iterador
		self.iter2 = 0
		self.continua = 0
		self.executa = 0
		self.simulacao = 0
		
		self.best_view_x = 0
		self.best_view_y = 0
		self.best_view_z = 100
		
		self.vel_max = 2000
		self.vel_min = 10
		self.movimentos = []
		
		self.wireframe = self.args[0]
		#self.figura = self.args[1]
		self.codigo = self.args[2]
		self.contador = self.args[3]
		self.libera = self.args[4]
		self.e_parar = self.args[5]
		self.mens = self.args[6]

		#------------------------------------------------------------
		
		self.start()
	
	def sai(self):
		self.raiz.quit()
		self.figura.sai() #saida do SDL

	def run(self):
		''' Modifica o metodo run da classe threading'''
		
		# constroi a GUI tk normalmente
		
		self.raiz = tk.Tk()
		self.raiz.protocol("WM_DELETE_WINDOW", self.sai)
		
		#self.trava = trava
		
		#------------------------------------------
		#Cria o visualizador de codigo e sua barra de rolagem
		#------------------------------------------
		self.f_visual_gcode = tk.Frame(self.raiz)
		self.f_visual_gcode.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
		self.visual_gcode = tk.Listbox(self.f_visual_gcode, width=40,
							height=25,
							selectmode=tk.SINGLE)
		self.visual_gcode.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
		self.vis_barra = tk.Scrollbar(self.f_visual_gcode)
		self.vis_barra.grid(row=0, column=1, sticky=tk.W+tk.E+tk.N+tk.S)
		self.vis_barra.configure(command=self.visual_gcode.yview)
		self.visual_gcode.configure(yscrollcommand=self.vis_barra.set)
		self.visual_gcode.after(50, self.temporal)
		
		#------------------------------------------
		#Cria os comandos de rotação do desenho
		#------------------------------------------
		#frame dos comandos de visualizacao
		self.f_transf = tk.Frame(self.raiz)
		self.f_transf.grid(row=0, column=1, sticky=tk.E)
		
		tk.Label(self.f_transf, text='Rotacao X:').grid(row=0, column=0,
										sticky=tk.E)
		self.rot_x = tk.Scale(self.f_transf, orient=tk.HORIZONTAL,
						resolution=1.0, to=360.0,
						command=self.roda_x)
		self.rot_x.grid(row=0, column=1,
					sticky=tk.W+tk.E+tk.N+tk.S)
		self.rot_x.set(60)
		
		tk.Label(self.f_transf, text='Rotacao Y:').grid(row=1, column=0,
										sticky=tk.E)
		self.rot_y = tk.Scale(self.f_transf, orient=tk.HORIZONTAL,
						resolution=1.0, to=360.0,
						command=self.roda_y)
		self.rot_y.grid(row=1, column=1, 
					sticky=tk.W+tk.E+tk.N+tk.S)
		
		tk.Label(self.f_transf, text='Rotacao Z:').grid(row=2, column=0,
										sticky=tk.E)
		self.rot_z = tk.Scale(self.f_transf, orient=tk.HORIZONTAL,
						resolution=1.0, to=360.0,
						command=self.roda_z)
		self.rot_z.grid(row=2, column=1,
					sticky=tk.W+tk.E+tk.N+tk.S)
		#self.rot_z.set(30)
		
		#------------------------------------------
		#Cria os comandos de translação do desenho
		#------------------------------------------
		tk.Label(self.f_transf, text='Offset X:').grid(row=3, column=0,
									sticky=tk.E)
		self.trans_x = tk.Scale(self.f_transf, from_=-100, to=100,
						orient=tk.HORIZONTAL,
						command=self.offset_x)
		self.trans_x.grid(row=3, column=1)
		
		tk.Label(self.f_transf, text='Offset Y:').grid(row=4, column=0,
									sticky=tk.E)
		self.trans_y = tk.Scale(self.f_transf, from_=-100, to=100,
						orient=tk.HORIZONTAL,
						command=self.offset_y)
		self.trans_y.grid(row=4, column=1)

		tk.Label(self.f_transf, text='Zoom:').grid(row=5, column=0,
									sticky=tk.E)
		self.trans_z = tk.Scale(self.f_transf, from_=10, to=500,
						orient=tk.HORIZONTAL,
						command=self.zoom)
		self.trans_z.grid(row=5, column=1)
		self.trans_z.set(100)
		
		#------------------------------------------
		#Cria o comando de escala de cores do desenho
		#------------------------------------------
		tk.Label(self.f_transf, text='Esc. Cor:').grid(row=6, column=0,
									sticky=tk.E)
		self.esc_cor = tk.Scale(self.f_transf, from_=10, to=500,
						orient=tk.HORIZONTAL,
						command=self.escala_cor)
		self.esc_cor.grid(row=6, column=1)
		self.esc_cor.set(100)
		
		#------------------------------------------
		#Cria os botões
		#------------------------------------------
		
		self.f_botoes = tk.Frame(self.raiz)
		self.f_botoes.grid(row=1, column=0, sticky=tk.W)
		
		self.b_simula = tk.Button(self.f_botoes, text='Simula GCODE',
							command=self.simula)
		self.b_simula.grid(row=0, column=0)
		
		self.b_exec = tk.Button(self.f_botoes, text='Executa',
							command=self.exc)
		self.b_exec.grid(row=1, column=0)
		
		self.b_pausa = tk.Button(self.f_botoes, text='Pausa',
							command=self.pausa)
		self.b_pausa.grid(row=0, column=1)
		
		self.b_continua = tk.Button(self.f_botoes, text='Continua',
							command=self.vai)
		self.b_continua.grid(row=1, column=1)
		
		self.b_para = tk.Button(self.f_botoes, text='Para',
							command=self.para)
		self.b_para.grid(row=2, column=1)
		
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
		
		
		#cria a janela SDL para visualizacao
		self.figura = bitmap(self.largura, self.altura,(0,0,0))
		
		self.raiz.update()
		#print self.raiz.winfo_x(), self.raiz.winfo_y(), self.raiz.winfo_width(), self.raiz.winfo_height()
		
		#altera a posicao da janela SDL
		self.figura.lib.SDL_SetWindowPosition(self.figura.window, self.raiz.winfo_x()+self.raiz.winfo_width()+30, self.raiz.winfo_y()+30)
		
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
				self.wireframe.limpa()
				self.wireframe.add_pt(ponto(0,0,0),0) #o primeiro ponto eh sempre zero
				
				for num_linha, line in enumerate(f):
					# retira os separadores de linha e os substitui por espaços
					line = line.replace('\r', ' ') 
					line = line.replace('\n', ' ')
					self.visual_gcode.insert(tk.END,line)
					# interpreta previamente para determinar
					# os limites e ajuste da tela
					self.codigo.linha = line
					self.codigo.interpreta()
					
					for i in range(len(self.codigo.lista)):			#cada objeto da lista interpretada eh adicionado ao desenho
						nome = self.codigo.lista[i].__class__.__name__ #nome do comando
						if nome == 'l_usin': #se o comando for para usinagem
							pt1 = self.codigo.lista[i].pt1
							pt2 = self.codigo.lista[i].pt2
							if ((pt2.x-pt1.x)!=0) or (
							     (pt2.y-pt1.y)!=0) or (
							     (pt2.z-pt1.z)!=0):
								#adiciona somente o ultimo ponto ao desenho
								self.wireframe.add_pt(pt2,
										self.codigo.lista[i].vel)
			self.best_view_z = (1.3*(max(self.codigo.x_max,
							self.codigo.y_max,
							self.codigo.z_max) - 
							min(self.codigo.x_min,
							self.codigo.y_min,
							self.codigo.z_min)))
			self.trans_x.set(0.0)
			self.trans_y.set(0.0)
			self.wireframe.offset_x = 0
			self.wireframe.offset_y = 0
			self.trans_z.set(100)
			self.esc_cor.set(100)
			
		
			self.best_view_x = ((self.codigo.x_max -
					self.codigo.x_min)/2) + self.codigo.x_min
		
			self.best_view_y = ((self.codigo.y_max -
					self.codigo.y_min)/2) + self.codigo.y_min
			
			self.wireframe.olho_x = self.best_view_x
			self.wireframe.olho_y = self.best_view_y
			if self.best_view_z > 0:
				self.wireframe.olho_z = self.best_view_z
			
			self.wireframe.rot_x = int(self.rot_x.get())
			self.wireframe.rot_y = int(self.rot_y.get())
			self.wireframe.rot_z = int(self.rot_z.get())

			#self.wireframe.v_min = self.codigo.f_min
			
			self.codigo.limpa()
			self.wireframe.draw(self.figura) #redesenha o wire
	
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
		if self.simulacao and (self.iter < self.visual_gcode.size()) and self.continua:
			if self.iter != self.iter_antigo:
				#self.iter2 = 0
				self.visual_gcode.selection_clear(0,tk.END)  		#limpa a linha de codigo selecionada anterior
				self.visual_gcode.selection_set(self.iter)  	#e mostra a linha atual
				delta = self.iter - self.iter2
				if (delta >= 23): 	#se a linha selecionada esta proxima do final da exibicao
					self.visual_gcode.yview(self.iter) #rearranja a exibição da lista (rola automaticamente)
					self.iter2 = self.iter
				self.iter_antigo = self.iter
		#self.wireframe.draw(self.figura) #redesenha o wire
		self.wireframe.draw_cursor(self.figura) #redesenha somente a posicao do cursor
		
		self.e.delete(0, tk.END) #teste
		self.e.insert(0, self.mens.get()) #teste
		#print self.contador.get()
		
		self.visual_gcode.after(200, self.temporal) # reagenda
	
	
	#------------------------------------------
	#Comando de simular GCODE
	#--------------------------------------------
	def simula(self):
		self.limpa()
		self.continua = 1
		self.simulacao = 1
		self.wireframe.cursor_x += 0
		self.wireframe.cursor_y += 0
		self.wireframe.cursor_z += 0
		with self.libera:
			self.libera.notify()
		
	def pausa(self):
		self.continua = 0
		
	def vai(self):
		self.continua = 1
		# ========testa a troca de ferramenta
		with self.libera:
			self.libera.notify()
		#=========================
		
	def para(self):
		self.continua = 0
		self.simulacao = 0
		self.e_parar.set()
	def exc(self):
		self.limpa()
		self.executa=1
		self.continua = 1
		'''tarefa = threading.Thread(target=background,
							args = (parar,trava))
		tarefa.start()'''
		
	def limpa(self):
		#self.desenho.delete("all")
		self.continua = 0
		self.executa=0 
		self.iter = 0
		self.iter2 = 0
		self.iter_antigo = -1
		self.codigo.limpa()
		#self.wireframe.limpa()
		self.wireframe.cursor_x = 0
		self.wireframe.cursor_y = 0
		self.wireframe.cursor_z = 0
		self.wireframe.draw(self.figura) #redesenha o wire
	
	#-------------------------------------------
	#Comando do slider de rotação x
	#-------------------------------------------
	def roda_x(self, valor):
		self.wireframe.rot_x = float(valor)
		self.wireframe.draw(self.figura) #redesenha o wire

	#-------------------------------------------
	#Comando do slider de rotação y
	#-------------------------------------------
	def roda_y(self, valor):
		self.wireframe.rot_y = float(valor)
		self.wireframe.draw(self.figura) #redesenha o wire
		
	#-------------------------------------------
	#Comando do slider de rotação z
	#-------------------------------------------
	def roda_z(self, valor):
		self.wireframe.rot_z = float(valor)
		self.wireframe.draw(self.figura) #redesenha o wire
	
	#-------------------------------------------
	#Comando do slider de translação x
	#-------------------------------------------
	def offset_x(self, valor):
		self.wireframe.offset_x = int(valor)/100.0 #modifica a posicao do desenho
		self.wireframe.draw(self.figura) #redesenha o wire
	
	#-------------------------------------------
	#Comando do slider de translação y
	#-------------------------------------------
	def offset_y(self, valor):
		self.wireframe.offset_y = int(valor)/100.0 #modifica a posicao do desenho
		self.wireframe.draw(self.figura) #redesenha o wire

	#-------------------------------------------
	#Comando do slider de translação z
	#-------------------------------------------
	def zoom(self, valor):
		self.wireframe.zoom = int(valor)/100.0
		self.wireframe.draw(self.figura) #redesenha o wire
	
	#-------------------------------------------
	#Comando do slider de escala de cor
	#-------------------------------------------
	def escala_cor(self, valor):
		self.wireframe.esc_cor = int(valor)/100.0
		self.wireframe.draw(self.figura) #redesenha o wire
		
if __name__ == "__main__":
	print 'Modulo que constroi a GUI Tk/Tcl do interpretador G-code'