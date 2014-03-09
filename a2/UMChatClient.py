#!/bin/python
import getpass, os, signal, socket, struct, sys, time

DEFAULT_HOST=socket.gethostname()
DEFAULT_PORT=10009
DEFAULT_TYPE='u'

def startMulticastReceiver(group, port):
  recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  recv_sock.bind(('', port))
  mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
  recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  
  send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
  return (recv_sock,send_sock)

def printSocket(host,port):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.bind((host,port))
  print('Printing messages from ' + str((host,port)))
  while True:
    try:
      (data, address) = s.recvfrom(1024)
      print(str(address) + ": " + data)
    except:
      pass
  s.close()
  sys.exit()

def mcastClient(s, host, port):
  s.send('0') # sends "0" & receives M, P, L and E.
  m = s.recv(32).strip()
  p = int(s.recv(5))
  l = int(s.recv(7))
  e = int(s.recv(7))
  print('Connected with m=' + m + ' p=' + str(p) + ' l='+ str(l) + ' e=' + str(e))
  _recv_sock, _send_sock = startMulticastReceiver(m, p)
  
def close(s, us, e, listPrinter, socketPrinter):
  print('No chars or ctrl-d pressed, quitting')
  us.close()
  s.send(str(e))
  s.close()
  os.kill(listPrinter, signal.SIGKILL)
  os.kill(socketPrinter, signal.SIGKILL)
  sys.exit()

def sigQuit(s, us, e, listPrinter, socketPrinter, p):
  us.sendto(str(e),(host,p))
  close(s, us, e, listPrinter, socketPrinter)

def printList(host, p):
  usRead=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  print('Binding to ' + str((host,p)))
  usRead.bind((host,p))
  while True:
    try:
      data = usRead.recv(1024)
      if data == '':
        break
      print('Printing LIST:\n' + data)
    except:
      pass
  usRead.close()
  sys.exit()

def unicastClient(s, host, port):
  s.send('1') # sends "1" & receives P, L and E.
  p = int(s.recv(5))
  l = int(s.recv(7))
  e = int(s.recv(7))
  s.settimeout(1)
  print('Connected with p=' + str(p) + ' l='+ str(l) + ' e=' + str(e))
  
  listPrinter=os.fork()
  if(listPrinter == 0):
    printList(host,p)
  socketPrinter=os.fork()
  if(socketPrinter == 0):
    printSocket(host, port)
 
  us=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  signal.signal(signal.SIGINT, lambda signum,frame: us.sendto(str(l),(host,p)))#ctrl-c
  signal.signal(signal.SIGQUIT, lambda signum,frame: sigQuit(s, us, e, listPrinter, socketPrinter, p))#ctrl-/
  while True:
    msg = sys.stdin.readline().strip()
    if msg != '':
      us.sendto(msg,(host,p))
    else:
      close(s, us, e, listPrinter, socketPrinter)

def startClient(host,port,socketType):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))
  s.send(getpass.getuser()) # send username
  time.sleep(1)
  if socketType == 'm':
    mcastClient(s, host, port)
  else:
    unicastClient(s, host, port)

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
