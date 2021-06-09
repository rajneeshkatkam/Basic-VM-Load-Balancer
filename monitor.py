import libvirt
import sys
import time
import threading
import socket


thread_run=True
dom2=None

vm_list=[]
vm_flag=True
vm2_first_run =  False
ip_failed=0


def libconnectHost():
    global thread_run
    try:
        conn = libvirt.open('qemu:///system')
        return conn
    except libvirt.libvirtError:
        thread_run=False
        print('Failed to open connection to the hypervisor')
        return None

def libconnectDomain(name):
    global thread_run
    try:
        dom = conn.lookupByName(name)
        return dom
    except libvirt.libvirtError:
        print(name+' not Present')
        thread_run=False
        return None


def getIP(dom):
    global thread_run
    try:
        ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0)
        dom_ip=str(ifaces['enp1s0']['addrs'][0]['addr'])
        return dom_ip
    except libvirt.libvirtError:
        print(dom.name() + ' not available for IP..Retrying')
        time.sleep(2)
        getIP(dom)



def get_cpu_percentage(dom):
    global thread_run
    try:
        stats = dom.getCPUStats(True)
        guest_fin=stats[0]['cpu_time']/1000000000.-stats[0]['system_time']/1000000000.-stats[0]['user_time']/1000000000.
        #guest_fin=stats[0]['cpu_time']/1000000000.
        sleep_time=1
        cpu_percent=0.00
        loop_cycle=4
        for i in range(loop_cycle):
            guest_init=guest_fin
            time.sleep(sleep_time)
            stats = dom.getCPUStats(True)
            guest_fin=stats[0]['cpu_time']/1000000000.-stats[0]['system_time']/1000000000.-stats[0]['user_time']/1000000000.
            #guest_fin=stats[0]['cpu_time']/1000000000.
            cpu_percent+=(100*(guest_fin - guest_init)/sleep_time)
        
        return round(max(cpu_percent/loop_cycle, 0.00), 1)
    except:
        print(dom.name()+" not running. Exiting ...")
        thread_run=False
        exit(0)




def send_ip(dom):
    global ip_failed
    if(thread_run == False):
        print("Exiting Monitor Program...")
        exit(0)

    ip=getIP(dom)
    if ip == None:
        ip_failed+=1
        print('Retry getting IP..')
        time.sleep(2)
        if ip_failed<5:
            send_ip(dom)
        else:
            ip_failed=0
    try:
        client_socket=socket.socket()
        client_socket.connect(('',9998))
        client_socket.send(bytes("Add "+ip, "utf-8"))
        print("IP sent to Client: "+ str(ip))
        client_socket_response=str(client_socket.recv(1024).decode("utf-8"))
        client_socket.close()
    except socket.error as msg:
        ip_failed+=1
        print('\nSending Add IP to Client Failed. Client is not running. Retrying...')
        time.sleep(2)
        if ip_failed<5:
            send_ip(dom)
        else:
            ip_failed=0



def delete_ip(dom):
    global ip_failed
    if(thread_run == False):
        print("Exiting Monitor Program...")
        exit(0)

    ip=getIP(dom)
    if ip == None:
        ip_failed+=1
        print('Retry deleting IP..')
        time.sleep(2)
        if ip_failed<5:
            delete_ip(dom)
        else:
            ip_failed=0
    try:
        client_socket=socket.socket()
        client_socket.connect(('',9998))
        client_socket.send(bytes("Delete: "+ip, "utf-8"))
        print("Delete IP sent to Client: "+ str(ip))
        client_socket_response=str(client_socket.recv(1024).decode("utf-8"))
        client_socket.close()
    except socket.error as msg:
        ip_failed+=1
        print('\nSending Delete IP to Client Failed. Client is not running. Retrying...')
        time.sleep(2)
        if ip_failed<5:
            delete_ip(dom)
        else:
            ip_failed=0



def monitor_VMs():
    global thread_run
    global dom2
    thread_run=True
    global vm_flag
    global vm2_first_run
    run_count = 0
    while thread_run:
        for dom in vm_list:

            if dom.name()==dom2.name() and vm2_first_run and run_count<=3:
                if run_count>=3:
                    print("Spawning "+dom2.name()+" Completed !!!")
                    vm2_first_run=False
                #print("\n\n\n\n Continuing... \n\n\n\n")
                run_count+=1
                continue

            curr_cpu_usage = get_cpu_percentage(dom)
            print('CPU %'+' of '+dom.name()+ ' : '+str(curr_cpu_usage))

            if vm_flag == False and dom.name() == "Lubuntu-1" and curr_cpu_usage<=35 and len(vm_list) == 2:
                
                new_cpu_usage=get_cpu_percentage(dom)
                print('\nCPU %'+' of '+dom.name()+ ' : '+str(new_cpu_usage))
                if new_cpu_usage<=35:
                    print("\nLow CPU usage on " + dom.name())

                    delete_ip(dom2)
                    dom2.destroy()
                    vm_list.remove(dom2)
                    print("Stopping " + dom2.name() + " ...\n")
                    time.sleep(2)
                    print("Stopped " + dom2.name() + " !!")
                    vm_flag=True


            elif curr_cpu_usage >=80. :
                new_cpu_usage=get_cpu_percentage(dom)
                print('\nCPU %'+' of '+dom.name()+ ' : '+str(new_cpu_usage))
                if vm_flag and new_cpu_usage >= 80 and len(vm_list) < 2:
                    print("!! " + dom.name() + " Overloaded !!")
                    if dom2.isActive() == False:
                        try:
                            id =  dom2.create()
                            if id < 0:
                                print('Unable to create guest ', file=sys.stderr)
                            
                        except:
                            print(dom2.name()+' already running')
                            pass
                    else:
                        vm_flag=False
                    
                    if vm_flag:
                        print("Spawning "+dom2.name()+" ...")
                        time.sleep(20)
                    
                    send_ip(dom2)
                    vm_list.append(dom2)
                    vm_flag=False
                    vm2_first_run=True
                    run_count = 0


        print("")


def start_shell():

    global thread_run
    thread_run=True
    while thread_run:
        cmd=input()
        if 'exit' in cmd:
            thread_run=False
            print("Exiting Monitor Program...")
            break
        else:
            print("Command not recognised")




conn = libconnectHost()
dom = libconnectDomain("Lubuntu-1")
dom2 = libconnectDomain("Lubuntu-2")

if dom.isActive() == False:
    print("No Domain running. Starting "+ dom.name() + "...")
    try:
        id =  dom.create()
        if id < 0:
            print('Unable to create guest ', file=sys.stderr)
        
    except:
        print(dom.name()+' already running')
        vm_flag=False
        pass
    time.sleep(15)
                    
print("\n"+dom.name()+ " Running !!\n")

send_ip(dom)
vm_list.append(dom)
dom_ip = getIP(dom)


#Custom shell Thread
t1= threading.Thread(target=start_shell)
t1.daemon=True
t1.start()

#Peer Listening Thread
t2=threading.Thread(target=monitor_VMs)
t2.daemon=True
t2.start()

t2.join()
t1.join()

