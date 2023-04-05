from flask import Flask, render_template, request, redirect,Response
import sys,time,json

from pyopenbeken import BoardManager, ThreadManager,networkScan

### Example: JSON Settings file
#settings = json.load( open('pyOpenBekenSettings.json') )
#host_ip     = settings['host_ip']
#gh_api_token = settings['gh_api_token'] # If using docker might be better to use env variable
#list_ips     = settings['list_ips']

### Example: Get local IP & Bkn devices by scanning the local network
network = networkScan()
host_ip = network.local_ip
print('Scanning local network for IPs')
network.get_network_ips(ip_chunks_size=10)
print('Looking for OpenBeken devices')
network.obkn_api_scan(ip_chunks_size=2)
list_ips = network.bkn_ips
print('Devices found: '+ '; '.join(list_ips))

app = Flask(__name__)
thmanager = ThreadManager()
boardmgr = BoardManager(list_ips=list_ips) #gh_token=gh_api_token

msg = ''

release = boardmgr.releases

@app.route('/', methods=['GET', 'POST'])
def index():
    global list_ips,boards,release,boardmgr
    if request.method == 'POST':
        list_ips = request.form.get('IPs', '').split(',')
        boardmgr = BoardManager(list_ips=list_ips,gh_token=gh_api_token)
        #TODO more elegan way to get the release?
    return render_template('home_table.html', data=boardmgr.boards, list_ips=list_ips, release= release, message = msg)

def update_ips(request):
    global list_ips
    list_ips = request.form.get('IPs', '').split(',')

@app.route('/find_devices', methods=['GET', 'POST'])
def find_devices():
    global boardmgr,release, list_ips, msg
    network.get_network_ips(ip_chunks_size=10)
    network.obkn_api_scan(ip_chunks_size=2)
    new_ips = [ new_ip for new_ip in network.bkn_ips if new_ip not in list_ips ]
    if len(new_ips)>0:
        msg = 'New Devices found: '+ '; '.join(new_ips)
        list_ips = network.bkn_ips
        boardmgr = BoardManager(list_ips=list_ips,gh_token=gh_api_token)
    return redirect('/')

@app.route('/refresh_releases', methods=['GET', 'POST'])
def refresh_releases():
    global boardmgr,release
    release = boardmgr.update_releases()
    return redirect('/')
    
@app.route('/update', methods=['GET', 'POST'])
def run_ota_boards():
    boards_to_update = []
    for key, value in request.form.to_dict(flat=False).items():
         if key == 'ota_available':
            boards_to_update=value
    print(f"BOARDS TO UPDATE: {'; '.join(boards_to_update)}", file=sys.stderr)
    thmanager.start_thread(target=boardmgr.update_boards, args=(boards_to_update))
    return f"{'; '.join(boards_to_update)} board(s) will be updated.<br>Please wait a few minutes.<a href='/'>Return to main page<//a>"

if __name__ == '__main__':
    app.run(host=host_ip,port=8998, debug=False)