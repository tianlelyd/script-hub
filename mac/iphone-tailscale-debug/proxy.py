import asyncio,sys,signal,time
async def main():
 stop=asyncio.Event();loop=asyncio.get_running_loop();servers=[];jobs=set();last=time.monotonic()
 for s in (signal.SIGTERM,signal.SIGINT):loop.add_signal_handler(s,stop.set)
 def heartbeat():
  nonlocal last
  if not sys.stdin.buffer.read1(1024):stop.set();loop.remove_reader(0)
  last=time.monotonic()
 loop.add_reader(0,heartbeat)
 async def relay(r,w,p):
  t=asyncio.current_task();jobs.add(t);remote=None;tasks=[]
  try:
   if w.get_extra_info('peername')[0]!=sys.argv[4]:return
   rr,remote=await asyncio.wait_for(asyncio.open_connection(sys.argv[1],p),4)
   async def cp(a,b):
    while data:=await a.read(65536):b.write(data);await b.drain()
   tasks=[asyncio.create_task(cp(r,remote)),asyncio.create_task(cp(rr,w))]
   await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
  except (OSError,asyncio.TimeoutError):pass
  finally:
   for t2 in tasks:t2.cancel()
   await asyncio.gather(*tasks,return_exceptions=True);w.close()
   if remote:remote.close()
   jobs.discard(t)
 try:
  failed=[]
  for port in [49000,*range(49152,65536)]:
   try:servers.append(await asyncio.start_server(lambda r,w,p=port:relay(r,w,int(sys.argv[2]) if p==49000 else p),sys.argv[3],port))
   except OSError:failed.append(port)

  if failed:raise RuntimeError('Required ports occupied: '+str(failed))
  print('READY',len(servers),flush=True)
  while not stop.is_set() and time.monotonic()-last<40:
   try:await asyncio.wait_for(stop.wait(),1)
   except asyncio.TimeoutError:pass
 finally:
  for s in servers:s.close()
  ts=list(jobs)
  for t in ts:t.cancel()
  await asyncio.gather(*ts,return_exceptions=True)
  for s in servers:await s.wait_closed()
  print('CLEANED',flush=True)
asyncio.run(main())
