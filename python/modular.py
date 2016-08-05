# -*- coding: cp1252 -*-
import threading
import ezeq_maq.gcode
import ezeq_maq.render
import ezeq_maq.gui
import ezeq_maq.convert as conv
from ezeq_maq.ponto import*

import Queue
import math
import copy

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
def execucao(janela, libera, mens_trans, mens_rec, maq_parada, maq_livre, maq_buff, contador, pronto, parar, gui_mens):
	while True:
		with libera:
			libera.wait()
			tamanho = janela.visual_gcode.size()
			iter = 0
			iter_anterior = 0
		while janela.simulacao and (iter <= tamanho) and not parar.is_set():
			janela.codigo.linha = janela.visual_gcode.get(iter) 	#pega a linha atual
			janela.codigo.interpreta() #e interpreta
			if maq_buff.get() == 0:
				janela.iter = iter
			else:
				janela.iter = iter_anterior
			for i in range(len(janela.codigo.lista)): #eh retornado uma lista de comandos
				if not parar.is_set():
					nome = janela.codigo.lista[i].__class__.__name__ #nome do comando
					#print nome
					if nome == 'l_usin': #se o comando for para usinagem
						pt1 = copy.deepcopy(janela.codigo.lista[i].pt1)
						pt2 = copy.deepcopy(janela.codigo.lista[i].pt2)
						vel = janela.codigo.lista[i].vel
						delta_x = (pt2.x-pt1.x)
						delta_y = (pt2.y-pt1.y)
						delta_z = (pt2.z-pt1.z)
						dist = math.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
						tempo = dist/vel
					elif nome == 'tempo':
						tempo = janela.codigo.lista[i].t
						delta_x = delta_y = delta_z = vel =0
						#print tempo
					elif nome =='espera':
						tempo = delta_x = delta_y = delta_z = vel = 0
						gui_mens.set('motivo espera: '+ janela.codigo.lista[i].tipo)
						with maq_parada:
							maq_parada.wait()
						# a condicao 'libera' poderah ser substituida neste caso
						with libera:
							libera.wait()
						gui_mens.set('Maq em execucao')
					else:
						tempo = delta_x = delta_y = delta_z = vel = 0
					
					if tempo!=0:
						#mens_trans.put(tempo)
						mens_trans.put((tempo, delta_x, delta_y, delta_z, vel))
						with maq_livre:
							maq_livre.wait()
					iter_anterior = iter
						#a = mens_rec.get()
						#mens_rec.task_done()
				else: break
			iter += 1 #passa para a proxima
		else:
			parar.clear()
			print 'parada'

#comunicacao com a placa
def comunica(instr, mens_trans, mens_rec, maq_parada, maq_livre, maq_buff, contador, vel_sim, pronto, janela, parar):
	#temp = 0
	a=0
	x = 0
	y = 0
	z = 0
	vel = 0
	t = 0
	#vel_sim = 10
	while True:
		#recepcao de mensagem
		if janela.simulacao and janela.continua:
			#simulacao
			if contador.get() > 0:
				contador.set(contador.get()-1)
				janela.wireframe.cursor_x += x * total
				janela.wireframe.cursor_y += y * total
				janela.wireframe.cursor_z += z * total
			elif maq_buff.get() > 0:
				maq_buff.set(maq_buff.get()-1)
				if maq_buff.get() != 0:
					t, x, y, z, vel = a
					total = 1.0/(int(t*vel_sim.get())+1)
					contador.set(int(t*vel_sim.get())+1) #teste
		else:
			pass
		
		#transmissao de mensagem
		if not mens_trans.empty() and maq_buff.get() < 2:
			a= mens_trans.get()
			mens_trans.task_done()
			config = conv.maq_usina(a[1], a[2], a[3], a[4]) #converte p/ parametros de maquina
			if a[4] != 0: # se tiver usinagem
				comando = [1] #manda executar
				mens = comando + config
			elif a[0] != 0: # se não usinagem, mas tiver tempo
				comando = [1] #manda executar
				#recalcula e substitui o parametro de tempo
				mens = comando + conv.maq_tempo(a[0]) + config[2:]
				#print conv.maq_le(mens[1:])
			else:
				mens = []
			
			if janela.simulacao:
				print mens
				if maq_buff.get() == 0:
					t, x, y, z, vel = a
					total = 1.0/(int(t*vel_sim.get())+1)
					contador.set(int(t*vel_sim.get())+1) #teste
					with maq_livre:
						maq_livre.notify()
				maq_buff.set(maq_buff.get()+1)
			else:
				# ============== manda mensagem de execucao
				pass
		#trava.release()
		
		#verifica o status da maquina
		if janela.continua:
			if maq_buff.get() == 0 and contador.get() == 0:
				with maq_parada:
					maq_parada.notify()
			if maq_buff.get() < 2:
				with maq_livre:
					maq_livre.notify()
		else:
			#==================== manda sinal de pausa
			pass
		if parar.is_set():
			#==================== manda sinal de parar
			contador.set(0)
			maq_buff.set(0)
			with maq_parada:
				maq_parada.notify()
			with maq_livre:
				maq_livre.notify()
		time.sleep(0.1)

contador = ponteiro(0)

maq_buff = ponteiro(0)
vel_sim = ponteiro(1)
gui_mens = ponteiro('Maq parada')

mens_trans = Queue.Queue()
mens_rec  = Queue.Queue()
instr = None

parar = threading.Event()
trava = threading.RLock()
libera = threading.Condition()
pronto = threading.Condition()
maq_parada = threading.Condition()
maq_livre = threading.Condition()

#figura = ezeq_maq.render.bitmap(300,300,(255,255,255))
figura = ''
lista = ezeq_maq.render.wireframe()
codigo = ezeq_maq.gcode.Gcode()
	
janela = ezeq_maq.gui.Janela(args=(lista, figura, codigo, contador,
						libera, parar, gui_mens))

execut = threading.Thread(target=execucao,
					args = (janela, libera, mens_trans, mens_rec,
					maq_parada, maq_livre, maq_buff, contador, 
					pronto, parar, gui_mens))
execut.setDaemon(True)
execut.start()

tarefa = threading.Thread(target=comunica,
					args = (instr, mens_trans, mens_rec,
					maq_parada, maq_livre, maq_buff, contador, vel_sim, pronto, janela, parar))
tarefa.setDaemon(True)
tarefa.start()
