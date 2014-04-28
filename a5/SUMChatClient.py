#!/bin/python
import getpass, sctp, select, signal, socket, struct, sys, time

DEFAULT_HOST=socket.gethostname()
DEFAULT_PORT=10009
DEFAULT_TYPE='u'

def startMulticastReceiver(group, port):
  ur = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  ur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  ur.bind((group, port))
  mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
  ur.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  
  us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  us.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
  return (ur,us)

def createU(sockname):
  u=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  u.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#shouldn't be necessary but if same host it binds over the server soooo
  u.bind(sockname)
  return u

def handleFromServer(u, e, l):
  (data, address) = u.recvfrom(1024)
  if data != str(e) and data != str(l):
    print(str(address) + ": " + data)
  else:
    print('Remote received: ' + data)
  
def handleFromStdin(s, us, e, p, host, socketList):
  msg = sys.stdin.readline()
  if msg != '':
    us.sendto(msg, (host,p))
  else:
    close(s, us, e, p, host, socketList)
  
def close(s, u, e, p, host, socketList):
  print('No chars or ctrl-d pressed, quitting')
  u.sendto(str(e),(host,p))
  [s.close() for s in socketList]
  sys.exit(0)

def mcastClient(s, host, port, u):
  s.send('0') # sends "0" & receives M, P, L and E.
  m = s.recv(32).strip()
  p = int(s.recv(5))
  l = int(s.recv(7))
  e = int(s.recv(7))
  
  (ur,us) = startMulticastReceiver(m, p)
  print('Connected with m=' + m + ' p=' + str(p) + ' l='+ str(l) + ' e=' + str(e) + ' bound to ' + str(u.getsockname()))
  signal.signal(signal.SIGINT, lambda signum,frame: u.sendto(str(l),(host,p)))#ctrl-c
  signal.signal(signal.SIGQUIT, lambda signum,frame: close(s, us, e, p, host, [s,u,ur,us]))#ctrl-/
  socket_list = [sys.stdin, ur, u]
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
        elif sock == u:
          handleFromServer(u, e, l)
        elif sock == sys.stdin:
          handleFromStdin(s, u, e, p, host, [s,u,ur,us])
    except select.error  as ex:
      if ex[0] == 4:#catch interrupted system call, do nothing
        continue
      else:
        raise

def unicastClient(s, host, u):
  s.send('1') # sends "1" & receives P, L and E.
  p = int(s.recv(5))
  l = int(s.recv(7))
  e = int(s.recv(7))
  
  print('Connected with p=' + str(p) + ' l='+ str(l) + ' e=' + str(e) + ' bound to ' + str(u.getsockname()))
  
  signal.signal(signal.SIGINT, lambda signum,frame: u.sendto(str(l),(host,p)))#ctrl-c
  signal.signal(signal.SIGQUIT, lambda signum,frame: close(s, u, e, p, host, [s,u]))#ctrl-/
  socket_list = [sys.stdin, u]
  while True:
    try:
      read_sockets, _w, _e = select.select(socket_list , [], [])
      for sock in read_sockets:
        if sock == u:
          handleFromServer(u, e, l)
        elif sock == sys.stdin:
          handleFromStdin(s, u, e, p, host, [s,u])
    except select.error  as ex:
      if ex[0] == 4:#catch interrupted system call, do nothing
        continue
      else:
        raise

def sctpClient(host, port):
  s = sctp.sctpsocket_tcp(socket.AF_INET)
  s.connect((host, port))
  s.send(getpass.getuser()) # send username
    
  p = int(s.recv(5))
  l = int(s.recv(7))
  e = int(s.recv(7))
  
  print('Connected with p=' + str(p) + ' l='+ str(l) + ' e=' + str(e) + ' bound to ' + str(u.getsockname()))
  
  signal.signal(signal.SIGINT, lambda signum,frame: u.sendto(str(l),(host,p)))#ctrl-c
  signal.signal(signal.SIGQUIT, lambda signum,frame: close(s, u, e, p, host, [s,u]))#ctrl-/
  socket_list = [sys.stdin, u]
  while True:
    try:
      read_sockets, _w, _e = select.select(socket_list , [], [])
      for sock in read_sockets:
        if sock == u:
          handleFromServer(u, e, l)
        elif sock == sys.stdin:
          handleFromStdin(s, u, e, p, host, [s,u])
    except select.error  as ex:
      if ex[0] == 4:#catch interrupted system call, do nothing
        continue
      else:
        raise

def startClient(host,port,socketType):
  if socketType == 's':
    sctpClient(host, port)
  else:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(getpass.getuser()) # send username
    time.sleep(1)
    u=createU(s.getsockname())
    if socketType == 'm':
      mcastClient(s, host, port, u)
    elif socketType == 'u':
      unicastClient(s, host, u)
    else:
      print('Unknown socket type: ' + socketType)

if __name__ == "__main__":
  if len(sys.argv) != 4:
    print('Usage: ./UMChatClient <host e.g. ' + DEFAULT_HOST + '> <port e.g. ' + 
          str(DEFAULT_PORT) + '> <type e.g. ' + DEFAULT_TYPE + '> (examples are used as defaults)')
    host=DEFAULT_HOST
    port=DEFAULT_PORT
    socketType=DEFAULT_TYPE
  else:
    host=sys.argv[1]
    port=int(sys.argv[2])
    socketType=sys.argv[3]
  startClient(host,port,socketType)
