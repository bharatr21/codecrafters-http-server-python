import socket
import asyncio
import sys

def handle_file(directory, filename):
    try:
        with open(f'/{directory}/{filename}', 'rb') as file:
            content = file.read()
            file_size = len(content)
            return True, file_size, content
    except FileNotFoundError:
        return False, 0, b''

async def handle_client(reader, writer):
    client_address = writer.get_extra_info('peername')
    print(f"Connection from {client_address}")
    try:
        while True:
            data = await reader.read(100)
            if not data:
                break
            data = data.decode().split('\r\n')
            data = [item for item in data if item.strip()]
            headers = data[1:]
            user_agent = ''
            print(f"Request data: {data}")
            for header in headers:
                if header.startswith('User-Agent'):
                    user_agent = header.split(': ')[-1]
            url_item = data[0].split(' ')
            method, path, protocol = url_item
            path = path.lower()
            if path == '/':
                response = b'HTTP/1.1 200 OK\r\n\r\n'
            elif path.startswith('/echo'): # Handle /echo/{str}
                path_params = path.split('/')[1:]
                response = f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(path_params[-1])}\r\n\r\n{path_params[-1]}'.encode()
            elif path.startswith('/user-agent'): # Handle /user-agent
                response = f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}'.encode()
            elif path.startswith('/files'):
                directory = sys.argv[2]
                filename = path.split('/')[-1]
                file_exists, file_size, content = handle_file(directory, filename)
                if file_exists:
                    response = f'HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {file_size}\r\n\r\n'.encode()
                    response += content
                else:
                    response = b'HTTP/1.1 404 Not Found\r\n\r\n'
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
    server_socket = await asyncio.start_server(handle_client, 'localhost', 4221)
    async with server_socket:
        await server_socket.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server...")

