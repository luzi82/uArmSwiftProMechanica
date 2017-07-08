import subprocess
import os
import re
import threading
import copy
import sys
import time
import numpy as np
import cv2

BUFFER_COUNT = 3

class VideoCapture:

    def __init__(self,src_name,width,height):
        self.src_name = src_name
        self.width = width
        self.height = height
        self.lock = threading.Lock()
        self.read_lock = None
        self.write_lock = None
        self.next_frame_idx = 1
        self.timestamp_list = [0] * BUFFER_COUNT
        self.closing = False
        self.data_ready = False
    
    def init(self):
        self.ffmpeg_exec_path = self._ffmpeg_exec_path()
        self.device_id = self._find_device_id()
        self.buffer = [ bytearray(self.width*self.height*4) for _ in range(BUFFER_COUNT) ]

    def start(self):
        self.thread = threading.Thread( target=self._run )
        self.thread.start()

    def wait_data_ready(self):
        while(True):
            with self.lock:
                if self.data_ready:
                    return
                time.sleep(0.1)

    def close(self):
        self.closing = True
        if self.proc:
            self.proc.wait()

    def get_frame(self):
        return self._get_read_buf()

    def release_frame(self):
        self._release_read_buf()

    def _run(self):
        self.proc = subprocess.Popen([
                self.ffmpeg_exec_path,
                '-nostdin',
                '-f','avfoundation',
                '-pixel_format','uyvy422',
                '-i','{}:none'.format(self.device_id),
                '-vsync','2',
                '-an',
                '-vf','scale={}:{}'.format(self.width,self.height),
                '-pix_fmt','bgr0',
                '-f','rawvideo',
                '-'
            ],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.PIPE
        )
        while (not self.closing):
            buf = self._get_write_buf()
            llen = self.proc.stdout.readinto(buf)
            if llen!=len(buf):
                print(llen,file=sys.stderr)
                assert(False)
            self._release_write_buf()
            with self.lock:
                self.data_ready = True
        #print('terminate',file=sys.stderr)
        self.proc.terminate()
        timeout = time.time() + 5
        while(time.time()<timeout):
            if self.proc.returncode != None:
                return
            time.sleep(0.1)
        #print('kill',file=sys.stderr)
        self.proc.kill()

    def _get_write_buf(self):
        with self.lock:
            assert(self.write_lock == None)
            tmp_timestamp_list = copy.copy(self.timestamp_list)
            if self.read_lock != None:
                tmp_timestamp_list[self.read_lock] = sys.float_info.max
            idx = tmp_timestamp_list.index(min(tmp_timestamp_list))
            self.write_lock = idx
            self.timestamp_list[idx] = self.next_frame_idx
            self.next_frame_idx += 1
            return self.buffer[idx]

    def _release_write_buf(self):
        with self.lock:
            assert(self.write_lock != None)
            self.write_lock = None

    def _get_read_buf(self):
        with self.lock:
            assert(self.read_lock == None)
            tmp_timestamp_list = copy.copy(self.timestamp_list)
            if self.write_lock != None:
                tmp_timestamp_list[self.write_lock] = 0
            idx = tmp_timestamp_list.index(max(tmp_timestamp_list))
            self.read_lock = idx
            return self.buffer[idx]

    def _release_read_buf(self):
        with self.lock:
            assert(self.read_lock != None)
            self.read_lock = None

    def _ffmpeg_exec_path(self):
        path = __file__
        path = os.path.realpath(path)
        path = os.path.dirname(path)
        path = os.path.join(path,'external','ffmpeg','ffmpeg')
        assert(os.path.isfile(path))
        return path

    def _find_device_id(self):
        test_run = subprocess.run([
            self.ffmpeg_exec_path,
            '-f','avfoundation',
            '-list_devices','true',
            '-i',''
            ],
            stderr=subprocess.PIPE
        )
        stderr_str = test_run.stderr.decode('UTF8')
        stderr_line_list = stderr_str.split('\n')
        src_list = []
        for line in stderr_line_list:
            regex = '\\[v\\] \\[(\d+)\\] \\[([^\\]]+)\\]'
            m = re.search(regex, line)
            if m == None:
                continue
            src_list.append(m.group(2))
            if m.group(2) == self.src_name:
                return int(m.group(1))
        raise Exception('src \"{}\" not found, available src:{}'.format(self.src_name,src_list))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='video capture')
    parser.add_argument('src_name', help='src_name')
    parser.add_argument('width', type=int, help='width')
    parser.add_argument('height', type=int, help='height')
    args = parser.parse_args()

    vc = VideoCapture(args.src_name,args.width,args.height)
    vc.init()
    vc.start()
    vc.wait_data_ready()
    print('data_ready')
    for i in range(10):
        print('get_frame')
        buf = vc.get_frame()
        ndata = np.frombuffer(buf, np.uint8)
        vc.release_frame()
        print(ndata.shape)
        ndata = np.reshape(ndata, (args.height, args.width, 4) )
        cv2.imwrite('x{}.png'.format(i),ndata)
        time.sleep(1)
    vc.close()