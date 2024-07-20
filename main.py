from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import multiprocessing
import socket
import mimetypes
import json
from urllib.parse import urlparse, parse_qs, unquote_plus
import logging
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

# Константи
HTTP_SERVER_PORT = 3000
UDP_IP = "localhost"
UDP_PORT = 5001
MONGO_URI = "mongodb://mongo:27017/"
DB_NAME = "messages_db"
COLLECTION_NAME = "messages"

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Функція для збереження даних у MongoDB
def save_data(data):
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    collection.insert_one(data)
    client.close()

# Обробник HTTP запитів
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        
        try:
            # Визначаємо шлях до файлу
            file_path = os.path.join(os.getcwd(), self.path[1:])

            if not os.path.isfile(file_path):
                self.send_error(404, "File not found")
                self.path = 'error.html'
                file_path = os.path.join(os.getcwd(), self.path[1:])

            mimetype, _ = mimetypes.guess_type(file_path)
            self.send_response(200)
            self.send_header('Content-type', mimetype)
            self.end_headers()
            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())
        except Exception as e:
            self.send_error(500, "Internal server error")
            logging.error(f"Error handling GET request: {e}")

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse_qs(unquote_plus(post_data.decode('utf-8')))
            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]
            # Створюємо ключ "date" з часом отримання повідомлення
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            doc = {"date": timestamp, "username": username, "message": message}
            
            # Відправка даних на UDP сервер
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(json.dumps(doc).encode(), (UDP_IP, UDP_PORT))
            
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

# Запуск HTTP сервера
def start_http_server():
    server_address = ('', HTTP_SERVER_PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    logging.info(f"Serving HTTP on port {HTTP_SERVER_PORT}")
    httpd.serve_forever()

# Запуск UDP сервера
def start_udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((UDP_IP, UDP_PORT))
        logging.info(f"Serving UDP on port {UDP_PORT}")
        while True:
            data, _ = s.recvfrom(1024)
            message = json.loads(data.decode())
            save_data(message)

# Запуск серверів
if __name__ == "__main__":
    http_process = multiprocessing.Process(target=start_http_server)
    udp_process = multiprocessing.Process(target=start_udp_server)
    
    http_process.start()
    udp_process.start()
    
    http_process.join()
    udp_process.join()
