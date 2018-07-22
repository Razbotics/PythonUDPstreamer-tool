#!/usr/bin/env python
# pi receiver side

import socket
import cv2
import numpy as np
import struct
from threading import Thread, Lock

class ImageGrabber(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)
        self.lock = Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (host, port)
        self.sock.settimeout(0.2)
        self.array = None
        self.running = True

    def stopServer(self):
        self.sock.sendto(struct.pack('<L',0), self.server_address)

    def imageGrabber(self):
        if self.array is not None:
            self.lock.acquire()
            array = self.array
            self.lock.release()
            return array

    def run(self):
        while self.running:
            try:
                self.sock.sendto(struct.pack('<L',1), self.server_address)
                try:
                    data_len_packed, server = self.sock.recvfrom(struct.calcsize('<L'))
                except socket.timeout:
                    continue
                data_len = struct.unpack('<L',data_len_packed)[0]
                if data_len < 65507:
                    print "byte recv: ", data_len
                try:
                    data, server = self.sock.recvfrom(data_len)
                except socket.timeout:
                    continue
                except Exception:
                    continue
                if not len(data) == data_len:
                    print "There was a image packet loss..."
                    continue
                if data == 404:
                    continue
                self.lock.acquire()
                self.array = np.frombuffer(data, dtype=np.dtype('uint8'))
                self.lock.release()

            except:
                self.running = False
                self.lock.acquire()
                self.image = None
                self.lock.release()

if __name__ == '__main__':
    image = ImageGrabber('192.168.0.103', 1080)
    image.daemon = True
    image.start()
    try:
        while image.running:
            array = image.imageGrabber()
            if array is None:
                continue
            img = cv2.imdecode(array, 1)
            ## Do some Processing here
            #
            #
            #
            try:
                cv2.imshow("Image", img)
            except Exception:
                continue
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except:
        image.stopServer()
        image.sock.close()
