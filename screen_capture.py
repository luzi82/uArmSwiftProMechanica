import subprocess

def get_windowid():
    p = subprocess.run(['osascript','-e','tell app "QuickTime Player" to id of window 1'],stdout=subprocess.PIPE)
    assert(p.returncode == 0)
    return p.stdout.decode('ascii').strip()

def screencapture(windowid,filename):
    p = subprocess.run(['screencapture','-x','-l',str(windowid),'-o',filename])
    assert(p.returncode == 0)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='screen capture')
    parser.add_argument('filename', nargs='?', help='filename')
    args = parser.parse_args()

    windowid = get_windowid()
    screencapture(windowid,args.filename)
