#!/usr/bin/env python3
"""Mac + OrbStack local proxy to a previously paired iPhone over Tailscale.
Failure handling: offline/wrong peer, stale discovery profile, changed control
port, occupied VM ports, lost parent, Ctrl-C and timeout. No router operations.
"""
import argparse,fcntl,ipaddress,json,os,re,selectors,signal,socket,struct,subprocess,sys,tempfile,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent
IMAGE='ghcr.io/open-webui/open-webui:main'
def say(s):print(time.strftime('[%H:%M:%S] ')+s,flush=True)
def run(cmd,timeout=15):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,start_new_session=True)
 if p.returncode:raise RuntimeError((p.stderr or p.stdout).strip())
 return p.stdout

def check(ip,port):
 try:
  with socket.create_connection((ip,port),2) as s:
   s.settimeout(2)
   msg={'message':{'plain':{'_0':{'request':{'_0':{'handshake':{'_0':{'hostOptions':{'attemptPairVerify':True},'wireProtocolVersion':26}}}}}}},'originatedBy':'host','sequenceNumber':0}
   b=json.dumps(msg).encode();s.sendall(b'RPPairing'+struct.pack('>H',len(b))+b)
   return s.recv(11).startswith(b'RPPairing')
 except OSError:return False

# Publisher child holds dns-sd and stops it on parent pipe EOF, even after SIGKILL.
PUBLISHER='''import subprocess,sys,json,signal
signal.signal(signal.SIGINT,signal.SIG_IGN)
p=subprocess.Popen(json.loads(sys.argv[1]),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 while sys.stdin.buffer.read(1):pass
finally:
 p.terminate()
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:p.kill();p.wait()
'''
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('ip',nargs='?');ap.add_argument('--port',type=int);ap.add_argument('--duration',type=int,default=0);a=ap.parse_args()
 ip=str(ipaddress.IPv4Address(a.ip or input('请输入 iPhone 的 Tailscale IP（100.x）：').strip()))
 if ipaddress.ip_address(ip) not in ipaddress.ip_network('100.64.0.0/10'):raise RuntimeError('请输入手机的 Tailscale IPv4 地址')
 lock=open(Path(tempfile.gettempdir())/'iphone-tailscale-debug.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 status=json.loads(run(['tailscale','status','--json']))
 if not any(ip in p.get('TailscaleIPs',[]) and p.get('OS')=='iOS' for p in status.get('Peer',{}).values()):raise RuntimeError('该 IP 不是当前 tailnet 的 iOS 节点')
 profile=json.loads((ROOT/'iphone-profile.json').read_text());port=a.port or int(profile['port'])
 if not 1<=port<=65535 or not check(ip,port):raise RuntimeError('手机调试端口不可达或已变化。解锁手机重试；可用 --port 指定新端口。原路由器版仍可使用。')
 image=json.loads(run(['docker','image','inspect',IMAGE]))[0]['Id']
 # Read the existing OrbStack VM address without changing its networking.
 info=run(['docker','run','--rm','--network','host','--no-healthcheck','--entrypoint','python3',image,'-c',"import socket,sys; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect((sys.argv[1],59123)); print(s.getsockname()[0])",ip])
 vm=info.strip();ipaddress.IPv4Address(vm)
 route=run(['/sbin/route','-n','get',vm]);m=re.search(r'interface:\s*(bridge\d+)',route)
 if not m:raise RuntimeError('OrbStack 虚拟机没有可用的本地 bridge 路径')
 iface=m.group(1);net=run(['/sbin/ifconfig',iface]);host=re.search(r'\binet (\d+\.\d+\.\d+\.\d+)',net).group(1)
 name='iphone-ts-debug-'+uuid.uuid4().hex[:10];proxy=None;pub=None;stopped=False;report={'ip':ip,'vm':vm,'interface':iface,'container':name,'router_access':False}
 def end(*_):
  nonlocal stopped
  stopped=True
 signal.signal(signal.SIGINT,end);signal.signal(signal.SIGTERM,end)
 try:
  say(f'Mac → 本机 OrbStack {vm} → iPhone Tailscale {ip}:{port}')
  say('无需路由器服务；请保持手机解锁及开发者模式。Ctrl-C 停止并断开代理连接。')
  cmd=['docker','run','--rm','-i','--network','host','--no-healthcheck','--ulimit','nofile=65536:65536','--name',name,'-v',str(ROOT/'proxy.py')+':/proxy.py:ro','--entrypoint','python3',image,'-u','/proxy.py',ip,str(port),vm,host]
  proxy=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
  sel=selectors.DefaultSelector();sel.register(proxy.stdout,selectors.EVENT_READ)
  deadline=time.monotonic()+30;ready=False
  while time.monotonic()<deadline and not stopped:
   if sel.select(.5):
    line=proxy.stdout.readline().strip()
    if line.startswith('READY'):ready=True;break
    if line:say(line)
    if proxy.poll() is not None:break
  sel.close()
  if not ready:raise RuntimeError('本地代理启动失败或超时')
  cmd=['dns-sd','-i',iface,'-P',profile['name'],'_remotepairing._tcp','local.','49000','iphone-ts-vm.local.',vm,*profile['txt']]
  pub=subprocess.Popen([sys.executable,'-c',PUBLISHER,json.dumps(cmd)],stdin=subprocess.PIPE,start_new_session=True)
  started=time.monotonic();last=0
  say('已发布调试服务。现在可在 Xcode 选择原来的 lyd-iPhone。')
  while not stopped and (not a.duration or time.monotonic()-started<a.duration):
   if proxy.poll() is not None or pub.poll() is not None:raise RuntimeError('代理或 Bonjour 子进程退出')
   if time.monotonic()-last>5:proxy.stdin.write('h\n');proxy.stdin.flush();last=time.monotonic()
   time.sleep(.2)
 finally:
  say('正在停止临时服务……')
  if pub:
   pub.stdin.close()
   try:pub.wait(timeout=5)
   except subprocess.TimeoutExpired:pub.kill();pub.wait()
  if proxy:
   try:proxy.stdin.close()
   except BrokenPipeError:pass
   try:proxy.wait(timeout=8)
   except subprocess.TimeoutExpired:
    run(['docker','stop','-t','3',name],10)
    proxy.wait(timeout=5)
   if proxy.stdout:proxy.stdout.close()
  remaining=run(['docker','ps','-a','--filter','name=^/'+name+'$','--format','{{.ID}}'])
  report['cleaned']=not remaining.strip();(ROOT/'last-run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  if remaining.strip():raise RuntimeError('容器仍存在，请检查 '+name)
  say('已确认：本次容器、代理连接和 Bonjour 发布已清理。')
if __name__=='__main__':
 try:main()
 except (Exception,KeyboardInterrupt) as e:print('错误：'+str(e),file=sys.stderr);sys.exit(1)
