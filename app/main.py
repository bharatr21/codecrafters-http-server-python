import socket
import asyncio
import sys
from argparse import ArgumentParser

GLOBALS = {}
MAX_BYTES = 2**16

status_message = {
    200: 'OK',
    201: 'Created',
    400: 'Bad Request',
    404: 'Not Found',
    405: 'Method Not Allowed',
    422: 'Unprocessable Entity'
}

VALID_ENCODING_SCHEMES = ['gzip', 'deflate', 'br', 'compress', 'identity', 'zstd', '*']

def make_response(status_code, protocol='HTTP/1.1', headers={}, body=''):
    if body:
        headers['Content-Length'] = len(body)
    response = (
        f'{protocol} {status_code} {status_message[status_code]}\r\n'
        + '\r\n'.join([f'{key}: {value}' for key, value in headers.items()])
        + '\r\n\r\n'
        + body
    )
    print(f"HTTP constructed response: {response}")
    return response.encode()

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
                response = make_response(200)
            elif path.startswith('/echo'): # Handle /echo/{str}
                path_params = path.split('/')[1:]
                headers['Content-Type'] = 'text/plain'
                if 'Accept-Encoding' in headers:
                    encodings = headers['Accept-Encoding'].split(',')
                    valid_encodings = [encoding.strip() for encoding in encodings if encoding.strip() in VALID_ENCODING_SCHEMES]
                    if valid_encodings:
                        headers['Content-Encoding'] = ', '.join(valid_encodings)
                response = make_response(200, headers=headers, body=path_params[-1])
            elif path.startswith('/user-agent'): # Handle /user-agent
                user_agent = headers.get('User-Agent', 'Unknown')
                headers['Content-Type'] = 'text/plain'
                response = make_response(200, headers=headers, body=user_agent)
            elif path.startswith('/files'):
                    directory = GLOBALS['DIR']
                    filename = path.split('/')[-1]
                    if method == 'GET':
                        file_exists, file_size, content = read_file(directory, filename)
                        if file_exists:
                            response = make_response(200, headers={"Content-Type": "application/octet-stream"}, body=content.decode())
                        else:
                            response = make_response(404)
                    elif method == 'POST':
                        content = body.encode()
                        success = create_file(directory, filename, content)
                        if success:
                            response = make_response(201)
                        else:
                            response = make_response(422)
                    else:
                        response = make_response(405)
            else:
                response = make_response(404)
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
