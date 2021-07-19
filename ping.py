from socket import *
import os
import sys
import struct
import time
import select
from netaddr import IPNetwork

def checksum(str):
    str = bytearray(str)
    csum = 0
    countTo = (len(str) // 2) * 2

    for count in range(0, countTo, 2):
        thisVal = str[count + 1] * 256 + str[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff

    if countTo < len(str):
        csum = csum + str[-1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

ICMP_ECHO_REQUEST = 8

def receivePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if type != 8 and packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:
            return "Request timed out."

def sendPing(mySocket, destAddr, ID):
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    myChecksum = checksum(header + data)

    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff

    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))

def OnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    mySocket = socket(AF_INET, SOCK_DGRAM, icmp)

    myID = os.getpid() & 0xFFFF
    sendPing(mySocket, destAddr, myID)
    delay = receivePing(mySocket, myID, timeout, destAddr)

    mySocket.close()
    return delay

def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + dest )
    print("")
    delay = OnePing(dest, timeout)
    print(delay)
    time.sleep(1)
    return delay

ipad = sys.argv [1]
subnet = []
for ip in IPNetwork(ipad):
    subnet.append(ip)
for ip in subnet:
    ping(str(ip))

