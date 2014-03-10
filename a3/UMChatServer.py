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
  
  connectedUnicast={}
  connectedMulticast={}
  signal.signal(signal.SIGINT, lambda signum,frame: printConnected(connectedUnicast,connectedMulticast))
  socket_list = [sys.stdin, s, u]
  while True:
    try:
      read_sockets,_w,_e = select.select(socket_list,[],[])
      for sock in read_sockets:
        #New connection
        if sock == s:
            # Handle the case in which there is a new connection recieved through server_socket
            sockfd, _addr = s.accept()
            username = sockfd.recv(1024)
            clientType = sockfd.recv(1)
            if clientType == '0':
              print('New MC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
              connectedUnicast[sockfd.getpeername()] = username
              sockfd.send(str(m))
              time.sleep(1)
            else:
              print('New UC Client: ' + str(sockfd.getpeername()) + '[' + username + ']')
              connectedMulticast[sockfd.getpeername()] = username
            sockfd.send(str(p))
            time.sleep(1)
            sockfd.send(str(l))
            time.sleep(1)
            sockfd.send(str(e))
            time.sleep(1)
        elif sock == u:
            (data,address) = u.recvfrom(1024)
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
                  del connectedUnicast[sock.getpeername()]
                  del connectedMulticast[sock.getpeername()]
                  sock.close()
                try:
                  dataNumber = int(data)
                  if dataNumber == l:
                    print('Received l, sending list to connection')
                    sock.send('Unicast: ' + str(connectedUnicast) + 
                              'Multicast: ' + str(connectedMulticast))
                except:
                  pass
            except:
                print "Client (%s, %s) is offline" % sock.getpeername()
                del connectedUnicast[sock.getpeername()]
                del connectedMulticast[sock.getpeername()]
                sock.close()
                continue
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
