#!/bin/python
import select, signal, socket, struct, sys, time
from random import randint

DEFAULT_PORT=10009

def generateMulticastGroupPort():
  return randint(10000,11001)

def generateMulticastGroupIP():
  return str(randint(224,239)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255))

def generateNumber():
  return randint(1000000,9999999)

def getConnectedString(connected):
  s=''
  for socket in connected.items():
    for user,address in socket.getpeername():
      s += 'User: ' + user + ' address: ' + str(address) + '\n'
  return s

def getConnectedString(uList, mList):
  s  = 'Connected UDP clients:\n'
  s += getConnectedString(uList)
  s += 'Connected MCast clients:\n'
  s += getConnectedString(mList)
  return s

def printConnected(uList, mList):
  print(getConnectedString(uList, mList))

def close(s,u):
  s.close()
  u.close()

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
  if s in u:
    del u[s]
  if s in m:
    del m[s]

def handleClientMessage(s, l, e, uList, mList):
  (data,address) = s.recvfrom(1024)
  try:
    dataNumber = int(data)
    if dataNumber == l:
      print('Received l, sending list to connection')
      s.send(getConnectedString(uList, mList))
    elif dataNumber == e:
      print('Received e, goodbye person!')
      removeClient(s,uList,mList)
  except:
    print(str(address) + ': ' + data)
    return (True,data)
  return (False,0)

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
        " on %s" % str(socket.gethostname()))
  
  uList={}
  mList={}
  signal.signal(signal.SIGINT, lambda signum,frame: printConnected(uList, mList))
  socket_list = [sys.stdin, s, u, mr]
  while True:
    try:
      read_sockets,_w,_e = select.select(socket_list,[],[])
      for sock in read_sockets:
        #New connection
        if sock == s:
            # Handle the case in which there is a new connection received through server_socket
            sockfd, _addr = s.accept()
            username = sockfd.recv(1024)
            sockfd.settimeout(2)
            try: #TCP self buffers, and usually appends the 0 or 1 on username. Catch that case here
              clientType = sockfd.recv(1)
            except:
              clientType = int(username[-1])
              username = username[0:-1]
            sockfd.settimeout(None)
            if clientType == '0':
              print('New MC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
              uList[sockfd] = username
              sockfd.send(str(m))
              time.sleep(1)
            else:
              print('New UC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
              mList[sockfd] = username
            sockfd.send(str(p))
            time.sleep(1)
            sockfd.send(str(l))
            time.sleep(1)
            sockfd.send(str(e))
            time.sleep(1)
            socket_list.append(sockfd)
        elif sock == u:#received unicast, send to multicast
            data = handleClientMessage(sock, l, e, uList, mList)
            if(data[0]):
              ms.sendto(data, (m,p))
        elif sock == mr:#received multicast, send to each unicast client
            data = handleClientMessage(sock, l, e, uList, mList)
            if(data[0]):
              [uClient.sendto(data) for uClient in uList]
        else:
            # Data received from client, process it
            try:
                #In Windows, sometimes when a TCP program closes abruptly,
                # a "Connection reset by peer" exception will be thrown
                data = sock.recv(1024) #doesn't block
                if data is None or data == '':
                  print "Client (%s, %s) disconnected" % sock.getpeername()
                  removeClient(sock,uList,mList)
                  sock.close()
                  socket_list.remove(sock)
                else:
                  print('Received unhandled message: ' + data)
            except:
                print "Client (%s, %s) is offline" % sock.getpeername()
                removeClient(sock,uList,mList)
                sock.close()
                socket_list.remove(sock)
    except:
      #Ctrl-c perhaps, just pass
      pass

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print('No port given as argument 1, defaulting to ' + str(DEFAULT_PORT))
    port=DEFAULT_PORT
  else:
    port=int(sys.argv[1])
  startServer(port)
