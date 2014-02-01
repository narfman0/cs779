#!/bin/python
import socket
import sys
import time
import traceback

DEFAULT_HOST="localhost"
DEFAULT_PORT=10009

def getClientSocket(host,port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))
  return s

def startMulticastReceiver(group, port):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  try:
    s.seckopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  except AttributeError:
    traceback.print_exc()
  s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32) 
  s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
  s.bind((group, port))
  host = socket.gethostbyname(socket.gethostname())
  s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
  s.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, 
                   socket.inet_aton(group) + socket.inet_aton(host))
  return s

def startClient(host,port):
  s = getClientSocket(host,port)
  receiverSocket = None
  lastKeepAlive=0
  while True:
    try:
      if time.time() - lastKeepAlive > 2:
        lastKeepAlive = time.time()
        s.send('KeepAlive')
        
      multicastGroupData,serverAddr=s.recvfrom(1024)
      if '|' in multicastGroupData:
        if receiverSocket is None:
          ip,port=multicastGroupData.split('|')
          receiverSocket = startMulticastReceiver(ip,int(port))
        else:
          pass #normal keepalive, working as expected
      else:
        print('Error from server keepalive, no | character')
      data, addr = receiverSocket.recvfrom(1024)
    except socket.error, e:
      traceback.print_exc()
      pass

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print('No host given as argument 1, defaulting to ' + DEFAULT_HOST)
    print('No port given as argument 2, defaulting to ' + str(DEFAULT_PORT))
    host=DEFAULT_HOST
    port=DEFAULT_PORT
  else:
    host=sys.argv[1]
    port=sys.argv[2]
  startClient(host,port)