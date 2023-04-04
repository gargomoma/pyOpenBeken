def chunkArray(ArrObj=[], length=1):
    return list(ArrObj[0+i:length+i] for i in range(0, len(ArrObj), length))

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

    def ping(self,ip_addr):
        if platform.system() == 'Windows':
            ping_cmd = ['ping', '-n', '1', '-w', '500']
        else:
            ping_cmd = ['ping', '-c', '1', '-W', '1']
            
        try:
            subprocess.check_output(ping_cmd+[ip_addr])
            return True
        except subprocess.CalledProcessError:
            pass
            return False
    def ping_obk(self,ip_addr='',retries=1):
        requests.adapters.DEFAULT_RETRIES = retries
        try:
            board_info = requests.get(f'http://{ip_addr}/api/info')#.json()
            if board_info.status_code == 200:
                return True
        except:
            pass
            return False
    
    def __mt_ping(self,ip_chunk):
        for ip in ip_chunk:
            if self.ping(ip):
                self.temp_mt_ips.append(ip)
        return True
    
    def __mt_ping_obk(self,ip_chunk):
        for ip in ip_chunk:
            if self.ping_obk(ip):
                self.temp_mt_ips.append(ip)
        return True
    
    def get_network_ips(self,ip_list=None,ip_chunks_size = 50):
        """Get a list of used IP addresses on the local network."""
        manager = ThreadManager()
        if ip_list is None:
            ip_list = self.ip_list

        ip_range = [ self.network_ip + str(i) for i in range(1, 255) ]
        ip_range_chunks = chunkArray( ip_range, ip_chunks_size ) #255/50 = 6 chunks
        self.temp_mt_ips = []
        
        for ip_chunk in ip_range_chunks:
            manager.start_thread(target=self.__mt_ping , args=( ip_chunk, ) )
        manager.join_all()
        
        self.ip_list = self.temp_mt_ips
        del self.temp_mt_ips
        return self.ip_list    
    
    #def get_used_ips(self,ip_list=None):
    #    """Get a list of used IP addresses on the local network."""
    #    if ip_list is None:
    #        ip_list = self.ip_list
    #    used_ips = []
    #    for i in range(1, 255):
    #        ip = self.network_ip + str(i)
    #        if ip not in ip_list and self.ping(ip):
    #            used_ips.append(ip)                
    #        else:
    #            used_ips.append(ip)
    #    self.ip_list = used_ips
    #    return used_ips    
    
    def obkn_api_scan(self,ip_list=None,ip_chunks_size=4):
        """Get a list of OpenBeken devices based on a list of IP addresses."""
        self.bkn_ips = []
        manager = ThreadManager()
        if ip_list is None:
            ip_list = self.ip_list
        ip_range_chunks = chunkArray( ip_list, ip_chunks_size ) #255/50 = 6 chunks
        self.temp_mt_ips = []
        
        for ip_chunk in ip_range_chunks:
            manager.start_thread(target=self.__mt_ping_obk , args=( ip_chunk, ) )
        manager.join_all()
        
        self.bkn_ips = self.temp_mt_ips
        del self.temp_mt_ips
        return self.bkn_ips
