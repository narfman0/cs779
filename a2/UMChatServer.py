#!/bin/python
import select, signal, socket, struct, sys, time, traceback
from random import randint
from multiprocessing.managers import SyncManager

DEFAULT_PORT=10009
WAHAB_ACK='!E!T!'

def generateMulticastGroupPort():
  return randint(10000,11001)

def generateMulticastGroupIP():
  return str(randint(224,239)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255))

def generateNumber():
  return randint(1000000,9999999)

def getListString(connected):
  s=''
  for peername in connected:
    s += str(peername) + '\n'
  return s

def getConnectedString(uList, mList):
  s  = 'Connected UDP clients:\n'
  s += getListString(uList)
  s += 'Connected MCast clients:\n'
  s += getListString(mList)
  return s

def printConnected(uList, mList):
  print(getConnectedString(uList, mList))

def close(socketList):
  [s.close() for s in socketList]
  sys.exit()

def startMulticastReceiver(group, port):
  ur = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  ur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  ur.bind((group, port))
  mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
  ur.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  
  us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  us.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
  return (ur,us)

def removeClient(s,u,m):
  for item in u:
    if str(item) == str(s.getpeername()):
      u.remove(item)
  for item in m:
    if str(item) == str(s.getpeername()):
      m.remove(item)

def handleClientMessage(src, m, p, l, e, uList, mList, ms):
  (data,address) = src.recvfrom(1024)
  if data == WAHAB_ACK: #don't know why he does this, skipping it
    return
  try:
    dataNumber = int(data)
    if dataNumber == l:
      print('Received l from ' + str(address) + ', sending list')
      ms.sendto(getConnectedString(uList, mList), address)
    elif dataNumber == e:
      print('Received e, goodbye ' + str(address))
      removeClient(src,uList,mList)
  except:
    print(str(address) + ': ' + data)
    ms.sendto(data, (m,p))
    for cli in uList:
      ms.sendto(data, cli)

def handleNewClient(s, mList, uList, m, p, l, e):
  sockfd, _addr = s.accept()
  username = sockfd.recv(1024)
  sockfd.settimeout(2)
  try: #TCP self buffers, and usually appends the 0 or 1 on username. Catch that case here
    clientType = int(sockfd.recv(1))
  except:
    clientType = int(username[-1])
    username = username[0:-1]
  sockfd.settimeout(None)
  if clientType == 0:
    print('New MC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
    mList.append(sockfd.getpeername())
    sockfd.send(str(m))
    time.sleep(1)
  else:
    print('New UC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
    uList.append(sockfd.getpeername())
  sockfd.send(str(p))
  time.sleep(1)
  sockfd.send(str(l))
  time.sleep(1)
  sockfd.send(str(e))
  time.sleep(1)
  #sockfd.send(WAHAB_ACK)
  return sockfd
    
def handleOther(sock, uList, mList, m, p, l, e):
  print "Client went offline"
  removeClient(sock,uList,mList)
  sock.close()
  return sock

def getSharedLists():
  manager = SyncManager()
  manager.start(lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))
  return (manager.list(), manager.list())

def startServer(port):
  l=generateNumber()
  e=generateNumber()
  p=generateMulticastGroupPort()
  m=generateMulticastGroupIP()
  
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((socket.gethostname(), port))
  s.listen(1)
  u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  u.bind((socket.gethostname(), p))
  (mr,ms) = startMulticastReceiver(m, p)
  print("Using l=" + str(l) + ' e=' + str(e) + ' p=' + str(p) + ' m=' + str(m) + 
        "\ns on %s" % str(s.getsockname()) + " u on %s" % str(u.getsockname()) + 
        "\nmr on %s" % str(mr.getsockname()))
  
  (mList, uList) = getSharedLists()
  signal.signal(signal.SIGINT, lambda signum,frame: printConnected(uList, mList))
  signal.signal(signal.SIGQUIT, lambda signum,frame: close([s,u,mr,ms]))#ctrl-/
  socket_list = [sys.stdin, s, u, mr]
  while True:
    try:
      read_sockets,_w,_e = select.select(socket_list,[],[])
      for sock in read_sockets:
        if sock == s:
          socket_list.append(handleNewClient(s, mList, uList, m, p, l, e))
        elif sock == u:
          handleClientMessage(u, m, p, l, e, uList, mList, ms)
        elif sock == mr:
          handleClientMessage(u, m, p, l, e, uList, mList, ms)
        elif sock == sys.stdin:
          if sys.stdin.readline() == 'exit':
            close([s,u,mr,ms])
        else:
          socket_list.remove(handleOther(sock, uList, mList, m, p, l, e))
    except:
      #traceback.print_exc()
      #Ctrl-c perhaps, just pass
      pass

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print('No port given as argument 1, defaulting to ' + str(DEFAULT_PORT))
    port=DEFAULT_PORT
  else:
    port=int(sys.argv[1])
  startServer(port)
