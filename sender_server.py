#!/usr/bin/env python
#pisender side server

import socket
import cv2
from threading import Thread, Lock
import struct

debug = True
jpeg_quality = 40
host = '192.168.0.103'
port = 1080

class VideoGrabber(Thread):
        def __init__(self, jpeg_quality):
            Thread.__init__(self)
            self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
            self.cap = cv2.VideoCapture(0)
            self.cap.set(3, 640)
            self.cap.set(4, 480)
            self.running = True
            self.buffer = None
            self.lock = Lock()

        def stop(self):
            self.running = False

        def get_buffer(self):

            if self.buffer is not None:
                    self.lock.acquire()
                    cpy = self.buffer.copy()
                    self.lock.release()
                    return cpy

        def run(self):
            while self.running:
                success, img = self.cap.read()
                if not success:
                        continue
                self.lock.acquire()
                result, self.buffer = cv2.imencode('.jpg', img, self.encode_param)
                self.lock.release()

grabber = VideoGrabber(jpeg_quality)
grabber.daemon = True
grabber.start()

running = True

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = (host, port)

print('starting up on %s port %s\n' % server_address)

sock.bind(server_address)
while running:
    data_packed, address = sock.recvfrom(struct.calcsize('<L'))
    data = struct.unpack('<L',data_packed)[0]
    if(data == 1):
            buffer = grabber.get_buffer()
            if buffer is None:
                    continue
            if len(buffer) > 65507:
                print "too large sorry"
                sock.sendto(struct.pack('<L',struct.calcsize('<L')), address)
                sock.sendto(struct.pack('L',404), address) #capture error
                continue
            sock.sendto(struct.pack('<L',len(buffer)), address)
            sock.sendto(buffer.tobytes(), address)
    elif(data == 0):
            grabber.stop()
            running = False

print("Quitting..")
grabber.join()
sock.close()
