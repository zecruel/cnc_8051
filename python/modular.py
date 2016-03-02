# -*- coding: cp1252 -*-
import threading
import ezeq_maq.gcode
import ezeq_maq.render
import ezeq_maq.gui
from ezeq_maq.ponto import*

import Queue
import math

import time
'''
#-- debugando------------------------
import logging
logging.basicConfig(filename='log_filename.txt',
			level=logging.DEBUG,
			format='%(asctime)s - %(levelname)s - %(message)s')
#logging.debug('This is a log message.')
#-----------------------------------------------------
'''
def execucao(janela, libera, mens_trans, mens_rec, maq_parada, maq_livre, contador, pronto):
	#global contador
	#global exec_pronto
	while True:
		with libera:
			libera.wait()
			tamanho = janela.visual_gcode.size()
		while janela.simulacao and (janela.iter <= tamanho):
			janela.codigo.linha = janela.visual_gcode.get(janela.iter) 	#pega a linha atual
			janela.codigo.interpreta() #e interpreta
			#print janela.iter
			for i in range(len(janela.codigo.lista)):			#cada objeto da lista interpretada eh adicionado ao desenho
				pt1 = janela.codigo.lista[i].pt1
				pt2 = janela.codigo.lista[i].pt2
				delta_x = (pt2.x-pt1.x)
				delta_y = (pt2.y-pt1.y)
				delta_z = (pt2.z-pt1.z)
				dist = math.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
				tempo = dist/janela.codigo.lista[i].vel
				
				janela.pt1 = pt1
				janela.pt2 = pt2
				janela.t_cursor = tempo
				
				if delta_x!=0 or delta_y!=0 or delta_z!=0:
					mens_trans.put('executa')
					with maq_livre:
						maq_livre.wait()
					#a = mens_rec.get()
					#mens_rec.task_done()
			janela.iter += 1 #passa para a proxima

#comunicacao com a placa
def comunica(instr, mens_trans, mens_rec, maq_parada, maq_livre, contador, pronto):
	temp = 0
	while True:
		#recepcao de mensagem
		#simulacao
		if contador.get() > 0:
			contador.set(contador.get()-1)
		elif temp > 0:
			temp -= 1
			#verifica o status da maquina
			if temp == 0:
				with maq_parada:
					maq_parada.notify()
			if temp < 2:
				with maq_livre:
					maq_livre.notify()
			if temp != 0:
				contador.set(10) #teste
			'''mens_rec.put(contador.get())
			with pronto:
				pronto.notify()
			with maq_parada:
				maq_parada.notify()'''
		
		#transmissao de mensagem
		if not mens_trans.empty() and temp < 2:
			a= mens_trans.get()
			mens_trans.task_done()
			print a
			if temp == 0: 
				contador.set(10) #teste
				with maq_livre:
					maq_livre.notify()
			temp += 1
			
		
		#trava.release()
		time.sleep(0.15)
		
		
#vel_max = 2000
#vel_min = 10.0
contador = ponteiro(0)
#exec_pronto = 0
#movimentos = []

mens_trans = Queue.Queue()
mens_rec  = Queue.Queue()
instr = None

parar = threading.Event()
trava = threading.RLock()
libera = threading.Condition()
pronto = threading.Condition()
maq_parada = threading.Condition()
maq_livre = threading.Condition()

figura = ezeq_maq.render.bitmap(300,300,(255,255,255))
lista = ezeq_maq.render.wireframe()
codigo = ezeq_maq.gcode.Gcode()
	
janela = ezeq_maq.gui.Janela(args=(lista, figura, codigo, contador, libera))

execut = threading.Thread(target=execucao,
					args = (janela, libera, mens_trans, mens_rec,
					maq_parada, maq_livre, contador, pronto))
execut.setDaemon(True)
execut.start()

tarefa = threading.Thread(target=comunica,
					args = (instr, mens_trans, mens_rec,
					maq_parada, maq_livre, contador, pronto))
tarefa.setDaemon(True)
tarefa.start()

#mens_trans.put('teste Queue')

#janela.start()

#Janela(raiz, parar, trava)

#raiz.mainloop()
#contador.set(2)
#time.sleep(10)
#parar.set()
#print contador
#trava.release()