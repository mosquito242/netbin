import socket
from multiprocessing.pool import Pool
import netbin_host
import netbin_client
import sys
import netifaces
import re
import constants
from thread import *
from util import *


def send_is_host_query(subnet, sock, m_range):
	for i in m_range:
		try:
			sock.sendto("ISHOST?", (subnet+str(i), constants.HOST_LISTEN_PORT))
		except socket.error as serr:
			printDebug("Socket Error No " + str(serr.errno) +":" + subnet+str(i), "i")


	
def main():	
	lNodes = {}
	pAddress = []
	my_ip = ""
	##FIND THE SUBNET MASK
	subnet = ""
	netArray = [ x for x in netifaces.interfaces() if x.startswith('en') ]
	#if not enArray: enArray = [ x for x in netifaces.interfaces() if x.startswith('eth') ]

	if not netArray:
		netArray = netifaces.interfaces()
		
	for en in netArray:
		printDebug(str(netifaces.ifaddresses(en).keys()), "i")
		bcTuple = netifaces.ifaddresses(en)
		if (2 in bcTuple):
			printDebug(str(bcTuple[2]), "i")
			if ('broadcast' in bcTuple[2][0]):
				subnet = re.match("^\d+.\d+.[^.]", bcTuple[2][0]['broadcast']).group(0)+'.'
				my_ip = bcTuple[2][0]['addr']
				break

	## IF NO SUBNET FOUND, TERMINATE
	if(subnet == ""):
		print "Could not find subnet mask for LAN - please check your network settings"
		sys.exit()



	pAddress.extend(range(1, 255))
	chunk_size = len(pAddress)/16
	address_groups = [pAddress[i:i+chunk_size] for i in range(0, len(pAddress), chunk_size)]

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	sock.bind((my_ip,constants.COMMUNICATE_PORT))

	for li in address_groups:
		start_new_thread(send_is_host_query, (subnet, sock, li, ))

	sock.settimeout(2.5)
	while 1:
		try:
			result, addr = sock.recvfrom(1024)
			if result == "IAMHOST":
				sock.sendto("ACK", addr)
				hostAddr = addr[0]
				break
			else:
				hostAddr = ""
		except socket.error:
			hostAddr = ""
			break

	sock.close()


	if hostAddr: 
		## empty strings falsify
		## another node is already host
		netbin_client.start(hostAddr, constants.HOST_PORT)

	else:
		if my_ip == "":
			print "Tried to initialize a host process, but could not find device's LAN IP."
			print "Please restart netbin."
			sys.exit()
		netbin_host.start(constants.HOST_PORT, my_ip)

if __name__ == '__main__':
    main()


