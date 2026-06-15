import subprocess, time

def measure_foreground_latency(cmd=['sleep','0.5']):
    t0 = time.time()
    p = subprocess.Popen(cmd)
    p.wait()
    return time.time() - t0

if __name__ == '__main__':
    base = measure_foreground_latency(['sleep','0.1'])
    print('Foreground latency baseline:', base)
    print('Now run daemon in another terminal and re-measure.')
