# -*- coding: cp1252 -*-
import copy

class ponto:
	def __init__(self, x = 0.0, y = 0.0, z = 0.0):
		self.x = x
		self.y = y
		self.z = z

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

class ponteiro:
	def __init__(self, obj): self.obj = obj
	def get(self):    return self.obj
	def set(self, obj):      self.obj = obj

class tempo:
	def __init__(self, t = 0.0):
		self.t = t
		
class espera:
	def __init__(self, tipo = 'suspende'):
		self.tipo = tipo

if __name__ == "__main__":
	print 'Modulo que define um os tipos de dados (ponto, linha, etc.)'