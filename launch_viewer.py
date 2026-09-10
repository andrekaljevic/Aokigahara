#!/usr/bin/env python3
"""Serve the Aokigahara free-roam viewer locally.

The original handover shipped a launch_viewer.py that was lost in the truncated
archive tail; this is a functional replacement. The viewer must be served over
HTTP (ES modules, binary terrain grids and ../models/ references do not load
from file://). The server root is the repository root so that
viewer/ can reach ../models/Aokigahara_Surface_Terrain.glb.

Usage:  python3 launch_viewer.py [--port 8000] [--open]
Then open the printed address (default http://127.0.0.1:8000/viewer/).
"""
import argparse, http.server, mimetypes, os, socketserver, sys, webbrowser
from functools import partial

ROOT = os.path.dirname(os.path.abspath(__file__))
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('text/javascript', '.mjs')
mimetypes.add_type('model/gltf-binary', '.glb')
mimetypes.add_type('model/gltf+json', '.gltf')
mimetypes.add_type('application/octet-stream', '.f32')
mimetypes.add_type('application/octet-stream', '.u8')
mimetypes.add_type('application/json', '.json')

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    def log_message(self, fmt, *args):
        if '--quiet' not in sys.argv:
            super().log_message(fmt, *args)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--bind', default='127.0.0.1')
    ap.add_argument('--open', action='store_true', help='open the viewer in the default browser')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    url = f'http://{a.bind}:{a.port}/viewer/'
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((a.bind, a.port), partial(Handler, directory=ROOT)) as srv:
        print(f'Aokigahara viewer: {url}   (serving {ROOT}; Ctrl+C to stop)')
        if a.open:
            webbrowser.open(url)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nstopped')

if __name__ == '__main__':
    main()
