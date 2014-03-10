#!/bin/python
import select, signal, socket, sys, time
from random import randint

DEFAULT_PORT=10009

def generateMulticastGroupPort():
  return randint(10000,11001)

def generateMulticastGroupIP():
  return str(randint(224,239)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255))

def generateNumber():
  return randint(1000000,9999999)

def printConnected(connected):
  print('Connected clients:')
  for user,address in connected.items():
    print('User: ' + user + ' address: ' + str(address))

def close(s,u):
  s.close()
  u.close()

def removeClient(s,u,m):
  try:
    del u[s.getpeername()]
  except:
    pass
  try:
    del m[s.getpeername()]
  except:
    pass

def startServer(port):
  l=generateNumber()
  e=generateNumber()
  p=generateMulticastGroupPort()
  m=generateMulticastGroupIP()
  print "Using l=" + str(l) + ' e=' + str(e) + ' p=' + str(p) + ' m=' + str(m)
  
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((socket.gethostname(), port))
  s.listen(1)
  u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  u.bind((socket.gethostname(), p))
  print "Bound to %s" % str(socket.gethostname())
  
  uList={}
  mList={}
  signal.signal(signal.SIGINT, lambda signum,frame: printConnected(uList, mList))
  socket_list = [sys.stdin, s, u]
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
              uList[sockfd.getpeername()] = username
              sockfd.send(str(m))
              time.sleep(1)
            else:
              print('New UC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
              mList[sockfd.getpeername()] = username
            sockfd.send(str(p))
            time.sleep(1)
            sockfd.send(str(l))
            time.sleep(1)
            sockfd.send(str(e))
            time.sleep(1)
            socket_list.append(sockfd)
        elif sock == u:
            (data,address) = u.recvfrom(1024)
            try:
              dataNumber = int(data)
              if dataNumber == l:
                print('Received l, sending list to connection')
                sock.send('Unicast: ' + str(uList) + 
                          'Multicast: ' + str(mList))
              if dataNumber == e:
                print('Received e, goodbye person!')
                removeClient(sock,uList,mList)
            except:
              pass
            print(str(address) + ': ' + data)
        #Some incoming message from a client
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
