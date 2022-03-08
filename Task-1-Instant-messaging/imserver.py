import socket
import threading
import sys


IP = "127.0.0.1"
PORT = 8000
clientList = []  # {"conn" : conn, "username" : str, "channel" : int}


def new_client(conn, addr):
    print(f"New connection: {addr}.")
    clientInfo = conn.recv(128).decode("utf-8").split(" ")
    username = clientInfo[0]
    userCh = int(clientInfo[1])
    clientList.append(
        {"conn": conn, "username": username, "channel": userCh})

    broadcast_msg(f"{username} connected to server.", 999, conn)
    conn.send("Start chatting or type /help to view commands.".encode("utf-8"))

    # Listening to connected client
    try:
        while True:
            msg = conn.recv(256).decode("utf-8")
            if(msg):
                print(addr, msg)

                # Client commands
                if(msg == "/disconnect"):
                    remove_conn(conn)
                    broadcast_msg(f"{username} disconnected.", 999, None)
                    break
                elif(msg == "/help"):
                    conn.send(
                        f"Commands:\n\t/disconnect to disconnect from the server\n\t/channel [x] to switch channel (0-1)\n\t/users to display online users\n\t/pm [username] [content] to send a private message".encode("utf-8"))
                elif("/channel" in msg):
                    destination = int(msg.split(" ")[1])
                    if(userCh != destination):
                        for client in clientList:
                            if(conn == client["conn"] and client["channel"] != destination):
                                client["channel"] = destination
                                conn.send(
                                    f"You joined ch-{destination}.".encode("utf-8"))
                                userCh = destination

                elif(msg == "/users"):
                    conn.send("Current users:".encode("utf-8"))
                    for client in clientList:
                        conn.send(
                            f"\tCh: {client['channel']} - {client['username']}\n".encode("utf-8"))

                elif("/pm" in msg):
                    parts = msg.split(" ")
                    try:
                        for client in clientList:
                            if parts[1] == client["username"]:
                                client["conn"].send(
                                    f"PM from {username}: {' '.join(parts[2:])}".encode("utf-8"))
                    except:
                        conn.send("Error sending pm".encode("utf-8"))
                else:
                    broadcast_msg(f"{username}: {msg}", userCh, conn)
    except Exception as e:
        remove_conn(conn)
    conn.close()


def remove_conn(conn):
    for i in range(len(clientList)):
        if(clientList[i]["conn"] == conn):
            del clientList[i]


def broadcast_msg(msg, channelNr, conn):
    for client in clientList:
        # If conn, broadcast to everyone on same channel except the sender
        if(conn and client["conn"] != conn and channelNr == client["channel"]):
            client["conn"].send(msg.encode("utf-8"))

        # If !conn, broadcast to everyone
        elif(conn == None):
            client["conn"].send(msg.encode("utf-8"))


def main():
    print(f"Server starting...")

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((IP, PORT))  # Binds the socket to 127.0.0.1:8000

    serverSocket.listen()
    print(f"Server running on {IP}:{PORT}")
    try:
        while True:
            conn, addr = serverSocket.accept()
            newThread = threading.Thread(target=new_client, args=(conn, addr))
            newThread.start()

    except Exception as e:
        print(e)
        serverSocket.close()
        sys.exit()


if __name__ == '__main__':
    main()
