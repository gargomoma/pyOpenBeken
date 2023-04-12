from .core import device
from .utils import threadManager,networkScan,releaseManager

class deviceManager:
    def __init__(self, list_ips,gh_token=None,silent=True):
        self.list_ips = list_ips
        self.gh_token = gh_token
        self.releaseMngr = releaseManager(gh_token)
        self.is_silent = silent
        self.get_devices()

    def get_devices(self):
        devices = {}
        for board_ip in self.list_ips:
            devices[board_ip] = self.__builddevices( device(board_ip,self.gh_token) )
        self.devices=devices
        self.check_ota()
        return self.devices
    
    def __builddevices(self,deviceOjb):
        
        return {'device'    : deviceOjb
                ,'name'      : deviceOjb.name
                ,'mqtttopic' : deviceOjb.info['mqtttopic']
                ,'chipset'   : deviceOjb.chipset
                ,'build'     : deviceOjb.build
                ,'files'     : deviceOjb.get_files()}        
    
    def check_ota(self,redownload_release=False):
        self.releaseMngr.get_releases(redownload_release)
        for board_ip,board_dict in self.devices.items():
            #By using an unique Release Manager we call GH once, and all share the same release info.
            board_dict['device'].releaseMngr = self.releaseMngr #One call to check'em all.
            board_dict['device'].check_ota()#1st will call GH the others will retrieve from memory.            
            board_dict['ota_available']=board_dict['device'].ota_available        
    
    def update_devices(self, devices=None,is_silent=False,backupFlow=True):
        manager = threadManager()        
        if devices is None:
            devices=self.devices
        devices_to_update = {k:v for k,v in self.devices.items() if k in devices}
        for board_ip,board_dict in devices_to_update.items():
            board_dict['device'].is_silent = is_silent
            #update sequentially is a waste of time, better do in multiple threads
            manager.start_thread(target=board_dict['device'].push_ota, args=(board_dict['device'].ota_fname,True))
            board_dict['ota_wip']=True
        manager.join_all()
        self.get_devices()
        for board_ip,board_dict in devices_to_update.items():
            board_dict.pop('ota_wip')