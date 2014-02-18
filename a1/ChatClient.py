#!/bin/python
import select,socket,struct,sys,traceback

DEFAULT_HOST=socket.gethostname()
DEFAULT_PORT=10009

def getClientSocket(host,port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))
  return s

def startMulticastReceiver(group, port):
  recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  recv_sock.bind(('', port))
  mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
  recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  
  send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
  return (recv_sock,send_sock)

def startClient(host,port):
  s = getClientSocket(host,port)
  recv_sock = None
  send_sock = None
  mcast_group = None
  mcast_port = None
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
          if '|' in data and recv_sock is None:
            mcast_group, mcast_port_str = data.split('|')
            mcast_port = int(mcast_port_str)
            print('Received multicast group info ip: ' + mcast_group + ' port: ' + mcast_port_str)
            try:
              recv_sock,send_sock = startMulticastReceiver(mcast_group, mcast_port)
              socket_list.append(recv_sock)
            except:
              print('Error connecting to multicast group')
              traceback.print_exc()
              sys.exit()
      elif sock == sys.stdin:
        msg = sys.stdin.readline()
        if msg != '':
          send_sock.sendto(str(s.getsockname()) + ': ' + msg, (mcast_group, mcast_port))
        else:
          print('No chars or ctrl-d pressed, quitting')
          sys.exit()
      elif sock == recv_sock:
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
    port=int(sys.argv[2])
  startClient(host,port)
