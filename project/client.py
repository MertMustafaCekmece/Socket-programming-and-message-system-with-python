import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

HOST = "127.0.0.1"
PORT = 12345

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.username = None

        self.root = tk.Tk()
        self.root.title("Chat Client")
        self.root.geometry("400x500")

        self.username_label = tk.Label(self.root, text="Kullanıcı Adı:")
        self.username_label.pack(pady=5)

        self.username_entry = tk.Entry(self.root, width=30)
        self.username_entry.pack(pady=5)

        self.connect_button = tk.Button(self.root, text="Bağlan", command=self.connect_to_server)
        self.connect_button.pack(pady=5)

        self.messages_box = scrolledtext.ScrolledText(self.root, state="disabled", width=50, height=20)
        self.messages_box.pack(pady=5)

        self.message_entry = tk.Entry(self.root, width=30)
        self.message_entry.pack(pady=5)

        self.send_button = tk.Button(self.root, text="Gönder", command=self.send_message)
        self.send_button.pack(pady=5)

        self.private_message_button = tk.Button(self.root, text="Private Mesaj Gönder", command=self.send_private_message)
        self.private_message_button.pack(pady=5)

    def connect_to_server(self):
        self.username = self.username_entry.get().strip()
        if not self.username:
            messagebox.showerror("Hata", "Lütfen bir kullanıcı adı girin!")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            self.client_socket.send(self.username.encode("utf-8"))
            
            self.messages_box.config(state="normal")
            self.messages_box.insert("end", "Sunucuya bağlandınız!\n")
            self.messages_box.config(state="disabled")

            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Bağlantı Hatası", str(e))

    def receive_messages(self):
        try:
            while True:
                message = self.client_socket.recv(1024).decode("utf-8")
                self.messages_box.config(state="normal")
                self.messages_box.insert("end", message + "\n")
                self.messages_box.yview("end")
                self.messages_box.config(state="disabled")
        except Exception as e:
            self.messages_box.config(state="normal")
            self.messages_box.insert("end", f"Bağlantı kesildi: {str(e)}\n")
            self.messages_box.config(state="disabled")

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            try:
                self.client_socket.send(message.encode("utf-8"))
                self.messages_box.config(state="normal")
                self.messages_box.insert("end", f"[Siz]: {message}\n")
                self.messages_box.yview("end")
                self.messages_box.config(state="disabled")
                self.message_entry.delete(0, "end")
            except Exception as e:
                messagebox.showerror("Hata", f"Mesaj gönderilemedi: {str(e)}")

    def send_private_message(self):
        target_user = simpledialog.askstring("Private Mesaj", "Hedef kullanıcı adını girin:")
        private_message = self.message_entry.get().strip()
        if target_user and private_message:
            try:
                message = f"/private {target_user} {private_message}"
                self.client_socket.send(message.encode("utf-8"))
                self.messages_box.config(state="normal")
                self.messages_box.insert("end", f"[Siz -> {target_user}]: {private_message}\n")
                self.messages_box.yview("end")
                self.messages_box.config(state="disabled")
                self.message_entry.delete(0, "end")
            except Exception as e:
                messagebox.showerror("Hata", f"Mesaj gönderilemedi: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()
