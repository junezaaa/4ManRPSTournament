import socket, threading, random, queue

HEADER, PORT, FORMAT, MAX = 64, 5050, "utf-8", 4
IP = socket.gethostbyname(socket.gethostname())
ADDR = (IP, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

players, inboxes = {}, {}
lock = threading.Lock()

def send(conn, name, code, phrase, msg=""):
    data = f"{code}|{phrase}|{msg}".encode(FORMAT)
    conn.send(str(len(data)).encode(FORMAT).ljust(HEADER, b" "))
    conn.send(data)
    print(f"[SERVER -> {name}] {code} {phrase} | {msg}")

def broadcast(code, phrase, msg=""):
    for name, conn in list(players.items()):
        send(conn, name, code, phrase, msg)

def recv(conn):
    size = conn.recv(HEADER).decode(FORMAT).strip()
    if not size:
        return None
    return conn.recv(int(size)).decode(FORMAT)

def winner(a, b):
    if a == b:
        return 0
    return 1 if (a, b) in [("rock","scissors"),
                            ("scissors","paper"),
                            ("paper","rock")] else -1

def match(a, b):
    send(players[a], a, 220, "MATCH", f"vs {b} - choose rock/paper/scissors")
    send(players[b], b, 220, "MATCH", f"vs {a} - choose rock/paper/scissors")

    while True:
        x = inboxes[a].get().lower()
        y = inboxes[b].get().lower()

        if x not in ("rock", "paper", "scissors") or y not in ("rock", "paper", "scissors"):
            send(players[a], a, 400, "BAD_REQUEST", "Invalid move. Use rock/paper/scissors.")
            send(players[b], b, 400, "BAD_REQUEST", "Invalid move. Use rock/paper/scissors.")
            send(players[a], a, 220, "MATCH", f"vs {b} - choose again")
            send(players[b], b, 220, "MATCH", f"vs {a} - choose again")
            continue

        result = winner(x, y)
        if result == 0:
            send(players[a], a, 221, "TIE", f"Draw vs {b} - replay")
            send(players[b], b, 221, "TIE", f"Draw vs {a} - replay")
            continue

        w, l = (a, b) if result == 1 else (b, a)
        send(players[w], w, 222, "WIN", f"You beat {l}")
        send(players[l], l, 223, "LOSE", f"You lost to {w}")
        return w, l

def tournament():
    names = list(players)
    for n in names:
        send(players[n], n, 300, "PROMPT", "Would you like to start the tournament? [y/n]")

    answers = {n: inboxes[n].get().lower() for n in names}
    if not all(x == "y" for x in answers.values()):
        broadcast(100, "CONTINUE", "Everyone isn't ready. Tournament postponed.")
        return

    random.shuffle(names)
    broadcast(201, "STARTED", "Tournament started!")

    w1, l1 = match(names[0], names[1])
    w2, l2 = match(names[2], names[3])
    champion, second = match(w1, w2)
    third, fourth = match(l1, l2)

    broadcast(230, "LEADERBOARD",
              f"1st:{champion}  2nd:{second}  3rd:{third}  4th:{fourth}")
    print("[SERVER] Tournament finished.")

def client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")
    with lock:
        if len(players) >= MAX:
            send(conn, "?", 403, "FORBIDDEN", "Server full (maximum 4 players).")
            conn.close()
            return

    name = recv(conn)
    with lock:
        if not name or name in players:
            send(conn, "?", 409, "CONFLICT", "Name already taken.")
            conn.close()
            return

        players[name] = conn
        inboxes[name] = queue.Queue()
        send(conn, name, 200, "OK", f"Joined as {name}")
        broadcast(101, "STATUS", f"{len(players)}/4 players joined.")
        ready = len(players) == MAX

    if ready:
        threading.Thread(target=tournament, daemon=True).start()

    while True:
        msg = recv(conn)
        if msg is None:
            break
        print(f"[CLIENT {name}] {msg}")
        inboxes[name].put(msg)

def start():
    server.listen()
    print(f"[LISTENING] Server running on {IP}:{PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=client, args=(conn, addr), daemon=True).start()

print("Server starting...")
start()
