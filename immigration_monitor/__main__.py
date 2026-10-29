import argparse
import json
import os
import sys
from pathlib import Path

from .db import Store, data_dir


def main():
    parser=argparse.ArgumentParser(description='Immigration Source Monitor — local evidence monitor')
    parser.add_argument('--data-dir',help='Runtime directory outside the repository')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('init',help='Create local database and add starter sources')
    serve=sub.add_parser('serve');serve.add_argument('--port',type=int,default=8765);serve.add_argument('--open',action='store_true')
    check=sub.add_parser('check');check.add_argument('--source',type=int);check.add_argument('--all',action='store_true',help='Check active sources now; still respects Retry-After')
    digest=sub.add_parser('digest');digest.add_argument('--now',action='store_true')
    sub.add_parser('backup')
    restore=sub.add_parser('restore');restore.add_argument('--file',required=True);restore.add_argument('--confirm',action='store_true')
    sub.add_parser('demo',help='Populate only an empty database with clearly fictional observations')
    verify=sub.add_parser('verify-sources');verify.add_argument('--output',required=True)
    args=parser.parse_args()
    if args.data_dir:os.environ['ISM_DATA_DIR']=args.data_dir
    if args.command=='verify-sources':
        from .verification import verify_sources
        return 0 if verify_sources(Path(args.output)) else 1
    store=Store()
    if args.command=='init':store.seed();print('Initialized local data at',store.root)
    elif args.command=='serve':
        from filelock import FileLock,Timeout
        from .web import create_app
        from waitress import serve as wsgi_serve
        try:
            with FileLock(str(store.root/'ui.lock'),timeout=0):
                if args.open:
                    import threading,webbrowser
                    threading.Timer(1.5,lambda:webbrowser.open(f'http://127.0.0.1:{args.port}')).start()
                print(f'Local UI listening on 127.0.0.1:{args.port}; close this console to stop it.',flush=True)
                wsgi_serve(create_app(store),host='127.0.0.1',port=args.port,threads=4,max_request_body_size=128*1024*1024)
        except Timeout:print('This data folder already has a running UI.');return 2
    elif args.command=='check':
        from .monitor import run_checks,UNHEALTHY
        from .notifications import make_digest,deliver_pending
        result=run_checks(store,source_id=args.source,force=args.all,lock_timeout=600 if args.source else 0)
        make_digest(store);delivery=deliver_pending(store)
        print(json.dumps({'checks':result,'delivery':delivery}))
        return 1 if any(status in UNHEALTHY for _,status in result['sources']) else 0
    elif args.command=='digest':
        from .notifications import make_digest,deliver_pending
        print(json.dumps({'digest_id':make_digest(store,force=args.now),'delivery':deliver_pending(store)}))
    elif args.command=='backup':
        from .backup import create_backup
        print(create_backup(store))
    elif args.command=='restore':
        from filelock import FileLock
        from .backup import restore_backup
        if not args.confirm:parser.error('Restore replaces current data; close the app and use --confirm after reviewing the backup')
        safety=restore_backup(store,Path(args.file).expanduser().resolve())
        print('Restored. Pre-restore safety backup:',safety)
        print('Email disabled. Reconfigure credentials and register Windows scheduler separately.')
    elif args.command=='demo':
        from .demo import demo
        print(json.dumps(demo(store),indent=2))
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        # Exception classes convey failure without leaking server credentials or SMTP content.
        print('Command failed:',type(exc).__name__+'. Review application history/configuration.',file=sys.stderr)
        sys.exit(2)
