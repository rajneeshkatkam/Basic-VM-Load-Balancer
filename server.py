import socket
import sys
import time
import threading


port=9999
# shell thread functions below
def start_shell():
    global thread_run
    thread_run=True
    while thread_run:
        cmd=input("shell> ")
        if 'exit' in cmd:
            thread_run=False
            print("Exiting Server...")
            break
        else:
            print("Command not recognised")




# creating object of socket
def create_socket():
    try:
        global s
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(5)
    except socket.error as msg:
        print("Socket creation error: "+str(msg))
# binding the socket
def bind_socket():
    try:
        print("Binding the port: "+str(port))
        s.bind(('', port))
        #s.listen(10)
    except socket.error as msg:
        print("Socket Binding error: "+str(msg))
        time.sleep(5) # Time to sleep before reattempting the bind connection
        bind_socket()




def accepting_connections():

    global thread_run
    thread_run=True
    while thread_run:
        try:
            peer_response, address = s.recvfrom(1024)
            peer_response=str(peer_response.decode("utf-8"))
            loop_count=peer_response.split(' ')[0]
            print(peer_response, end="\r")
            sum=0
            try:
                for i in range(int(loop_count)):
                    sum+=i
            except :
                pass
        except socket.error as msg :
            if "timed out" not in str(msg):
                print("accepting_connections() Error: "+ str(msg))
            continue


def listening_connections():
    create_socket()
    bind_socket()
    accepting_connections()


#Creating Threads for listening and other tasks
t1= threading.Thread(target=start_shell)
t1.daemon=True
t1.start()
t2=threading.Thread(target=listening_connections)
t2.daemon=True
t2.start()
t1.join()
t2.join()