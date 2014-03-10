#!/bin/python
import getpass, os, select, signal, socket, struct, sys, time, traceback

DEFAULT_HOST=socket.gethostname()
DEFAULT_PORT=10009
DEFAULT_TYPE='m'

def startMulticastReceiver(group, port):
  recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  recv_sock.bind(('', port))
  mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
  recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  
  send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
  return (recv_sock,send_sock)

def mcastClient(s, host, port):
  s.send('0') # sends "0" & receives M, P, L and E.
  m = s.recv(32).strip()
  p = int(s.recv(5))
  l = int(s.recv(7))
  e = int(s.recv(7))
  (ur,us) = startMulticastReceiver(m, p)
  print('Connected with m=' + m + ' p=' + str(p) + ' l='+ str(l) + ' e=' + str(e))
  
  signal.signal(signal.SIGINT, lambda signum,frame: us.sendto(str(l),(host,p)))#ctrl-c
  signal.signal(signal.SIGQUIT, lambda signum,frame: close(s, us, e, p, host))#ctrl-/
  socket_list = [sys.stdin, ur]
  while True:
    try:
      read_sockets, _w, _e = select.select(socket_list , [], [])
      for sock in read_sockets:
        if sock == ur:
          (data, address) = ur.recvfrom(1024)
          if data != str(e) and data != str(l):
            print(str(address) + ": " + data)
          else:
            print('Remote received: ' + data)
        elif sock == sys.stdin:
          msg = sys.stdin.readline()
          if msg != '':
            us.sendto(msg, (host,p))
          else:
            close(s, us, e, p, host)
    except select.error  as ex:
      if ex[0] == 4:#catch interrupted system call, do nothing
        continue
      else:
        raise
  
def close(s, u, e, p, host):
  print('No chars or ctrl-d pressed, quitting')
  u.sendto(str(e),(host,p))
  u.close()
  s.close()
  sys.exit(1)

def unicastClient(s, host):
  s.send('1') # sends "1" & receives P, L and E.
  p = int(s.recv(5))
  l = int(s.recv(7))
  e = int(s.recv(7))
  print('Connected with p=' + str(p) + ' l='+ str(l) + ' e=' + str(e))
  
  u=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  u.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#shouldn't be necessary but if same host it binds over the server soooo
  u.bind((host,p))
  signal.signal(signal.SIGINT, lambda signum,frame: u.sendto(str(l),(host,p)))#ctrl-c
  signal.signal(signal.SIGQUIT, lambda signum,frame: close(s, u, e, p, host))#ctrl-/
  socket_list = [sys.stdin, u]
  while True:
    try:
      read_sockets, _w, _e = select.select(socket_list , [], [])
      for sock in read_sockets:
        if sock == u:
          (data, address) = u.recvfrom(1024)
          if data != str(e) and data != str(l):
            print(str(address) + ": " + data)
          else:
            print('Remote received: ' + data)
        elif sock == sys.stdin:
          msg = sys.stdin.readline()
          if msg != '':
            u.sendto(msg, (host,p))
          else:
            close(s, u, e, p, host)
    except select.error  as ex:
      if ex[0] == 4:#catch interrupted system call, do nothing
        continue
      else:
        raise

def startClient(host,port,socketType):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))
  s.send(getpass.getuser()) # send username
  time.sleep(1)
  if socketType == 'm':
    mcastClient(s, host, port)
  else:
    unicastClient(s, host)

if __name__ == "__main__":
  if len(sys.argv) != 4:
    print('No <shost> given as argument 1, defaulting to ' + DEFAULT_HOST)
    print('No <sport> given as argument 2, defaulting to ' + str(DEFAULT_PORT))
    print('No <u|m> given as argument 3, defaulting to ' + DEFAULT_TYPE)
    host=DEFAULT_HOST
    port=DEFAULT_PORT
    socketType=DEFAULT_TYPE
  else:
    host=sys.argv[1]
    port=int(sys.argv[2])
    socketType=sys.argv[3]
  startClient(host,port,socketType)
