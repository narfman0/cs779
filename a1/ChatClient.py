#!/bin/python
import select,socket,sys,traceback

DEFAULT_HOST=socket.gethostname()
DEFAULT_PORT=10009

def getClientSocket(host,port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))
  return s

def startMulticastReceiver(group, port):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  s.seckopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
  socket_list = [sys.stdin, s]
  while True:
    read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
    for sock in read_sockets:
      #incoming message from remote server
      if sock == s:
        data = sock.recv(1024)
        if not data :
          print 'Disconnected from server'
          sock.close()
          sys.exit()
        else :
          #print data
          if '|' in data and receiverSocket is None:
            ip,port=data.split('|')
            print('Received multicast group info ip: ' + ip + ' port: ' + port)
            try:
              receiverSocket = startMulticastReceiver(ip,int(port))
              socket_list.append(receiverSocket)
            except:
              print('Error connecting to multicast group')
              traceback.print_exc()
              sys.exit()
      #user entered a message
      elif sock == sys.stdin:
        msg = sys.stdin.readline()
        if receiverSocket != None:
          receiverSocket.send(msg)
        else:
          print('Multicast socket null, reconnect!')
      elif sock == receiverSocket:
        data = sock.recv(1024)
        if not data or data == '':
          sock.close()
          print('Error, data null or empty, disconnected from multicast group')
          sys.exit()
        else:
          print(data) 

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