from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import os

hostName = "0.0.0.0"
serverPort = 8080

class CancamusaServer(BaseHTTPRequestHandler):
    def do_GET(self):
        pth = os.path.join(self.server.static_path, os.path.abspath(self.path).removeprefix("/"))
        try:
            with open(pth, 'rb') as r_f:
                data = r_f.read()
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            print(e)
            self.send_response(404)

def start_server(static_dir):
    webServer = HTTPServer((hostName, serverPort), CancamusaServer)
    webServer.static_path = static_dir
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), CancamusaServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")