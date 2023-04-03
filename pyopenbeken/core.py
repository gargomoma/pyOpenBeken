import os
import re
import requests
import time

class device:
    def slnt_print(self,message):
        if not self.is_silent:
            print(message)
        
    def get_info(self):
        self.board_info = requests.get(self.device_urls['info']).json()
        self.chipset = self.board_info['chipset']
        self.build = re.search(r"version (\d+\.\d+\.\d+)", self.board_info['build']).group(1)
        self.name = self.board_info['mqtttopic'].split("/")[-1]
        return self.board_info
    
    def send_cmnd(self,cmnd):
        send_cmnd = requests.post(f"{ self.device_urls['cmnd'] }",data= cmnd )
        return send_cmnd.status_code
    
    def get_files(self):
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
        post_file = requests.post(f"{ self.device_urls['lfs'] }{fname}",data=content.encode('utf-8'))
        if resetSVM_and_Start:
            post_file = self.send_cmnd( self.resetSVM_and_Start.format(scriptName=fname) )
    
    def delete_file(self,fname):
        post_file = requests.post(f"{ self.device_urls['del'] }/{fname}")
        return post_file.status_code
    
    def get_releases(self,redownload_release=False):
        if 'build' not in self.releases or redownload_release:
            self.slnt_print('Retrieving releases from GH.')
            headers = {'Authorization': 'token ' + self.gh_token}    
            latest = requests.get('https://api.github.com/repos/openshwprojects/OpenBK7231T_App/releases',headers=headers).json()[0]
            self.releases = {'build':latest['name'],'published_at': latest['published_at'],'html_url': latest['html_url'],'assets': [{'name':file['name'],'browser_download_url':file['browser_download_url']} for file in latest['assets']]}
        else:
            self.slnt_print('Retrieving releases from memory.')
        return self.releases

    def check_ota(self,redownload_release=False): 
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

    def push_ota(self,fileAddr='',backupFlow=True):
        if backupFlow:
            self.get_files()
        self.__send_ota(fileAddr)
        if backupFlow:
            self.board_files
            for fname,content in self.board_files.items():
                self.create_file(fname=fname,content=content)
            self.slnt_print(f'Files succesfully restored!')
            
    def download_ota(self):
        if self.ota_available:
            headers = {'Authorization': 'token ' + self.gh_token}    
            get_ota = requests.get(self.otaurl,headers=headers)
            if get_ota.status_code == 200:
                fname=os.path.basename(self.otaurl)
                open(fname, 'wb+').write(get_ota.content)
                self.slnt_print(f'OTA file saved in {os.getcwd()}/{fname}')
        else:
            self.slnt_print('No OTA is need, device is up to date.')
    
    def ota_fname_check(self,fname):
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
        params = locals()
        url_params_dict = {k:v for k,v in params.items() if v is not None}
        url_params_dict.pop('self')
        params = [(k,v) for k,v in url_params_dict.items()]
        return requests.post( self.device_urls['mqtt'], params=params )
    
    def ha_discv(self):
        self.slnt_print(f'Enabling HA discovery.')
        return requests.post( self.device_urls['ha_discv'])
    
    def __init__(self, ip_addr,gh_token='',silent=True):
        self.board_ip = ip_addr
        self.gh_token = gh_token
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