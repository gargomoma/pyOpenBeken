def chunkArray(ArrObj=[], length=1):
    """
    Splits an array into chunks of a specified length.

    Args:
    - ArrObj (list): The array to be chunked. Default is an empty list.
    - length (int): The length of each chunk. Default is 1.

    Returns:
    - A list of chunks of the specified length.

    This function takes an array and splits it into chunks of the specified length.
    """    
    return list(ArrObj[0+i:length+i] for i in range(0, len(ArrObj), length))

import threading

class ThreadManager:
    """
    A class to manage threads.

    This class provides methods to start threads and join them.
    """    
    def __init__(self):
        self.threads = []

    def start_thread(self, target, args=()):
        """
        Starts a new thread.

        Args:
        - target (function): The target function to be run in the new thread.
        - args (tuple): The arguments to be passed to the target function. Default is an empty tuple.

        This method starts a new thread with the specified target function and arguments.
        """        
        t = threading.Thread(target=target, args=args)
        t.daemon = True
        t.start()
        self.threads.append(t)

    def join_all(self):
        """
        Joins all threads.

        This method waits for all the threads managed by this object to finish.
        """        
        for t in self.threads:
            t.join()

    #TODO:: def check_active_threads()
            
import requests
import socket
import platform
import subprocess

class networkScan:
    """
    A class to scan a local network for devices.

    This class provides methods to scan a local network for devices and detect OpenBeken devices.
    """    
    def __init__(self, local_ip=None,ip_list=None,silent=True):
        """
        Initializes a new networkScan object.

        Args:
        - local_ip (str): The IP address of the local machine. Default is None.
        - ip_list (list): A list of IP addresses to scan. Default is an empty list.
        - silent (bool): A flag indicating whether to print output. Default is True.

        This method initializes a new networkScan object with the specified parameters.
        """        
        self.is_silent  = silent
        if local_ip is None:
            local_ip    = self.__get_local_ip()
        self.local_ip   = local_ip
        self.network_ip = self.__get_network_ip()
        if ip_list is None:
            ip_list     = []        
        self.ip_list    = ip_list
        self.bkn_ips    = []
        self.ping_echo_r = 3
        
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

    def ping(self,ip_addr='',ping_echo_r=None):
        """
        Ping the specified IP address using the system's ping command.

        Args:
        - ip_addr (str): The IP address to ping. Default is an empty string.
        - ping_echo_r (int): The number of echo requests to send. Default is None.

        Returns:
        - True if the ping was successful (i.e., the IP address is reachable), or False otherwise.

        If `ping_echo_r` is not specified, the value of `self.ping_echo_r` is used instead. This value represents the number of echo requests to send during the ping.
        The function uses the system's ping command to send the requests and wait for a response.
        If the command succeeds (i.e., the IP address is reachable), the function returns True. Otherwise, it returns False.
        """
        if ping_echo_r is None:
            ping_echo_r = self.ping_echo_r
            
        if platform.system() == 'Windows':
            ping_cmd = ['ping', '-n', f'{ping_echo_r}', '-w', '500'] ## -w in ms
        else:
            ping_cmd = ['ping', '-c', f'{ping_echo_r}', '-W', '1'] ## -w in s
            
        try:
            subprocess.check_output(ping_cmd+[ip_addr])
            return True
        except subprocess.CalledProcessError:
            pass
            return False
        
    def ping_obk(self,ip_addr='',retries=1):
        """
        Ping the specified IP address and try to access the OpenBeken API.

        Args:
        - ip_addr (str): The IP address to ping. Default is an empty string.
        - retries (int): The number of retries if the request fails. Default is 1.

        Returns:
        - True if the ping was successful and the API is accessible (i.e., an OpenBeken device is found), or False otherwise.

        This function pings the specified IP address and tries to access the OpenBeken API at http://[ip_addr]/api/info. If the ping and API request are successful (i.e., an OpenBeken device is found), the function returns True. Otherwise, it returns False.
        """        
        requests.adapters.DEFAULT_RETRIES = retries
        try:
            board_info = requests.get(f'http://{ip_addr}/api/info', timeout=2)#.json()
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
        """
        Get a list of used IP addresses on the local network.

        Args:
        - ip_list (list): A list of IP addresses to scan. Default is None.
        - ip_chunks_size (int): The size of the IP chunks to ping. Default is 50.

        Returns:
        - A list of IP addresses that respond to ping requests.

        This function scans the local network for used IP addresses by pinging each IP address in the range 192.168.1.1 to 192.168.1.254. The IP addresses are divided into chunks to speed up the scanning process. The function returns a list of IP addresses that respond to ping requests.
        """
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
    
    def obkn_api_scan(self,ip_list=None,ip_chunks_size=2):
        """
        Get a list of OpenBeken devices based on a list of IP addresses.

        Args:
        - ip_list (list): A list of IP addresses to scan. Default is None.
        - ip_chunks_size (int): The size of the IP chunks to ping. Default is 2.

        Returns:
        - A list of IP addresses that are running OpenBeken devices.

        This function scans a list of IP addresses for OpenBeken devices by pinging each IP address and trying to access the OpenBeken API at http://[ip_addr]/api/info. The IP addresses are divided into chunks to speed up the scanning process. The function returns a list of IP addresses that are running OpenBeken devices.
        """
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