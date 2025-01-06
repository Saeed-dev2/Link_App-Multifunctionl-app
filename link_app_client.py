import socket
import pickle
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox, scrolledtext
import pickle
from datetime import datetime
import pyaudio
import os
import threading
import struct

# Global variables
audio_stream = None
audio_socket = None
is_call_active = False
playback_stream = None
pending_file = None
pending_filesize = 0
pending_filename = ""
x="arham"
# Client Configuration #file sharing
SERVER_IP = "127.0.0.1"
SERVER_PORT = 7000
BUFFER_SIZE = 4096

# Connect to server
file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
file_socket.connect((SERVER_IP, SERVER_PORT))

# Identify client for file
client_name3= x+"file" # Change this for each client
file_socket.send(client_name3.encode('utf-8'))
# Downloads folder
DOWNLOADS_DIR = os.path.expanduser("receive_file")
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)
# Discarded folder
Discarded_DIR = os.path.expanduser("Discarded_Files")
if not os.path.exists(Discarded_DIR):
    os.makedirs(Discarded_DIR)

# Client Configuration # Audio Calling
# Client Configuration
servera_ip = "127.0.0.1"
servera_port = 9000
client_name1 = x+"call" # Change this for different clients

# Audio configurations
# Audio configurations for low-latency
CHUNK = 512  # Smaller chunk for reduced delay
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono for smaller data size
RATE = 22050  # Reduced rate for lower latency


def handle_file_metadata():
    """Listen for incoming file metadata and prompt the user for action."""
    global pending_file, pending_filesize, pending_filename

    try:
        while True:
            # Receive file metadata
            metadata = file_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not metadata:
                continue  # Skip if no data received

            # Debug print for received metadata
            print(f"Received Files: {metadata}")

            # Validate metadata format
            if '|' not in metadata:
                continue

            pending_filename, pending_filesize = metadata.split('|', 1)
            if not pending_filename or not pending_filesize.isdigit():
                print("Invalid metadata content")
                continue

            pending_filesize = int(pending_filesize)

            # Notify user about incoming file
            prompt_label.config(text=f"{pending_filename} ({pending_filesize} bytes).")
            receive_button.config(state=tk.NORMAL)
            discard_button.config(state=tk.NORMAL)

            # Pause to wait for user action
            action_event.wait()
            action_event.clear()
    except Exception as e:
        print(f"Error receiving file metadata: {e}")

def receive_file():
    """Receive the pending file and save it."""
    global pending_file, pending_filesize, pending_filename

    if not pending_filename:
        return

    try:
        filepath = os.path.join(DOWNLOADS_DIR, pending_filename)
        with open(filepath, "wb") as f:
            bytes_received = 0
            while bytes_received < pending_filesize:
                chunk = file_socket.recv(BUFFER_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)

        # Notify the user and reset the state
        messagebox.showinfo("File Received", f"File '{pending_filename}' saved to Received Files.")
    except Exception as e:
        messagebox.showerror("Error", f"Error receiving file: {e}")
    finally:
        reset_state()
        
def reset_state():
    """Reset the global state and disable buttons."""
    global pending_file, pending_filesize, pending_filename

    pending_file = None
    pending_filesize = 0
    pending_filename = ""

    prompt_label.config(text="No incoming files.")
    receive_button.config(state=tk.DISABLED)
    discard_button.config(state=tk.DISABLED)

    # Notify the metadata thread to resume listening
    action_event.set()
    
def discard_file():
    """Discard the pending file."""
    global pending_filename
    if not pending_filename:
        return

    try:
        filepath = os.path.join(Discarded_DIR, pending_filename)
        with open(filepath, "wb") as f:
            bytes_received = 0
            while bytes_received < pending_filesize:
                chunk = file_socket.recv(BUFFER_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)

        # Notify the user and reset the state
        messagebox.showinfo("File Discarded", f"File 'File '{pending_filename}' discarded.")
    except Exception as e:
        messagebox.showerror("Error", f"Error receiving file: {e}")
    finally:
        reset_state()

def send_file():
    """Handles file selection and sending."""
    filepath = filedialog.askopenfilename()
    if not filepath:
        return

    try:
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        metadata = f"{filename}|{filesize}"

        # Send metadata
        file_socket.send(metadata.encode('utf-8'))

        # Send file data
        with open(filepath, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                file_socket.sendall(chunk)

        messagebox.showinfo("File Sent", f"File '{filename}' sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send file: {e}")

def on_close(self):
    """Handle closing the application."""
    file_socket.close()
    self.destroy()
    
def start_call():
    """Initiates the call by setting up audio streams and communication."""
    global audio_socket, audio_stream, is_call_active
    voice_call_button.config(state=tk.DISABLED)
    end_call_button.config(state=tk.NORMAL)
    if is_call_active:
        messagebox.showinfo("Info", "Call is already active!")
        return

    try:
        # Create a UDP socket
        audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        audio_socket.sendto(client_name1.encode('utf-8'), (servera_ip, servera_port))

        # Start audio streaming
        pyaudio_instance = pyaudio.PyAudio()
        audio_stream = pyaudio_instance.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        global playback_stream
        playback_stream = pyaudio_instance.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True
        )

        is_call_active = True
        threading.Thread(target=send_audio).start()
        threading.Thread(target=receive_audio).start()

        messagebox.showinfo("Info", "Call started successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start call: {e}")

def send_audio():
    """Streams audio data from the microphone to the server."""
    global audio_socket, audio_stream, is_call_active
    try:
        while is_call_active:
            data1 = audio_stream.read(CHUNK, exception_on_overflow=False)
            audio_socket.sendto(data1, (servera_ip, servera_port))
    except Exception as e:
        print(f"Error in sending audio: {e}")

def receive_audio():
    """Receives audio data from the server and plays it."""
    global audio_socket, is_call_active, playback_stream

    try:
        while is_call_active:
            data1, _ = audio_socket.recvfrom(CHUNK * 2)  # Adjust buffer for incoming data
            if not data1:
                break
            playback_stream.write(data1)
    except Exception as e:
        print(f"Error in receiving audio: {e}")

def end_call():
    """Terminates the call by stopping streams and closing sockets."""
    global audio_socket, audio_stream, playback_stream, is_call_active
    voice_call_button.config(state=tk.NORMAL)
    end_call_button.config(state=tk.DISABLED)
    
    if not is_call_active:
        messagebox.showinfo("Info", "No active call to end!")
        return

    try:
        is_call_active = False

        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()

        if playback_stream:
            playback_stream.stop_stream()
            playback_stream.close()

        if audio_socket:
            audio_socket.close()

        messagebox.showinfo("Info", "Call ended successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to end call: {e}")


try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class FirstScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        global action_event
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.x_co = int((screen_width / 2) - (550 / 2))
        self.y_co = int((screen_height / 2) - (400 / 2)) - 80
        self.geometry(f"550x400+{self.x_co}+{self.y_co}")
        self.title("Link App")

        self.user = None
        self.image_extension = None
        self.image_path = None

        self.first_frame = tk.Frame(self, bg="sky blue")
        self.first_frame.pack(fill="both", expand=True)

        app_icon = Image.open('images/chat_ca.png')
        app_icon = ImageTk.PhotoImage(app_icon)

        self.iconphoto(False, app_icon)

        background = Image.open("images/login_bg_ca.jpg")
        background = background.resize((550, 400))
        background = ImageTk.PhotoImage(background)

        upload_image = Image.open('images/upload_ca.png')
        upload_image = upload_image.resize((25, 25))
        upload_image = ImageTk.PhotoImage(upload_image)

        self.user_image = 'images/user.png'

        tk.Label(self.first_frame, image=background).place(x=0, y=0)

        head = tk.Label(self.first_frame, text="Sign Up", font="lucida 17 bold", bg="grey")
        head.place(relwidth=1, y=24)

        self.profile_label = tk.Label(self.first_frame, bg="grey")
        self.profile_label.place(x=350, y=75, width=150, height=140)

        upload_button = tk.Button(self.first_frame, image=upload_image, compound="left", text="Upload Image",
                                  cursor="hand2", font="lucida 12 bold", padx=2, command=self.add_photo)
        upload_button.place(x=345, y=220)

        self.username = tk.Label(self.first_frame, text="Username", font="lucida 12 bold", bg="grey")
        self.username.place(x=80, y=150)

        self.username_entry = tk.Entry(self.first_frame,  font="lucida 12 bold", width=10,
                                       highlightcolor="blue", highlightthickness=1)
        self.username_entry.place(x=195, y=150)

        self.username_entry.focus_set()

        submit_button = tk.Button(self.first_frame, text="Connect", font="lucida 12 bold", padx=30, cursor="hand2",
                                  command=self.process_data, bg="#16cade", relief="solid", bd=2)

        submit_button.place(x=200, y=275)
        # Event to coordinate file reception
        action_event = threading.Event()

        # Start metadata handling thread
        threading.Thread(target=handle_file_metadata, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", on_close)
        self.mainloop()
    def add_photo(self):
        self.image_path = filedialog.askopenfilename()
        image_name = os.path.basename(self.image_path)
        self.image_extension = image_name[image_name.rfind('.')+1:]

        if self.image_path:
            user_image = Image.open(self.image_path)
            user_image = user_image.resize((150, 140))
            user_image.save('resized'+image_name)
            user_image.close()

            self.image_path = 'resized'+image_name
            user_image = Image.open(self.image_path)

            user_image = ImageTk.PhotoImage(user_image)
            self.profile_label.image = user_image
            self.profile_label.config(image=user_image)
    def process_data(self):
        if self.username_entry.get():
            self.profile_label.config(image="")

            if len((self.username_entry.get()).strip()) > 6:
                self.user = self.username_entry.get()[:6]+"."
            else:
                self.user = self.username_entry.get()

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect(("127.0.0.1", 8000))
                status = client_socket.recv(1024).decode()
                if status == 'not_allowed':
                    client_socket.close()
                    messagebox.showinfo(title="Can't connect !", message='Sorry, server is completely occupied.'
                                                                         'Try again later')
                    return

            except ConnectionRefusedError:
                messagebox.showinfo(title="Can't connect !", message="Server is offline , try again later.")
                print("Server is offline , try again later.")
                return

            client_socket.send(self.user.encode('utf-8'))

            if not self.image_path:
                self.image_path = self.user_image
            with open(self.image_path, 'rb') as image_data:
                image_bytes = image_data.read()

            image_len = len(image_bytes)
            image_len_bytes = struct.pack('i', image_len)
            client_socket.send(image_len_bytes)

            if client_socket.recv(1024).decode() == 'received':
                client_socket.send(str(self.image_extension).strip().encode())

            client_socket.send(image_bytes)

            clients_data_size_bytes = client_socket.recv(1024*8)
            clients_data_size_int = struct.unpack('i', clients_data_size_bytes)[0]
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break

            clients_connected = pickle.loads(b)

            client_socket.send('image_received'.encode())

            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.user} is user no. {user_id}")
            ChatScreen(self, self.first_frame, client_socket, clients_connected, user_id)
            
class ChatScreen(tk.Canvas):
    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):
        super().__init__(parent, bg="#2b2b2b")
        global prompt_label, receive_button, discard_button, voice_call_button, end_call_button
        self.client_socket = client_socket
        self.p = pyaudio.PyAudio()
        self.audio_stream = None
        self.is_calling = False 

        self.window = 'ChatScreen'

        self.first_frame = first_frame
        self.first_frame.pack_forget()

        self.parent = parent
        self.parent.bind('<Return>', lambda e: self.sent_message_format(e))

        self.all_user_image = {}

        self.user_id = user_id


        self.clients_connected = clients_connected

        # self.parent.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(self.first_frame))
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_socket = client_socket
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        x_co = int((screen_width / 2) - (680 / 2))
        y_co = int((screen_height / 2) - (750 / 2)) - 80
        self.parent.geometry(f"680x800+{x_co}+{y_co}")

        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40))
        self.user_image = ImageTk.PhotoImage(user_image)

        # global background
        # background = Image.open("images/chat_bg_ca.jpg")
        # background = background.resize((1600, 1500))
        # background = ImageTk.PhotoImage(background)

        global group_photo
        group_photo = Image.open('images/group_ca.png')
        group_photo = group_photo.resize((60, 60))
        group_photo = ImageTk.PhotoImage(group_photo)

        self.y = 140
        self.clients_online_labels = {}

        # self.create_image(0, 0, image=background)

        self.create_text(545, 120, text="Online", font="lucida 12 bold", fill="#40C961")

        tk.Label(self, text="   ", font="lucida 15 bold", bg="#b5b3b3").place(x=4, y=29)

        tk.Label(self, text="Welcome to Link App", font="lucida 15 bold", padx=20, fg="black",
                 bg="#b5b3b3", anchor="w", justify="left").place(x=88, y=29, relwidth=1)

        self.create_image(60, 40, image=group_photo)

        container = tk.Frame(self)
        # 595656
        # d9d5d4
        container.place(x=40, y=120, width=450, height=550)
        self.canvas = tk.Canvas(container, bg="#595656")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#595656")

        scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        def resize_frame(e):
            self.canvas.itemconfig(scrollable_window, width=e.width)

        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.yview_moveto(1.0)

        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame)
        self.canvas.pack(fill="both", expand=True)
        button_style1 = {"fg": "#000000", "font": "lucida 11 bold","bg": "#ffffff", "relief": "flat","bd": 3,"padx": 10,"pady": 5}

        # Common Button Styling
        #button_style = {"fg": "#83eaf7", "font": "lucida 11 bold", "bg": "#444444","relief": "flat", "bd": 3, "padx": 10, "pady": 5}   
        # # Enhanced Button Styling for Start/End Call
        start_call_style = {"fg": "white", "bg": "#28a745", "activebackground": "#218838",
                            "font": "lucida 11 bold", "padx": 10, "pady": 5, "relief": "ridge", "bd": 3}

        end_call_style = {"fg": "white", "bg": "#dc3545", "activebackground": "#c82333",
                          "font": "lucida 11 bold", "padx": 10, "pady": 5, "relief": "ridge", "bd": 3}
        # Send Button
        send_button = tk.Button(self, text="Send", command=self.sent_message_format, **button_style1)
        send_button.place(x=465, y=675,width=70, height=47)  # Adjusted position for better spacing

        #Start Call Button
        voice_call_button = tk.Button(self, text="Start Call", command=start_call, **start_call_style)
        voice_call_button.place(x=147, y=70,width=105, height=50)

        # End Call Button
        end_call_button = tk.Button(self, text="End Call", command=end_call,state=tk.DISABLED,**end_call_style)
        end_call_button.place(x=250, y=70,width=100, height=50)

        # Send File Button
        file_send_button = tk.Button(self, text="SendFile", command=send_file, **button_style1)
        file_send_button.place(x=540, y=675,width=93, height=47)
        
        # Notification area
        prompt_label = tk.Label(self,text="No incoming files.",font=("Arial", 9, "bold"),bg="white",
                            fg="black",wraplength=420,relief="solid",bd=2)
        prompt_label.place(x=39, y=725, width=426, height=73)

        # Receive button
        receive_button = tk.Button(self,text="Receivefile", command=receive_file, state=tk.DISABLED, **button_style1)
        receive_button.place(x=465, y=726,width=122, height=34)

        # Discard button
        discard_button = tk.Button(self,text="Discardfile", command=discard_file, state=tk.DISABLED, **button_style1)
        discard_button.place(x=465, y=764,width=122, height=34)
        
        self.entry = tk.Text(self, font="lucida 10 bold", width=38, height=2,
                             highlightcolor="blue", highlightthickness=1)
        self.entry.place(x=40, y=670)

        self.entry.focus_set()

        # ---------------------------emoji code logic-----------------------------------

        emoji_data = [('emojis/u0001f44a.png', '\U0001F44A'), ('emojis/u0001f44c.png', '\U0001F44C'), ('emojis/u0001f44d.png', '\U0001F44D'),
                      ('emojis/u0001f495.png', '\U0001F495'), ('emojis/u0001f496.png', '\U0001F496'), ('emojis/u0001f4a6.png', '\U0001F4A6'),
                      ('emojis/u0001f4a9.png', '\U0001F4A9'), ('emojis/u0001f4af.png', '\U0001F4AF'), ('emojis/u0001f595.png', '\U0001F595'),
                      ('emojis/u0001f600.png', '\U0001F600'), ('emojis/u0001f602.png', '\U0001F602'), ('emojis/u0001f603.png', '\U0001F603'),
                      ('emojis/u0001f605.png', '\U0001F605'), ('emojis/u0001f606.png', '\U0001F606'), ('emojis/u0001f608.png', '\U0001F608'),
                      ('emojis/u0001f60d.png', '\U0001F60D'), ('emojis/u0001f60e.png', '\U0001F60E'), ('emojis/u0001f60f.png', '\U0001F60F'),
                      ('emojis/u0001f610.png', '\U0001F610'), ('emojis/u0001f618.png', '\U0001F618'), ('emojis/u0001f61b.png', '\U0001F61B'),
                      ('emojis/u0001f61d.png', '\U0001F61D'), ('emojis/u0001f621.png', '\U0001F621'), ('emojis/u0001f624.png', '\U0001F621'),
                      ('emojis/u0001f631.png', '\U0001F631'), ('emojis/u0001f632.png', '\U0001F632'), ('emojis/u0001f634.png', '\U0001F634'),
                      ('emojis/u0001f637.png', '\U0001F637'), ('emojis/u0001f642.png', '\U0001F642'), ('emojis/u0001f64f.png', '\U0001F64F'),
                      ('emojis/u0001f920.png', '\U0001F920'), ('emojis/u0001f923.png', '\U0001F923'), ('emojis/u0001f928.png', '\U0001F928')]

        emoji_x_pos = 490
        emoji_y_pos = 520
        for Emoji in emoji_data:
            global emojis
            emojis = Image.open(Emoji[0])
            emojis = emojis.resize((20, 20))
            emojis = ImageTk.PhotoImage(emojis)

            emoji_unicode = Emoji[1]
            emoji_label = tk.Label(self, image=emojis, text=emoji_unicode, bg="#194548", cursor="hand2")
            emoji_label.image = emojis
            emoji_label.place(x=emoji_x_pos, y=emoji_y_pos)
            emoji_label.bind('<Button-1>', lambda x: self.insert_emoji(x))

            emoji_x_pos += 25
            cur_index = emoji_data.index(Emoji)
            if (cur_index + 1) % 6 == 0:
                emoji_y_pos += 25
                emoji_x_pos = 490

        # -------------------end of emoji code logic-------------------------------------

        m_frame = tk.Frame(self.scrollable_frame, bg="#d9d5d4")

        t_label = tk.Label(m_frame, bg="#d9d5d4", text=datetime.now().strftime('%H:%M'), font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=f"Happy Chatting {self.parent.user}",
                           font="lucida 10 bold", bg="orange")
        m_label.pack(fill="x")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.pack(fill="both", expand=True)

        self.clients_online([])
        # Event to coordinate file reception
        

        # Start metadata handling thread
        
        t = threading.Thread(target=self.receive_data)
        t.setDaemon(True)
        t.start()
        

    def receive_data(self):
        """Handle incoming data from the server."""
        while True:
            try:
                # Receive the header (notification or file)
                data_type = self.client_socket.recv(1024).decode()
                
                if data_type == 'FILE':
                    # Handle file transmission: file name and file size
                    file_info = self.client_socket.recv(1024).decode()
                    file_name, file_size = file_info.split(":")
                    file_size = int(file_size)

                    # Now call the method to receive the file
                    self.receive_file(file_name, file_size)

                elif data_type == 'notification':
                    # Handle notifications (e.g., messages)
                    data_size = self.client_socket.recv(4)
                    if len(data_size) < 4:
                        print("Error: Received less than 4 bytes for data size")
                        break
                    
                    # Unpack the size of the notification data
                    data_size_int = struct.unpack('i', data_size)[0]

                    # Receive the notification data in chunks
                    b = b''
                    while len(b) < data_size_int:
                        data_bytes = self.client_socket.recv(min(4096, data_size_int - len(b)))
                        if not data_bytes:
                            break
                        b += data_bytes
                    
                    # Deserialize the notification data
                    data = pickle.loads(b)
                    self.notification_format(data)

                else:
                    # For other types of data (messages, etc.), simply receive the data
                    data_bytes = self.client_socket.recv(4096)
                    data = pickle.loads(data_bytes)
                    self.received_message_format(data)

            except ConnectionAbortedError:
                print("You disconnected...")
                self.client_socket.close()
                break
            except ConnectionResetError:
                messagebox.showinfo(title='No Connection!', message="Server offline..try connecting again later")
                self.client_socket.close()
                self.first_screen()
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
            
    def on_closing(self):
        if self.window == 'ChatScreen':
            res = messagebox.askyesno(title='Warning !',message="Do you really want to disconnect ?")
            if res:
                import os
                os.remove(self.all_user_image[self.user_id])
                self.client_socket.close()
                self.first_screen()
        else:
            self.parent.destroy()
            
    def received_message_format(self, data):

        message = data['message']
        from_ = data['from']

        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        # if not os.path.exists(f"{from_}.{sender_image_extension}"):
        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image)

        im = Image.open(f"{from_}.{sender_image_extension}")
        im = im.resize((40, 40))
        im = ImageTk.PhotoImage(im)

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        m_frame.columnconfigure(1, weight=1)

        t_label = tk.Label(m_frame, bg="#595656",fg="white", text=datetime.now().strftime('%H:%M'), font="lucida 7 bold",
                           justify="left", anchor="w")
        t_label.grid(row=0, column=1, padx=2, sticky="w")

        m_label = tk.Label(m_frame, wraplength=250,fg="black", bg="#c5c7c9", text=message, font="lucida 9 bold", justify="left",
                           anchor="w")
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        i_label = tk.Label(m_frame, bg="#595656", image=im)
        i_label.image = im
        i_label.grid(row=0, column=0, rowspan=2)

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    def sent_message_format(self, event=None):

        message = self.entry.get('1.0', 'end-1c')

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c")

            from_ = self.user_id

            data = {'from': from_, 'message': message}
            data_bytes = pickle.dumps(data)

            self.client_socket.send(data_bytes)

            m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

            m_frame.columnconfigure(0, weight=1)

            t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'),
                               font="lucida 7 bold", justify="right", anchor="e")
            t_label.grid(row=0, column=0, padx=2, sticky="e")

            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="black", bg="#40C961",
                               font="lucida 9 bold", justify="left",
                               anchor="e")
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            i_label = tk.Label(m_frame, bg="#595656", image=self.user_image)
            i_label.image = self.user_image
            i_label.grid(row=0, column=1, rowspan=2, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1.0)
    def notification_format(self, data):
        if data['n_type'] == 'joined':

            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            self.clients_connected[client_id] = (name, image, extension)
            self.clients_online([client_id, name, image, extension])
            # print(self.clients_connected)

        elif data['n_type'] == 'left':
            client_id = data['id']
            message = data['message']
            self.remove_labels(client_id)
            del self.clients_connected[client_id]

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        t_label = tk.Label(m_frame, fg="white", bg="#595656", text=datetime.now().strftime('%H:%M'),
                           font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message, font="lucida 10 bold", justify="left", bg="sky blue")
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.yview_moveto(1.0)
    def clients_online(self, new_added):
        if not new_added:
            pass
            for user_id in self.clients_connected:
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                self.all_user_image[user_id] = f"{user_id}.{extension}"

                user = Image.open(f"{user_id}.{extension}")
                user = user.resize((45, 45))
                user = ImageTk.PhotoImage(user)

                b = tk.Label(self, image=user, text=name, compound="left",fg="white", bg="#2b2b2b", font="lucida 10 bold", padx=15)
                b.image = user
                self.clients_online_labels[user_id] = (b, self.y)

                b.place(x=500, y=self.y)
                self.y += 60
        else:
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            self.all_user_image[user_id] = f"{user_id}.{extension}"

            user = Image.open(f"{user_id}.{extension}")
            user = user.resize((45, 45))
            user = ImageTk.PhotoImage(user)

            b = tk.Label(self, image=user, text=name, compound="left", fg="white", bg="#2b2b2b",
                         font="lucida 10 bold", padx=15)
            b.image = user
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=500, y=self.y)
            self.y += 60
    def remove_labels(self, client_id):
        for user_id in self.clients_online_labels.copy():
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]
            if user_id == client_id:
                print("yes")
                b.destroy()
                del self.clients_online_labels[client_id]
                import os
                # os.remove(self.all_user_image[user_id])

            elif user_id > client_id:
                y_co -= 60
                b.place(x=510, y=y_co)
                self.clients_online_labels[user_id] = (b, y_co)
                self.y -= 60
    def insert_emoji(self, x):
        self.entry.insert("end-1c", x.widget['text'])
    def first_screen(self):
        self.destroy()
        self.parent.geometry(f"550x400+{self.parent.x_co}+{self.parent.y_co}")
        self.parent.first_frame.pack(fill="both", expand=True)
        self.window = None

if __name__ == "__main__":
    FirstScreen()
    