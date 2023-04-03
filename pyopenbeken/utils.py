import threading

class ThreadManager:
    def __init__(self):
        self.threads = []

    def start_thread(self, target, args=()):
        t = threading.Thread(target=target, args=args)
        t.daemon = True
        t.start()
        self.threads.append(t)

    def join_all(self):
        for t in self.threads:
            t.join()

import requests
import socket
import platform
import subprocess

class networkScan:
    def __init__(self, local_ip=None,ip_list=None,silent=True):
        self.is_silent  = silent
        if local_ip is None:
            local_ip    = self.__get_local_ip()
        self.local_ip   = local_ip
        self.network_ip = self.__get_network_ip()
        if ip_list is None:
            ip_list     = []        
        self.ip_list    = ip_list
        self.bkn_ips    = []
        
    def slnt_print(self,message):
        if not self.is_silent:
            print(message)
            
    def __get_local_ip(self):
        """Get the IP address of the current machine."""
        self.local_ip  = (socket.gethostbyname_ex(socket.gethostname())[2][-1])
        return self.local_ip

    def __get_network_ip(self):
        """Get the IP address of the local network."""
        self.network_ip = '.'.join(self.local_ip.split('.')[:-1]) + '.'
        return self.network_ip

    def get_used_ips(self,ip_list=None):
        """Get a list of used IP addresses on the local network."""
        if ip_list is None:
            ip_list = self.ip_list
        if platform.system() == 'Windows':
            ping_cmd = ['ping', '-n', '1', '-w', '500']
        else:
            ping_cmd = ['ping', '-c', '1', '-W', '1']
        used_ips = []
        for i in range(1, 255):
            ip = self.network_ip + str(i)
            if ip not in ip_list:
                try:
                    subprocess.check_output(ping_cmd+[ip])
                    used_ips.append(ip)
                    if len(ip_list)!=0:
                        self.slnt_print(f'New IP: {ip}')
                except subprocess.CalledProcessError:
                    pass
            else:
                used_ips.append(ip)
        self.ip_list = used_ips
        return used_ips
    
    def obkn_api_scan(self,ip_list=None):
        """Get a list of OpenBeken devices based on a list of IP addresses."""
        self.bkn_ips = []
        if ip_list is None:
            ip_list = self.ip_list
        requests.adapters.DEFAULT_RETRIES = 1
        for ip in ip_list:
            try:
                board_info = requests.get(f'http://{ip}/api/info')#.json()
                if board_info.status_code == 200:
                    self.bkn_ips.append(ip)
            except:
                pass
        return self.bkn_ips            