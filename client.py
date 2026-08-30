import socket

HEADER, PORT, FORMAT = 64, 5050, "utf-8"
SERVER = "192.168.1.6"    
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))

def send(msg):
    data = msg.encode(FORMAT)
    client.send(str(len(data)).encode(FORMAT).ljust(HEADER, b" "))
    client.send(data)

def recv():
    size = client.recv(HEADER).decode(FORMAT).strip()
    if not size:
        return None
    return client.recv(int(size)).decode(FORMAT)

send(input("Enter your unique name: "))

while True:
    msg = recv()
    if msg is None:
        print("Disconnected from server.")
        break

    code, phrase, text = msg.split("|", 2)
    print(f"[{code} {phrase}] {text}")

    if code in ("403", "409", "230"):
        break
    if code == "300":
        send(input("Ready? (y/n): ").lower())
    elif code == "220":
        send(input("Your move (rock/paper/scissors): ").lower())
    elif code == "221":
        send(input("Replay (rock/paper/scissors): ").lower())
