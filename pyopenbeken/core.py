import os
import re
import requests
import time

class device:
    def slnt_print(self,message):
        if not self.is_silent:
            print(message)

    def get_pins(self):
        """
        Gets information about the pin roles and channels configured on the device.

        Returns:
            A list of dictionaries containing information about the pins, channels and roles.
            Each dictionary has the following keys:
                - 'pin': the pin number.
                - 'channels': a list of channel numbers associated with the pin.
                - 'role': the role assigned to the pin.
        """        
        pins = requests.get(self.device_urls['pins']).json()
        self.pins=[]
        for pin_idx,role in enumerate(pins['roles']):
            #if role != 0?
            self.pins.append( {'pin':pin_idx,'channels':pins['channels'][pin_idx],'role':pins['rolenames'][role],'role_id':role} )
        return self.pins

    def set_pins(self,pin_roles=None):
        """
        Sends pins configuration to the device.

        Args:
            pin_roles (list): A list of dictionaries containing information about the pins, channels and roles.
            Each dictionary has the following keys:
                - 'pin': the pin number.
                - 'channels': a list of channel numbers associated with the pin.
                - 'role': the role assigned to the pin.
        Returns:
            bool: True if the pins were successfully configured, False otherwise.
        """
        if pin_roles is None:
            assert False
        #Checks if it's formated in pyOpenBeken human-readable format
        if ('channels' not in pin_roles) and ('channels' in pin_roles):
            #if so, convert to OpenBeken's
            pin_roles = {'channels':[pin['channels']for pin in pin_roles], 'roles':[pin['role_id']for pin in pin_roles]}
        elif ('channels' not in pin_roles):
            assert False
        set_pins = requests.post(self.device_urls['pins'],data= pin_roles)
        if set_pins.status_code == 200:
            self.get_pins()
            return True
        return False
            
    def get_info(self):
        """
        Retrieves information about the device's board.
        
        Returns:
            A dictionary containing basic information about the device.
        """              
        self.info = requests.get(self.device_urls['info']).json()
        self.chipset = self.info['chipset']
        self.build = re.search(r"version (\d+\.\d+\.\d+)", self.info['build']).group(1)
        self.name = self.info['mqtttopic'].split("/")[-1]
        self.get_pins()
        return self.info
    
    def send_cmnd(self,cmnd):
        """
        Sends the given command to the device's 'cmnd' URL.
        Args:
            cmnd (str): The command to be sent to the device.
        Returns:
            The status code of the POST request.
        """        
        send_cmnd = requests.post(f"{ self.device_urls['cmnd'] }",data= cmnd )
        return send_cmnd.status_code
    
    def get_files(self):
        """
        Retrieves the files stored on the device by sending a GET request to the 'lfs' URL.
        Returns:
            A dictionary containing the content of the files stored on the device.
        """            
        self.board_files = {}
        lfs = requests.get(self.device_urls['lfs'])
        if lfs.status_code == 200:
            for fname in [x['name'] for x in lfs.json()['content'] if x['type']!=2]:
                content = requests.get(f"{ self.device_urls['lfs'] }/{fname}").text
                self.board_files[fname]=content
            return self.board_files
        else:
            self.slnt_print(f'STATUSCODE {lfs.status_code} - Something is wrong, are you sure there are files?')

    def create_file(self,fname='autoexec.bat',content='',resetSVM_and_Start=True):
        """
        Creates a new file on the device by sending a POST request to the 'lfs' URL.
        Args:
            fname (str): The name of the file to be created (default is 'autoexec.bat').
            content (str): The content of the file to be created (default is an empty string).
            resetSVM_and_Start (bool): A boolean that indicates whether the SVM should be reset and started after creating the file (default is True).
        """            
        post_file = requests.post(f"{ self.device_urls['lfs'] }{fname}",data=content.encode('utf-8'))
        if resetSVM_and_Start:
            post_file = self.send_cmnd( self.resetSVM_and_Start.format(scriptName=fname) )
    
    def delete_file(self,fname):
        """
        Deletes the file with the given name from the device by sending a POST request to the 'del' URL.
        Args:
            fname (str): The name of the file to be deleted.
        """            
        post_file = requests.post(f"{ self.device_urls['del'] }/{fname}")
        return post_file.status_code
    
    def get_releases(self,redownload_release=False):
        """
        Retrieves the latest release of the OpenBK7231T_App by sending a GET request to the GitHub API.
        Args:
            redownload_release (bool): A boolean that indicates whether to download the release again (default is False).
        Returns:
            A dictionary containing the latest build, published date, URL, and assets of the releases of the OpenBK7231T_App.
        """            
        if 'build' not in self.releases or redownload_release:
            self.slnt_print('Retrieving releases from GH.')

            latest = requests.get('https://api.github.com/repos/openshwprojects/OpenBK7231T_App/releases',headers= self.gh_headers ).json()[0]
            self.releases = {'build':latest['name'],'published_at': latest['published_at'],'html_url': latest['html_url'],'assets': [{'name':file['name'],'browser_download_url':file['browser_download_url']} for file in latest['assets']]}
        else:
            self.slnt_print('Retrieving releases from memory.')
        return self.releases

    def check_ota(self,redownload_release=False): 
        """
        Checks whether an OTA update is available by comparing the device's build version with the latest release of the OpenBK7231T_App.
        Args:
            redownload_release (bool): A boolean that indicates whether to download the release again (default is False).
        Returns:
            The URL of the OTA file if an update is available; otherwise, None.
        """            
        if self.build < self.get_releases(redownload_release)['build']:
            #This way we can skip calling get_releases, and just call this method directly
            for asset in self.releases['assets']:
                if self.ota_fname_check(asset['browser_download_url']):
                    self.slnt_print(f"OTA file found -- build:{self.releases['build']}\n{self.releases['html_url']}") 
                    self.otaurl = asset['browser_download_url']
                    self.ota_available = True
                    self.ota_fname = os.path.basename(self.otaurl)
                    return self.otaurl
            self.slnt_print('No OTA file found.')
        else:
            self.ota_available = False
            self.slnt_print('Device is up to date.')

    def __build_gh_headers(self):
        if self.gh_token is not None:
            self.gh_headers = {'Authorization': 'token ' + self.gh_token}
        else:
            self.gh_headers = {}  
    
    def __send_ota(self,fileAddr=''):
        if self.ota_fname_check(fileAddr):
            if not os.path.exists(fileAddr):
                self.download_ota()
            post_file = requests.post(f"{ self.device_urls['ota'] }", data=open(fileAddr, "rb").read())
            if post_file.status_code == 200:
                requests.post(f"{ self.device_urls['reboot'] }")
                self.slnt_print('OTA sucessful, please wait 60 seconds')
                time.sleep(60)
                old_build = self.build
                self.get_info()
                self.slnt_print(f'Succesfully updated from {old_build} to {self.build}!')
        else:
            self.slnt_print('Wrong OTA file.')

    def push_ota(self,fileAddr=None,backupFlow=True):
        """
        Pushes the downloaded OTA file on the device.
        Args:
            filepath (str): The file path where the OTA file should be pushed to on the device.
        Returns:
            The True if the OTA was successful; otherwise, None.
        """
        if fileAddr is None:
            if hasattr(self, 'ota_fname'):
                fileAddr = self.ota_fname
            else:
                #I would rather raise an exception. But let's see how it goes.
                self.check_ota()
                fileAddr = self.ota_fname
        if backupFlow:
            self.get_files()
        self.__send_ota(fileAddr)
        if backupFlow:
            self.board_files
            for fname,content in self.board_files.items():
                self.create_file(fname=fname,content=content)
            self.slnt_print(f'Files succesfully restored!')
        return True
            
    def download_ota(self):
        """
        Downloads an OTA file (if available) and saves it to the file system.
        Args:
            url (str): The URL of the OTA file to download.
        Returns:
            Filename.
        """
        if not hasattr(self, 'ota_available'):
            self.slnt_print('Checking OTA...')
            self.check_ota()
        if self.ota_available:
            get_ota = requests.get(self.otaurl,headers= self.gh_headers )
            if get_ota.status_code == 200:
                fname=os.path.basename(self.otaurl)
                open(fname, 'wb+').write(get_ota.content)
                self.slnt_print(f'OTA file saved in {os.getcwd()}/{fname}')
                return fname
        else:
            self.slnt_print('No OTA is need, device is up to date.')
    
    def ota_fname_check(self,fname):
        """
        Checks whether a filename matches the expected format for an OTA update file for the device's board.
        Args:
            fname (str): The filename to check.
        Returns:
            True if the filename matches the expected format; otherwise, False.
        """           
        chipset_map = {
            'BK7231T': ('OpenBK7231T_', '.rbl'),
            'BK7231N': ('OpenBK7231N_', '.rbl'),
            'XR809': ('OpenXR809_', '.img'),
            'BL602': ('OpenBL602_', '.bin'),
            'W800': ('OpenW800_', '_ota.img'),
            'W600': ('OpenW600_', '_gz.img')
        }
        prefix, postfix = chipset_map.get(self.chipset, ('', ''))
        return (prefix in fname) and (postfix in fname)
    
    def cfg_mqtt(self,host,port,client,group,user,password):
        """
        Configures the MQTT settings for the device by sending a POST request to the device's MQTT configuration endpoint.
        Args:
            host (str): The MQTT broker hostname or IP address.
            port (int): The MQTT broker port number.
            client (str): The MQTT client ID to use when connecting to the broker.
            group (str): The group ID to use when connecting to the broker (optional).
            user (str): The username to use when connecting to the broker (optional).
            password (str): The password to use when connecting to the broker (optional).
        Returns:
            requests.Response: The response object returned by the MQTT configuration endpoint.
        """        
        params = locals()
        url_params_dict = {k:v for k,v in params.items() if v is not None}
        url_params_dict.pop('self')
        params = [(k,v) for k,v in url_params_dict.items()]
        return requests.post( self.device_urls['mqtt'], params=params )
    
    def ha_discv(self):
        """
        Enables HomeAssistant MQTT discovery.
        """         
        self.slnt_print(f'Enabling HA discovery.')
        return requests.post( self.device_urls['ha_discv'])
    
    def __init__(self, ip_addr,gh_token=None,silent=True):
        """
        A class for interfacing with an OpenBK7231T device

        Parameters:
        -----------
        ip_address : str
            The IP address of the device
        gh_token : str, optional
            The GitHub token to use for API access (default is None)
            Optional, but recommended to avoid
        silent : bool, optional
            Flag for silent mode. If True, print statements are suppressed (default is False)

        Methods:
        --------
        slnt_print(message)
            Print the message if silent mode is False
        get_info()
            Retrieve information about the device
        get_pins()
            Gets information about the pin roles and channels configured on the device
        set_pins()
            Sends pins configuration to the device           
        send_cmnd(cmnd)
            Send a command to the device
        get_files()
            Retrieve files from the device
        create_file(fname='autoexec.bat',content='',resetSVM_and_Start=True)
            Create a file on the device
        delete_file(fname)
            Delete a file from the device
        get_releases(redownload_release=False)
            Retrieve the latest release information from GitHub
        check_ota(redownload_release=False)
            Check if an OTA update is available
        push_ota(fileAddr='',backupFlow=True)
            Push an OTA update to the device
        download_ota()
            Download an OTA update from GitHub
        ota_fname_check(fname)
            Check if a filename is a valid OTA update for the device

        Attributes:
        -----------
        device_urls : dict
            Dictionary of URLs for interacting with the device
        gh_token : str or None
            The GitHub token to use for API access
        gh_headers : dict
            Dictionary of headers for use with the GitHub API
        chipset : str
            The chipset of the device
        pins : list
            List of dictionaries containing information about the pins, channels and roles.            
        build : str
            The build version of the device
        name : str
            The name of the device
        info : dict
            Information about the device
        board_files : dict
            Files on the device
        releases : dict
            Information about the latest release on GitHub
        ota_available : bool
            Flag for whether an OTA update is available
        otaurl : str
            URL of the OTA update
        ota_fname : str
            Filename of the OTA update
        is_silent : bool
            Flag for silent mode
        """        
        self.board_ip = ip_addr
        self.gh_token = gh_token
        self.__build_gh_headers()
        self.is_silent = silent
        self.releases = {} #so user can inject the releases from other chipset object avoiding multiple calls
        self.resetSVM_and_Start = 'backlog resetSVM; startScript /{scriptName}'
        self.board_url = f"http://{ip_addr}/"
        self.API_ENDPOINT = f"{self.board_url}api/"
        self.device_urls = {
                'info' : self.API_ENDPOINT+'info'
                ,'lfs':self.API_ENDPOINT+'lfs/' #needs the slash or fails O.o
                ,'cmnd':self.API_ENDPOINT+'cmnd'
                ,'del':self.API_ENDPOINT+'del'
                ,'pins':self.API_ENDPOINT+'pins'
                ,'channels':self.API_ENDPOINT+'channels'            
                ,'channelTypes':self.API_ENDPOINT+'channelTypes'
                ,'ota':self.API_ENDPOINT+'ota' #push OTA file as payload
                ,'reboot':self.API_ENDPOINT+'reboot'
                ,'mqtt':self.board_url+'cfg_mqtt_set'
                ,'ha_discv':self.board_url+'ha_discovery?prefix=homeassistant'
                }
        self.project_urls = {
                'devices' : 'https://openbekeniot.github.io/webapp/devices.json'
                ,'releases':'https://api.github.com/repos/openshwprojects/OpenBK7231T_App/releases'
                }
        self.get_info()