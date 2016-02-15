# -*- coding: cp1252 -*-
import threading
import ezeq_maq.gcode
import ezeq_maq.render
import ezeq_maq.gui
from ezeq_maq.ponto import*

#-- debugando------------------------
import logging
logging.basicConfig(filename='log_filename.txt',
			level=logging.DEBUG,
			format='%(asctime)s - %(levelname)s - %(message)s')
#logging.debug('This is a log message.')
#-----------------------------------------------------

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
		
vel_max = 2000
vel_min = 10.0
contador = 0
exec_pronto = 0
movimentos = []
figura = ezeq_maq.render.bitmap(400,400,(255,255,255))
lista = ezeq_maq.render.wireframe()
codigo = ezeq_maq.gcode.Gcode()
	
janela = ezeq_maq.gui.Janela(args=(lista, figura, codigo, contador))

parar = threading.Event()
trava = threading.RLock()

#janela.start()

#Janela(raiz, parar, trava)

#raiz.mainloop()

parar.set()
#trava.release()