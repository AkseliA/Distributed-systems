import socket
import threading
import sys


#IP = "127.0.0.1"
PORT = 8000


def receive_message(conn):
    try:
        while True:
            msg = conn.recv(256).decode("utf-8")
            if(msg):
                print(f"{msg}")

    except Exception as e:
        conn.close()


def send_message(conn):
    try:
        while True:
            message = input()
            conn.send(message.encode("utf-8"))
            if(message == "/disconnect"):
                conn.close()
                sys.exit()

    except Exception as e:
        conn.close()


def main():
    while True:
        IP = input("Enter server IP: ")
        username = input("Enter your username: ")
        channelNr = input("Enter channel number (1-2): ")
        if(username and channelNr == "1" or channelNr == "2"):
            break
    try:
        socketClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketClient.connect((IP, PORT))

        # Threads for receiving and sending messages
        threading.Thread(target=receive_message, args=[socketClient]).start()
        threading.Thread(target=send_message, args=[socketClient]).start()

        # Send username and channel nr to server
        userInfo = username + " " + channelNr
        socketClient.send(userInfo.encode("utf-8"))
    except Exception as e:
        sys.exit("Try again")


if __name__ == '__main__':
    main()
