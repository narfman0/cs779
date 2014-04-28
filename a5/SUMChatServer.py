#!/bin/python
import sctp, select, signal, socket, struct, sys, time
from random import randint

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
  for socket in connected:
    s += str(socket.getpeername()) + '\n'
  return s

def getConnectedString(uList, mList, sList):
  s  = 'Connected UDP clients:\n'
  s += getListString(uList)
  s += 'Connected MCast clients:\n'
  s += getListString(mList)
  s += 'Connected SCTP clients:\n'
  s += getListString(sList)
  return s

def printConnected(uList, mList, sList):
  print(getConnectedString(uList, mList, sList))

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

def removeClient(s,uList,mList,sList):
  for clientList in (uList,mList,sList):
    if s in clientList:
      clientList.remove(s)

def handleClientMessage(data, address, src, m, p, l, e, uList, mList, sList, ms):
  if data == WAHAB_ACK: #don't know why he does this, skipping it
    return
  try:
    dataNumber = int(data)
    if dataNumber == l:
      print('Received l from ' + str(address) + ', sending list')
      ms.sendto(getConnectedString(uList, mList, sList), address)
    elif dataNumber == e:
      print('Received e, goodbye ' + str(address))
      removeClient(src,uList,mList,sList)
  except:
    print(str(address) + ': ' + data)
    ms.sendto(data, (m,p))
    for cli in uList:
      ms.sendto(data, cli.getpeername())

def handleNewClient(sockfd, clientType, username, mList, uList, sList, m, p, l, e):
  if clientType == 0:
    print('New MC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
    mList.append(sockfd)
    sockfd.send(str(m))
    time.sleep(.1)
  elif clientType == 1:
    print('New UC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
    uList.append(sockfd)
  elif clientType == 2:
    print('New SCTP Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
    sList.append(sockfd)
  sockfd.send(str(p))
  time.sleep(.1)
  sockfd.send(str(l))
  time.sleep(.1)
  sockfd.send(str(e))
  time.sleep(.1)
  #sockfd.send(WAHAB_ACK)
  return sockfd
    
def handleOther(sock, uList, mList, sList, m, p, l, e):
  print "Client went offline"
  removeClient(sock,uList,mList,sList)
  sock.close()
  return sock
                
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
  sk = sctp.sctpsocket_tcp(socket.AF_INET)
  sk.bind((socket.gethostname(), port))
  q = sctp.sctpsocket_udp(socket.AF_INET)
  q.bind((socket.gethostname(), port+1))
  
  print("Using l=" + str(l) + ' e=' + str(e) + ' p=' + str(p) + ' m=' + str(m) + 
        "\ns on %s" % str(s.getsockname()) + " u on %s" % str(u.getsockname()) + 
        "\nmr on %s" % str(mr.getsockname()) + ' sk on %s' % str(sk.getsockname()) +
        "\nq on %s" % str(q.getsockname()))
  
  uList=[]
  mList=[]
  sList=[]
  signal.signal(signal.SIGINT, lambda signum,frame: printConnected(uList, mList, sList))#ctrl-c
  signal.signal(signal.SIGQUIT, lambda signum,frame: close([s,u,mr,ms,sk,q]))#ctrl-\
  socket_list = [sys.stdin, s, u, mr, sk, q]
  while True:
    try:
      read_sockets,_w,_e = select.select(socket_list,[],[])
      for sock in read_sockets:
        if sock == s:
          sockfd, _addr = s.accept()
          username = sockfd.recv(1024)
          sockfd.settimeout(2)
          try: #TCP self buffers, and usually appends the 0 or 1 on username. Catch that case here
            clientType = int(sockfd.recv(1))
          except:
            clientType = int(username[-1])
            username = username[0:-1]
          sockfd.settimeout(None)
          socket_list.append(handleNewClient(sockfd, clientType, username, mList, uList, sList, m, p, l, e))
        elif sock == u:
          data,address = u.recvfrom(1024)
          handleClientMessage(data,address, u,m, p, l, e, uList, mList, sList, ms)
        elif sock == mr:
          data,address = mr.recvfrom(1024)#note was u in a3
          handleClientMessage(data,address, mr, m, p, l, e, uList, mList, sList, ms)
        elif sock == q:
          address,_flags,data,_notif = q.sctp_recv(1024)
          handleClientMessage(data,address, q, m, p, l, e, uList, mList, sList, ms)
        elif sock == sk:
          sockfd, _addr = s.accept()
          _fromaddr,_flags,username,_notif = sockfd.sctp_recv(1024)
          socket_list.append(handleNewClient(sockfd, 2, username, mList, uList, sList, m, p, l, e))
        elif sock == sys.stdin:
          if sys.stdin.readline() == 'exit':
            close([s,u,mr,ms,sk])
        else:
          socket_list.remove(handleOther(sock, uList, mList, sList, m, p, l, e))
    except (select.error, socket.error) as ex:
      #Ctrl-c perhaps, just pass
      if ex[0] == 4:#catch interrupted system call, do nothing
        continue
      else:
        raise

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print('No port given as argument 1, defaulting to ' + str(DEFAULT_PORT))
    port=DEFAULT_PORT
  else:
    port=int(sys.argv[1])
  startServer(port)
