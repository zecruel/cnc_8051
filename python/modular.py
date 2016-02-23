# -*- coding: cp1252 -*-
import threading
import ezeq_maq.gcode
import ezeq_maq.render
import ezeq_maq.gui
from ezeq_maq.ponto import*

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
def background(parar, trava, contador):
	#global contador
	global exec_pronto
	
	for i in range(0,10000):
		if parar.is_set(): break
		trava. acquire()
		contador.set(i)
		time.sleep(.1)
		#exec_pronto = 1
		trava.release()
		
#vel_max = 2000
#vel_min = 10.0
contador = ponteiro(0)
exec_pronto = 0
movimentos = []
figura = ezeq_maq.render.bitmap(400,400,(255,255,255))
lista = ezeq_maq.render.wireframe()
codigo = ezeq_maq.gcode.Gcode()
	
janela = ezeq_maq.gui.Janela(args=(lista, figura, codigo, contador))

parar = threading.Event()
trava = threading.RLock()

tarefa = threading.Thread(target=background,
					args = (parar, trava, contador))
tarefa.start()

#janela.start()

#Janela(raiz, parar, trava)

#raiz.mainloop()
#contador.set(2)
time.sleep(10)
parar.set()
#print contador
#trava.release()