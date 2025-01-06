import socket
import struct
import pickle
import threading
import pyaudio
import os
# Server Configuration File sharing
servr_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servr_socket.bind(("127.0.0.1", 7000))  # Different port for file sharing
servr_socket.listen(4)

SAVE_FOLDER = os.path.expanduser("server_downloads")
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)
    
# Server Configuration chatting
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("127.0.0.1", 8000))
server_socket.listen(4)

# Server Configuration audio
# Create and bind the servera socket
servera_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
servera_socket.bind(("127.0.0.1", 9000))

BUFFER_SIZE = 4096
clients_connected5= {}
clients_connected1 = {}
clients_connected = {}
clients_data = {}
count = 1

# Audio configurations for low-latency
CHUNK = 512  # Smaller chunk for lower delay
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono for reduced data size
RATE = 22050  # Lower rate for reduced data size

def connection5_requests():
    """Handles incoming client connection requests."""
    while True:
        print("Waiting for connection...")
        file_socket, address3 = servr_socket.accept()

        print(f"Connection from {address3} has been established")
        if len(clients_connected5) >= 4:
            file_socket.send('not_allowed'.encode())
            file_socket.close()
            continue
        else:
            file_socket.send('allowed'.encode())

        try:
            client_name5 = file_socket.recv(1024).decode('utf-8')
        except:
            print(f"{address3} disconnected during identification")
            file_socket.close()
            continue

        print(f"{address3} identified itself as {client_name5}")
        clients_connected5[file_socket] = client_name5

        threading.Thread(target=handle_file_transfer, args=(file_socket,)).start()
        
def connection1_requests():
    threading.Thread(target=handle_client_data1).start()

def handle_client_data1():
    """Continuously listen for audio data and broadcast it to clients."""
    while True:
        try:
            data1, address1 = servera_socket.recvfrom(CHUNK * 2)  # Receive data
            if address1 not in clients_connected1:
                # Add client if not already connected
                if len(clients_connected1) < 4:
                    clients_connected1[address1] = True
                    print(f"New client connected: {address1}")
                    servera_socket.sendto(b'allowed', address1)
                else:
                    servera_socket.sendto(b'not_allowed', address1)
                    continue
            else:
                # Broadcast to all other clients
                broadcast_audio(address1, data1)
        except Exception as e:
            print(f"Error handling client data: {e}")
        
def connection_requests():
    global count
    while True:
        print("Waiting for connection...")
        client_socket, address = server_socket.accept()

        if len(clients_connected) == 4:
            client_socket.send('not_allowed'.encode())
            client_socket.close()
            continue
        else:
            client_socket.send('allowed'.encode())

        try:
            client_name = client_socket.recv(4096).decode('utf-8')
        except:
            print(f"{address} disconnected")
            client_socket.close()
            continue

        print(f"{address} identified itself as {client_name}")
        clients_connected[client_socket] = (client_name, count)


        # Image Receiving
        image_size_bytes = client_socket.recv(4096)
        image_size_int = struct.unpack('i', image_size_bytes)[0]

        client_socket.send('received'.encode())
        image_extension = client_socket.recv(1024).decode()

        b = b''
        while len(b) < image_size_int:
            image_bytes = client_socket.recv(1024)
            b += image_bytes

        clients_data[count] = (client_name, b, image_extension)

        clients_data_bytes = pickle.dumps(clients_data)
        clients_data_length = struct.pack('i', len(clients_data_bytes))

        client_socket.send(clients_data_length)
        client_socket.send(clients_data_bytes)

        if client_socket.recv(1024).decode() == 'image_received':
            client_socket.send(struct.pack('i', count))
            for client in clients_connected:
                if client != client_socket:
                    client.send('notification'.encode())
                    data = pickle.dumps({'message': f"{client_name} joined the chat", 
                                         'extension': image_extension,
                                         'image_bytes': b, 'name': client_name, 
                                         'n_type': 'joined', 'id': count})
                    data_length_bytes = struct.pack('i', len(data))
                    client.send(data_length_bytes)
                    client.send(data)
        count += 1
        threading.Thread(target=receive_data, args=(client_socket,)).start()    
        threading.Thread(target=connection1_requests).start()
        threading.Thread(target=connection5_requests).start()
 
def receive_data(client_socket):
    while True:
        try:
            data_bytes = client_socket.recv(4096)

            for client in clients_connected:
                if client != client_socket:
                    client.send('message'.encode())
                    client.send(data_bytes)

        except (ConnectionResetError, ConnectionAbortedError):
            handle_disconnect(client_socket)
            break

def broadcast_audio(sender_address1, data_bytes):
    """Broadcast audio data from one client to all others."""
    for client_address1 in list(clients_connected1.keys()):
        if client_address1 != sender_address1:
            try:
                servera_socket.sendto(data_bytes, client_address1)
            except Exception as e:
                print(f"Error sending audio to {client_address1}: {e}")
                handle_disconnect1(client_address1)

def handle_disconnect1(client_address1):
    """Handle disconnection of a client."""
    if client_address1 in clients_connected1:
        print(f"Client {client_address1} disconnected")
        del clients_connected1[client_address1]

        
def broadcast_file(sender_socket, filename):
    """Broadcasts the received file to all connected clients except the sender."""
    file_path = os.path.join(SAVE_FOLDER, filename)

    with open(file_path, "rb") as f:
        file_data = f.read()

    for client_socket5 in clients_connected5:
        if client_socket5 != sender_socket:
            try:
                # Send file metadata
                metadata = f"{filename}|{len(file_data)}"
                client_socket5.send(metadata.encode('utf-8'))

                # Send file data
                client_socket5.sendall(file_data)
                print(f"File {filename} sent to {clients_connected5[client_socket5]}")
            except Exception as e:
                print(f"Error sending file to {clients_connected5[client_socket5]}: {e}")
                handle_disconnect5(client_socket5)

def handle_file_transfer(file_socket):
    """Handles file transfer from a client and broadcasts to others."""
    try:
        while True:
            # Receive file metadata
            metadata = file_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not metadata:
                break

            filename, filesize = metadata.split('|')
            filesize = int(filesize)
            print(f"Receiving file: {filename} ({filesize} bytes) from {clients_connected5[file_socket]}")

            # Ensure the file is saved in the designated folder
            file_path = os.path.join(SAVE_FOLDER, filename)

            # Receive the file data
            with open(file_path, "wb") as f:
                bytes_received = 0
                while bytes_received < filesize:
                    data = file_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    f.write(data)
                    bytes_received += len(data)

            print(f"File {filename} saved to {file_path}")

            # Broadcast the file to other clients
            broadcast_file(file_socket, filename)

    except Exception as e:
        print(f"Error receiving file from {clients_connected5[file_socket]}: {e}")
    finally:
        handle_disconnect5(file_socket)
        
def handle_disconnect5(file_socket):
    """Handle disconnection of a client."""
    if file_socket in clients_connected5:
        print(f"{clients_connected5[file_socket]} disconnected")
        del clients_connected5[file_socket]
        file_socket.close()
        
def handle_disconnect(client_socket):
    
    print(f"{clients_connected[client_socket][0]} disconnected")
    for client in clients_connected:
        if client != client_socket:
            client.send('notification'.encode())
            data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                 'id': clients_connected[client_socket][1], 'n_type': 'left'})
            data_length_bytes = struct.pack('i', len(data))
            client.send(data_length_bytes)
            client.send(data)

    del clients_data[clients_connected[client_socket][1]]
    del clients_connected[client_socket]
    client_socket.close()


if __name__ == "__main__":
    connection_requests()
