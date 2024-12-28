# Uncomment this to pass the first stage
import socket


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    client, client_address = server_socket.accept() # wait for client
    while True:
        data = client.recv(1024)
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
            client.sendall(b'HTTP/1.1 200 OK\r\n\r\n')
        elif path.startswith('/echo'): # Handle /echo/{str}
            path_params = path.split('/')[1:]
            client.sendall(f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(path_params[-1])}\r\n\r\n{path_params[-1]}'.encode())
        elif path.startswith('/user-agent'): # Handle /user-agent
            client.sendall(f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}'.encode())
        else:
            client.sendall(b'HTTP/1.1 404 Not Found\r\n\r\n')
    client.close()
if __name__ == "__main__":
    main()
