from .core import device
from .utils import ThreadManager,networkScan

class BoardManager:
    def __init__(self, list_ips,gh_token=None,silent=True):
        self.list_ips = list_ips
        self.gh_token = gh_token
        self.is_silent = silent
        self.releases = {} #so user can inject the releases from other chipset object, avoiding multiple calls to gh
        self.get_boards()
    
    def update_releases(self):
        #TODO more elegat way to get the releases?
        ##This works but might be even easier way to just call get_boards again
        self.releases = self.boards[ next(iter(self.boards)) ]['obj'].get_releases(redownload_release=True)
        return self.releases
    
    def get_boards(self):
        boards = {}
        for board_ip in self.list_ips:
            boards[board_ip] = { 'obj' : device(board_ip,self.gh_token) }
            if 'build' not in self.releases:
                self.releases = boards[board_ip]['obj'].get_releases()
            else:
                boards[board_ip]['obj'].releases = self.releases

            boards[board_ip]['obj'].check_ota()

            board_name = boards[board_ip]['obj'].name
            boards[board_ip]['name']= board_name
            boards[board_ip]['mqtttopic']=boards[board_ip]['obj'].info['mqtttopic']
            boards[board_ip]['chipset']=boards[board_ip]['obj'].chipset
            boards[board_ip]['build']=boards[board_ip]['obj'].build
            boards[board_ip]['ota_available']=boards[board_ip]['obj'].ota_available
            boards[board_ip]['files'] = boards[board_ip]['obj'].get_files()
        self.boards=boards
        return self.boards
    
    def update_boards(self, boards=None,is_silent=False,backupFlow=True):
        manager = ThreadManager()        
        if boards is None:
            boards=self.boards
        boards_to_update = {k:v for k,v in self.boards.items() if k in boards}
        for board_ip,board_dict in boards_to_update.items():
            #TODO add threading? Doesn't make sense to run sequentially.
            board_dict['obj'].is_silent = is_silent
            #board_dict['obj'].push_ota(board_dict['obj'].ota_fname,backupFlow=backupFlow)
            #min/update sequentially is a waste of time, better do in multiple threads
            manager.start_thread(target=board_dict['obj'].push_ota, args=(board_dict['obj'].ota_fname,True))
            board_dict['ota_wip']=True
        manager.join_all()
        self.get_boards()
        for board_ip,board_dict in boards_to_update.items():
            board_dict.pop('ota_wip')