#!/bin/python
import select, signal, socket, sys
from random import randint

DEFAULT_PORT=10009

def generateMulticastGroupPort():
  return randint(9999,11001)

def generateMulticastGroupIP():
  return str(randint(224,239)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255)) + '.' + str(randint(0,255))

def getServerSocket(port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((socket.gethostname(), port))
  print('Bound socket to host: ' + socket.gethostname() + ' on port: ' + str(port))
  s.listen(5)
  return s

#Send ip/port to all connected (keepalive response)
def sendMulticastInfo(s,multicastGroupPort,multicastGroupIP):
  try:
    s.sendall(multicastGroupIP + '|' + str(multicastGroupPort))
  except socket.error, e:
    pass

def printConnected(connected):
  if len(connected) > 0:
    print('Clients connected:')
    for value in connected:
      print(value)
  else:
    print('No clients connected!')

def startServer(port):
  s=getServerSocket(port)
  multicastGroupPort=generateMulticastGroupPort()
  multicastGroupIP=generateMulticastGroupIP()
  connected=[]
  signal_handler = lambda signum,frame: printConnected(connected)
  signal.signal(signal.SIGINT, signal_handler)
  
  connectionList=[s]
  while True:
    try:
      read_sockets,write_sockets,error_sockets = select.select(connectionList,[],[])
      for sock in read_sockets:
        #New connection
        if sock == s:
            # Handle the case in which there is a new connection recieved through server_socket
            sockfd, addr = s.accept()
            connectionList.append(sockfd)
            print "Client (%s, %s) connected" % addr
            connected.append(str(sockfd.getpeername()))
            sendMulticastInfo(sockfd,multicastGroupPort,multicastGroupIP)
        #Some incoming message from a client
        else:
            # Data received from client, process it
            try:
                #In Windows, sometimes when a TCP program closes abruptly,
                # a "Connection reset by peer" exception will be thrown
                data = sock.recv(1024) #doesn't block
                if data is None or data == '':
                  print "Client (%s, %s) disconnected" % sock.getpeername()
                  connected.remove(str(sock.getpeername()))
                  connectionList.remove(sock)
                  sock.close()
            except:
                print "Client (%s, %s) is offline" % sock.getpeername()
                connected.remove(sock.getpeername())
                sock.close()
                connectionList.remove(sock)
                continue
    except:
      #Ctrl-c perhaps, just pass
      pass

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print('No port given as argument 1, defaulting to ' + str(DEFAULT_PORT))
    port=DEFAULT_PORT
  else:
    port=sys.argv[1]
  startServer(port)
