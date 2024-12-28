import socket
import asyncio
import sys
from argparse import ArgumentParser

GLOBALS = {}
MAX_BYTES = 2**16

def read_file(directory, filename):
    try:
        with open(f'/{directory}/{filename}', 'rb') as file:
            content = file.read()
            file_size = len(content)
            return True, file_size, content
    except FileNotFoundError:
        return False, 0, b''

def create_file(directory, filename, content):
    try:
        with open(f'/{directory}/{filename}', 'wb') as file:
            file.write(content)
            return True
    except Exception as e:
        print(f"Error creating file at /{directory}: {e}")
        return False

async def handle_client(reader, writer):
    client_address = writer.get_extra_info('peername')
    print(f"Connection from {client_address}")
    try:
        while True:
            data = await reader.read(MAX_BYTES)
            if not data:
                break
            initial_data, body = data.split(b'\r\n\r\n')
            data = initial_data.decode().split('\r\n')
            method, path, protocol = data[0].split(' ')
            data = [item for item in data if item.strip()]
            headers = {}
            print(f"Request data: {data}")
            for header in data[1:]:
                key, value = header.split(': ')
                headers[key] = value
            body = body.decode()
            path = path.lower()
            if path == '/':
                response = b'HTTP/1.1 200 OK\r\n\r\n'
            elif path.startswith('/echo'): # Handle /echo/{str}
                path_params = path.split('/')[1:]
                response = f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(path_params[-1])}\r\n\r\n{path_params[-1]}'.encode()
            elif path.startswith('/user-agent'): # Handle /user-agent
                user_agent = headers.get('User-Agent', 'Unknown')
                response = f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}'.encode()
            elif path.startswith('/files'):
                    directory = GLOBALS['DIR']
                    filename = path.split('/')[-1]
                    if method == 'GET':
                        file_exists, file_size, content = read_file(directory, filename)
                        if file_exists:
                            response = f'HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {file_size}\r\n\r\n'.encode()
                            response += content
                        else:
                            response = b'HTTP/1.1 404 Not Found\r\n\r\n'
                    elif method == 'POST':
                        content = body.encode()
                        success = create_file(directory, filename, content)
                        if success:
                            response = b'HTTP/1.1 201 Created\r\n\r\n'
                        else:
                            response = b'HTTP/1.1 422 Unprocessable Entity \r\n\r\n'
                    else:
                        response = b'HTTP/1.1 405 Method Not Allowed\r\n\r\n'
            else:
                response = b'HTTP/1.1 404 Not Found\r\n\r\n'
            writer.write(response)
            await writer.drain()
    except Exception as e:
        print(f"Error handling {client_address}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection from {client_address} closed")

async def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, default='.')
    args = parser.parse_args()
    if "directory" in args:
        GLOBALS["DIR"] = args.directory

    server = await asyncio.start_server(handle_client, 'localhost', 4221)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server...")
