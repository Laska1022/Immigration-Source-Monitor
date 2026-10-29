"""Optional real loopback HTTP smoke; separate from deterministic pytest tests."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

root=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='ism-http-smoke-') as data:
    demo=subprocess.run([sys.executable,'-m','immigration_monitor','--data-dir',data,'demo'],cwd=root,capture_output=True,text=True,check=True)
    result=json.loads(demo.stdout)
    assert result['steps'][2]['result']=='failed or blocked'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=subprocess.Popen([sys.executable,'-m','immigration_monitor','--data-dir',data,'serve','--port',str(port)],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    # ProxyHandler({}) is exclusively for loopback HTTP to this test-owned server.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        base=f'http://127.0.0.1:{port}'
        for attempt in range(50):
            try:
                with opener.open(base,timeout=2) as response:assert response.status==200
                break
            except OSError:
                if server.poll() is not None:raise RuntimeError('Local server exited before readiness')
                time.sleep(.1)
        else:raise RuntimeError('Local server did not become ready')
        for route,expected in [('/',b'Review inbox'),('/sources',b'FICTIONAL DEMO'),('/events/1',b'Inline comparison'),('/history',b'Immutable observed versions'),('/settings',b'Daily digest archive'),('/backup',b'Backup &amp; restore')]:
            with opener.open(base+route,timeout=5) as response:
                assert response.status==200 and expected in response.read(),route
                assert "script-src 'none'" in response.headers['Content-Security-Policy']
                print(route,'HTTP 200; expected content and CSP verified')
        with opener.open(base+'/versions/1/raw',timeout=5) as response:
            assert response.headers['Content-Disposition'].startswith('attachment;')
        print('PASS: fictional CLI demo, six real HTTP screens, attachment download')
    finally:
        server.terminate()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
