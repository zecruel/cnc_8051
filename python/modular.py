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
def execucao(janela, libera, mens_trans, mens_rec, maq_parada, maq_livre, maq_buff, contador, pronto):
	while True:
		with libera:
			libera.wait()
			tamanho = janela.visual_gcode.size()
			iter = 0
			iter_anterior = 0
		while janela.simulacao and (iter_anterior <= tamanho):
			janela.codigo.linha = janela.visual_gcode.get(iter) 	#pega a linha atual
			janela.codigo.interpreta() #e interpreta
			for i in range(len(janela.codigo.lista)): #eh retornado linhas simples em uma lista
				pt1 = copy.deepcopy(janela.codigo.lista[i].pt1)
				pt2 = copy.deepcopy(janela.codigo.lista[i].pt2)
				vel = janela.codigo.lista[i].vel
				delta_x = (pt2.x-pt1.x)
				delta_y = (pt2.y-pt1.y)
				delta_z = (pt2.z-pt1.z)
				dist = math.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
				tempo = dist/vel
				if maq_buff.get() == 0:
					janela.iter = iter
				else:
					janela.iter = iter_anterior
				if delta_x!=0 or delta_y!=0 or delta_z!=0:
					#mens_trans.put(tempo)
					mens_trans.put((tempo, delta_x, delta_y, delta_z, vel))
					with maq_livre:
						maq_livre.wait()
				iter_anterior = iter
					#a = mens_rec.get()
					#mens_rec.task_done()
			iter += 1 #passa para a proxima

#comunicacao com a placa
def comunica(instr, mens_trans, mens_rec, maq_parada, maq_livre, maq_buff, contador, vel_sim, pronto, janela):
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
		if janela.simulacao:
			#simulacao
			if contador.get() > 0:
				contador.set(contador.get()-1)
				janela.wireframe.cursor_x += x * total
				janela.wireframe.cursor_y += y * total
				janela.wireframe.cursor_z += z * total
			elif maq_buff.get() > 0:
				maq_buff.set(maq_buff.get()-1)
				#verifica o status da maquina
				if maq_buff.get() == 0:
					with maq_parada:
						maq_parada.notify()
				if maq_buff.get() < 2:
					with maq_livre:
						maq_livre.notify()
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
			mens = conv.maq_escreve(a[1], a[2], a[3], a[4])
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
				pass
		#trava.release()
		time.sleep(0.1)

contador = ponteiro(0)

maq_buff = ponteiro(0)
vel_sim = ponteiro(5)

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
					maq_parada, maq_livre, maq_buff, contador, pronto))
execut.setDaemon(True)
execut.start()

tarefa = threading.Thread(target=comunica,
					args = (instr, mens_trans, mens_rec,
					maq_parada, maq_livre, maq_buff, contador, vel_sim, pronto, janela))
tarefa.setDaemon(True)
tarefa.start()