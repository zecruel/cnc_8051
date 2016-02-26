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
def execucao(contador, janela, mens_trans, mens_rec, libera, pronto):
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
				if delta_x!=0 or delta_y!=0 or delta_z!=0:
					mens_trans.put('executa')
					janela.lista.cursor_x = pt1.x
					janela.lista.cursor_y = pt1.y
					janela.lista.cursor_z = pt1.z
					with pronto:
						pronto.wait()
					a = mens_rec.get()
					mens_rec.task_done()
			janela.iter += 1 #passa para a proxima

#comunicacao com a placa
def comunica(instr, trava, mens_trans, mens_rec, contador, pronto):
	while True:
		#trava. acquire()
		
		#transmissao de mensagem
		if not mens_trans.empty():
			a= mens_trans.get()
			mens_trans.task_done()
			contador.set(2)
			
		#recepcao de mensagem
		if contador.get() > 0:
			contador.set(contador.get()-1)
		if contador.get() == 1:
			mens_rec.put(contador.get())
			with pronto:
				pronto.notify()
		#trava.release()
		time.sleep(0.15)
		
		
#vel_max = 2000
#vel_min = 10.0
contador = ponteiro(0)
exec_pronto = 0
movimentos = []

mens_trans = Queue.Queue()
mens_rec  = Queue.Queue()
instr = None

parar = threading.Event()
trava = threading.RLock()
libera = threading.Condition()
pronto = threading.Condition()

figura = ezeq_maq.render.bitmap(400,400,(255,255,255))
lista = ezeq_maq.render.wireframe()
codigo = ezeq_maq.gcode.Gcode()
	
janela = ezeq_maq.gui.Janela(args=(lista, figura, codigo, contador, libera))

execut = threading.Thread(target=execucao,
					args = (contador, janela, mens_trans, mens_rec, libera, pronto))
execut.setDaemon(True)
execut.start()

tarefa = threading.Thread(target=comunica,
					args = (instr, trava, mens_trans, mens_rec, contador, pronto))
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