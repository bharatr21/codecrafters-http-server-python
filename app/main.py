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
        print(f"Request data: {data}")
        url_item = data[0].split(' ')
        method, path, protocol = url_item
        if path == '/':
            client.sendall(b'HTTP/1.1 200 OK\r\n\r\n')
        else:
            client.sendall(b'HTTP/1.1 404 Not Found\r\n\r\n')
    client.close()
if __name__ == "__main__":
    main()
