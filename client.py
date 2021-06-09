import socket
import sys
import threading
import time

port=9998
loop_count=300
sleep_time = 0.000025 #seconds   # High load = 0 us  - Low Load = 25 us

vm_ip_list=[]
count=0
dead_counter=0


# creating object of socket
def create_socket():
    try:
        global server_socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(5)
    except socket.error as msg:
        print("Socket creation error: "+str(msg))
# binding the socket
def bind_socket():
    try:
        #print("Binding the port: "+str(port))
        server_socket.bind(('', port))
        server_socket.listen(10)
    except socket.error as msg:
        print("Error binding with port:"+str(port)+" Please exit and try other port")
        time.sleep(5)
        bind_socket()
# Handling connections from multiple clients and saving to a list
# Closing previous connections if any
def accepting_connections():
    '''
    This is a function for a Thread which will run for the entire life or program and accept connections on the provided port.
    Then it'll also process according to the received response.
    '''
    global thread_run
    global vm_ip_list
    thread_run=True
    while thread_run:
        try:
            conn, address = server_socket.accept()
            client_response = str(conn.recv(1024).decode("utf-8"))
            
            if "Add" in client_response:
                client_response =  client_response.split(" ")[1]
                print('Add IP received from monitor program: '+client_response)
                #print("Add: "+client_response)
                if client_response not in vm_ip_list:
                    vm_ip_list.append(client_response)

            elif "Delete" in client_response:
                client_response =  client_response.split(" ")[1]
                print('Delete IP received from monitor program: '+client_response)
                #print("Delete: "+client_response)
                if client_response in vm_ip_list:
                    vm_ip_list.remove(client_response)

            conn.send(bytes("IP received to Client: "+client_response,"utf-8"))
            conn.close()
        except socket.error as msg :
            if "timed out" not in str(msg):
                print("accepting_connections() Error: "+ str(msg))
# Socket Functionalities End --------------------------



def listening_connections():
    create_socket()
    bind_socket()
    accepting_connections()



def start_shell():
    global thread_run
    thread_run=True
    global loop_count
    global sleep_time
    global count
    time.sleep(3)
    print("\n\n\t\tNormal Load Active ...")
    while thread_run:
        cmd=input("shell> ")
        
        if 'exit' in cmd:
            thread_run=False
            print("\n\n\t\tExiting Client...\n\n")
            break
        if 'list' in cmd:
            print("\n\n\t\tServer IPs: "+str(vm_ip_list), end="\n\n\n")
        elif 'loop' in cmd:
            split=cmd.split(' ')
            if len(split) == 2 :
                temp=loop_count
                loop_count=int(cmd.split(' ')[1])
                print("\n\n\t\tLoop count changed from: " +str(temp)+ " to: "+str(loop_count), end="\n\n\n")
        elif 'time' in cmd:
            split=cmd.split(' ')
            if len(split) == 2 :
                temp=sleep_time
                sleep_time=float(cmd.split(' ')[1])/1000000
                print('\n\n\t\tRequest time changed from: '+str(temp*1000000)+" μs "+'to: '+str(sleep_time*1000000)+" μs", end="\n\n\n")
        elif 'th' in cmd:
            print("\n\n\t\tCalculating Throughput ...")
            count_init=count
            time.sleep(5)
            count_fin=count
            print("\t\tThroughput is: " + str(int((count_fin-count_init)/5))+ " reqs/sec", end="\n\n\n")
        elif 'normal' in cmd:
            print("\n\n\t\tNormal Load Active ...")
            loop_count=300
            sleep_time = 0.000025
        elif 'high' in cmd:
            print("\n\n\t\tHigh Load Active ...")
            loop_count=300
            sleep_time = 0
        elif 'low' in cmd:
            print("\n\n\t\tLow Load Active ...")
            loop_count=100
            sleep_time = 0.000025
        
        else:
            print("\n\n\t\tCommand not recognised", end="\n\n\n")






# Liveness Functions ---------------------------------
def load_generator():
    '''
    This function will be run by an independent thread which will send requests to clients present in vm_ip_list.
    '''
    global thread_run
    global count
    global dead_counter
    global loop_count
    global vm_ip_list
    thread_run=True
    global myip

    while thread_run:
        # if len(vm_ip_list) == 0:
        #     thread_run=False
        for peer in vm_ip_list:
            try:
                client_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client_socket.settimeout(1.0)
                client_socket.sendto(bytes(str(loop_count)+" "+str(count), "utf-8"), (peer,9999))
                count+=1
            except socket.error as msg:
                print("Server not responding: "+str(dead_counter)+" "+ str(msg))
                dead_counter+=1
                if(dead_counter>=3):
                    print("Deleting IP from the list: "+ str(peer))
                    vm_ip_list.remove(peer)
                    dead_counter=0
        time.sleep(sleep_time)




#Custom shell Thread
t1= threading.Thread(target=start_shell)
t1.daemon=True
t1.start()
#Peer Listening Thread
t2=threading.Thread(target=listening_connections)
t2.daemon=True
t2.start()

#Liveness Thread
t3=threading.Thread(target=load_generator)
t3.daemon=True
t3.start()


t3.join()