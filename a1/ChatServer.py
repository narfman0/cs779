#!/bin/python
import socket
import sys
import time
import traceback
from random import randint

DEFAULT_PORT=10009

def generateMulticastGroupPort():
  return randint(9999,11001)

def generateMulticastGroupIP():
  return str(randint(224,239)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255))

def getServerSocket(port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((socket.gethostname(), port))
  s.listen(5)
  return s

def removeOldConnections(connectedTimeMap):
  for key,value in connectedTimeMap.iteritems():
    if time.time() - value > 5:#older than 5 seconds
      del connectedTimeMap[key]
      print('Removing connection which has not been kept alive within 5 seconds ' + key)

def receiveData(s,connectedTimeMap):
  try:
    data, addr = s.recvfrom(1024) #doesn't block
    connectedTimeMap[addr] = time.time()
  except socket.error, e:
    pass

#Send ip/port to all connected (keepalive response)
def sendMulticastInfo(s,multicastGroupPort,multicastGroupIP):
  try:
    s.sendall(str(multicastGroupPort) + '|' + multicastGroupIP)
  except socket.error, e:
    pass

def startServer(port):
  s=getServerSocket(port)
  multicastGroupPort=generateMulticastGroupPort()
  multicastGroupIP=generateMulticastGroupIP()
  connectedTimeMap={}
  while True:
    try:
      s.accept()
    except:
      traceback.print_exc()
      pass
    receiveData(s,connectedTimeMap)
    removeOldConnections(connectedTimeMap)
    sendMulticastInfo(s,multicastGroupPort,multicastGroupIP)

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print('No port given as argument 1, defaulting to ' + str(DEFAULT_PORT))
    port=DEFAULT_PORT
  else:
    port=sys.argv[1]
  startServer(port)
