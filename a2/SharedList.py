#!/usr/bin/python

from multiprocessing import Lock
from multiprocessing.sharedctypes import Array, Value
from ctypes import Structure, c_char_p, c_int

class SharedList(object):
	class Client(Structure):
		_fields_ = [('ip', c_char_p), ('port', c_int)]
	
	def __repr__(self):
			return '{}:{}'.format(self.ip, self.port)
		
	def __init__(self, capacity):
		self.lock = Lock()
		self._size = Value('i', 0)
		elements=[('0.0.0.0', 10000) for _i in range(0,capacity)]
		self.capacity = capacity
		self._clients = Array(self.Client, elements, lock=self.lock)
	
	def size(self):
		size = self._size.value
		return size
	
	def add(self, ip, port):
		if self._size.value < self.capacity:
			self._clients[self._size.value] = (ip, port)
			self._size.value += 1
			return True
		else:
			return False

	def remove(self, ip, port):
		for i in range(self._size.value):
			if self._clients[i].ip == ip and self._clients[i].port == port:
				for j in range(i, self._size.value):
					self._clients[j] = self._clients[j+1]
				self._size.value -= 1
				return True
		return False

	def getClients(self):
		return [client for client in self._clients[:self._size.value]]