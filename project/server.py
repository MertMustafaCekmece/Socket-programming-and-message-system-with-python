import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import os

HOST = "127.0.0.1"
PORT = 12345
LOG_FILE = "chat_logs.txt"

clients = {}
lock = threading.Lock()

class ServerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sunucu Arayüzü")

        self.chat_display = scrolledtext.ScrolledText(self.root, width=50, height=20, state="disabled")
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

        self.message_frame = tk.Frame(self.root)
        self.message_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.message_entry = tk.Entry(self.message_frame, width=40)
        self.message_entry.grid(row=0, column=0, padx=10, pady=5)

        self.send_button = tk.Button(self.message_frame, text="Mesaj Gönder", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=10, pady=5)

        self.private_frame = tk.Frame(self.root)
        self.private_frame.grid(row=2, column=0, padx=10, pady=10, columnspan=2, sticky="ew")

        self.private_label = tk.Label(self.private_frame, text="Kullanıcı Adı")
        self.private_label.grid(row=0, column=0, padx=10, pady=5)

        self.private_user_entry = tk.Entry(self.private_frame, width=20)
        self.private_user_entry.grid(row=0, column=1, padx=10, pady=5)

        self.private_message_label = tk.Label(self.private_frame, text="Private Mesaj")
        self.private_message_label.grid(row=1, column=0, padx=10, pady=5)

        self.private_message_entry = tk.Entry(self.private_frame, width=40)
        self.private_message_entry.grid(row=1, column=1, padx=10, pady=5)

        self.private_send_button = tk.Button(self.root, text="Private Mesaj Gönder", command=self.send_private_message)
        self.private_send_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.log_button = tk.Button(self.root, text="Log Kayıtları", command=self.show_logs)
        self.log_button.grid(row=4, column=0, columnspan=2, pady=10)

    def update_chat(self, message):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.config(state="disabled")
        self.chat_display.yview(tk.END)

        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(message + "\n")

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            if message.startswith("/private"):
                _, target_user, private_msg = message.split(" ", 2)
                send_private_message("Sunucu", target_user, private_msg, self)
                self.update_chat(f"[Sunucu] {target_user} adlı kullanıcıya private mesaj gönderildi.")
            elif message.startswith("/server"):
                server_msg = message[len("/server "):].strip()
                self.update_chat(f"[Sunucu]: {server_msg}")
                broadcast(f"[Sunucu]: {server_msg}", None, self, is_server=True)
            else:
                broadcast(f"[Sunucu]: {message}", None, self)
            self.message_entry.delete(0, "end")

    def send_private_message(self):
        target_user = self.private_user_entry.get().strip()
        message = self.private_message_entry.get().strip()
        if target_user and message:
            send_private_message("Sunucu", target_user, message, self)
        else:
            self.update_chat("Private mesaj göndermek için kullanıcı adı ve mesaj girin.")

    def show_logs(self):
        if os.path.exists(LOG_FILE):
            log_window = tk.Toplevel(self.root)
            log_window.title("Log Kayıtları")

            log_display = scrolledtext.ScrolledText(log_window, width=50, height=20, state="normal")
            log_display.pack(padx=10, pady=10)

            with open(LOG_FILE, "r", encoding="utf-8") as file:
                logs = file.read()
                log_display.insert(tk.END, logs.strip())
                log_display.config(state="disabled")
        else:
            self.update_chat("Log dosyası bulunamadı.")

def handle_client(client_socket, username, ui):
    try:
        broadcast(f"{username} sohbete katıldı.", None, ui)
        while True:
            message = client_socket.recv(1024).decode('utf-8').strip()
            if not message:
                break

            if message.startswith("/private"):
                try:
                    _, target_user, private_msg = message.split(" ", 2)
                    send_private_message(username, target_user, private_msg, ui)
                except ValueError:
                    client_socket.send("Hatalı private mesaj formatı! Doğru format: /private <kullanıcı adı> <mesaj>\n".encode('utf-8'))
            elif message.startswith("/server"):
                server_msg = message[len("/server "):].strip()
                ui.update_chat(f"[{username} -> Sunucu]: {server_msg}")
                broadcast(f"[{username} -> Sunucu]: {server_msg}", client_socket, ui, is_server=True)
            else:
                broadcast(f"{username}: {message}", client_socket, ui)
    except (ConnectionResetError, ConnectionAbortedError):
        pass
    finally:
        with lock:
            print(f"{username} bağlantıyı kesti.")
        clients.pop(username, None)
        broadcast(f"{username} sohbetten ayrıldı.", None, ui)
        client_socket.close()

def broadcast(message, sender_socket, ui, is_server=False):
    if is_server:
        ui.update_chat(f"{message.strip()}")
    else:
        ui.update_chat(f"{message.strip()}")

    for client_socket in clients.values():
        if client_socket != sender_socket and not is_server:
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                pass

def send_private_message(from_user, to_user, message, ui=None):
    target_socket = clients.get(to_user)
    if target_socket:
        try:
            target_socket.send(f"[Private] {from_user}: {message}".encode('utf-8'))
            if ui:
                ui.update_chat(f"[{from_user} -> {to_user}]: {message}")
        except:
            pass
    else:
        if from_user in clients:
            sender_socket = clients[from_user]
            sender_socket.send(f"{to_user} adlı kullanıcı bulunamadı.\n".encode('utf-8'))

def server_chat(ui):
    while True:
        message = input("Sunucu mesajı (komut: /private <kullanıcı adı> <mesaj>): ").strip()
        if message.startswith("/private"):
            try:
                _, target_user, private_msg = message.split(" ", 2)
                send_private_message("Sunucu", target_user, private_msg, ui)
            except ValueError:
                ui.update_chat("Hatalı private mesaj formatı! Doğru format: /private <kullanıcı adı> <mesaj>\n")
        elif message.startswith("/server"):
            server_msg = message[len("/server "):].strip()
            ui.update_chat(f"[Sunucu]: {server_msg}")
            broadcast(f"[Sunucu]: {server_msg}", None, ui, is_server=True)
        else:
            broadcast(f"[Sunucu]: {message}", None, ui, is_server=True)

def start_server(ui):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    with lock:
        print(f"Sunucu {HOST}:{PORT} üzerinde çalışıyor...")
        ui.update_chat(f"Sunucu {HOST}:{PORT} üzerinde çalışıyor...\n")

    threading.Thread(target=server_chat, args=(ui,), daemon=True).start()

    while True:
        client_socket, client_address = server.accept()
        client_socket.send("Kullanıcı adınızı girin: ".encode('utf-8'))
        username = client_socket.recv(1024).decode('utf-8').strip()

        if username in clients:
            client_socket.send("Bu kullanıcı adı zaten kullanılıyor.\n".encode('utf-8'))
            client_socket.close()
            continue

        clients[username] = client_socket
        with lock:
            print(f"{username} ({client_address}) bağlandı.")
            ui.update_chat(f"{username} ({client_address}) bağlandı.\n")
        thread = threading.Thread(target=handle_client, args=(client_socket, username, ui))
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    server_ui = ServerUI(root)
    threading.Thread(target=start_server, args=(server_ui,), daemon=True).start()
    root.mainloop()
