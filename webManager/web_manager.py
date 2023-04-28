from flask import Flask, render_template, request, redirect,Response
import sys,time,json
from pyopenbeken import deviceManager, threadManager,networkScan

app = Flask(__name__)
thmanager = threadManager()

##Get local IP & Bkn devices by scanning the local network
network = networkScan()
host_ip = network.local_ip

def scan_devices(method='ip'):
    global network, list_ips
    start_time = time.time()
    if method == 'ssdp':
        network.obkn_ssdp_scan()
    if method == 'ip':
        print('Scanning local network for IPs')
        network.get_network_ips(ip_chunks_size=1)
        print('Looking for OpenBeken devices')
        network.obkn_api_scan(ip_chunks_size=1)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} seconds -- Devices found: {'; '.join( network.bkn_ips )}")
    
def refresh_ota_info(redownload_release=True):
    global devmgr,release,changes    
    devmgr.check_ota(redownload_release)
    release = devmgr.releaseMngr.latest
    changes = devmgr.releaseMngr.check_changes(devmgr.min_build)       


@app.route('/', methods=['GET', 'POST'])
def index():
    global list_ips,devices,release,devmgr,changes
    if request.method == 'POST':
        list_ips = request.form.get('IPs', '').split(',')
        devmgr = deviceManager(list_ips=list_ips,gh_token=gh_api_token)
        changes = devmgr.releaseMngr.check_changes(devmgr.min_build)
        #TODO more elegan way to get the release?
    return render_template('home_table.html', data=devmgr.devices
                               , list_ips=list_ips , release= release
                           , message = msg , build_changes = changes)

@app.route('/scan_devices', methods=['GET', 'POST'])
def find_devices():
    methods=['ssdp','ip']
    global devmgr,release, list_ips, msg,changes
    json_payload = request.get_json()
    if 'scan_method' in json_payload and json_payload['scan_method'] in methods:
        scan_devices(json_payload['scan_method'])
        new_ips = [ new_ip for new_ip in network.bkn_ips if new_ip not in list_ips ]
        if len(new_ips)>0:
            msg = 'New Devices found: '+ '; '.join(new_ips)
            list_ips = network.bkn_ips
            devmgr = deviceManager(list_ips=list_ips,gh_token=gh_api_token)
            changes = devmgr.releaseMngr.check_changes(devmgr.min_build)
        else:
            msg = f"No NEW devices found. {'SSDP drivers might be disabled, please consider IP method.' if json_payload['scan_method']=='ssdp' else ''}"
        return f"{msg}"
    else:
        return f"Invalid method, please review."

@app.route('/refresh_releases', methods=['GET', 'POST'])
def refresh_releases():
    global devmgr,release,changes
    refresh_ota_info(redownload_release=True)
    return redirect('/')
    
@app.route('/update', methods=['GET', 'POST'])
def run_ota_devices():
    json_payload = request.get_json()
    if 'updateips' in json_payload:
        devices_to_update = json_payload['updateips']
        print(f"Devices TO UPDATE: {'; '.join(devices_to_update)}", file=sys.stderr)
        thmanager.start_thread(target=devmgr.update_devices, args=(devices_to_update,))
        return f"The following board(s) will be updated:\n{'; '.join(devices_to_update)}\nPlease wait a few minutes."

@app.route('/writefs', methods=['GET', 'POST'])
def write_file():
    json_payload = request.get_json()
    if 'fileName' in json_payload:
        devmgr.devices[ json_payload['ip_addr'] ]['device'].create_file(fname=json_payload['fileName'],content=json_payload['value'],resetSVM_and_Start=True)
        return f"The following file(s) will be updated:\n- device IP(s): {json_payload['ip_addr']}: {json_payload['fileName']}\nPlease wait a few seconds."    

if __name__ == '__main__':
    
    gh_api_token = None
    scan_devices()
    list_ips = network.bkn_ips
    devmgr   = deviceManager(list_ips=list_ips, gh_token=gh_api_token)
    refresh_ota_info(redownload_release=False)
    msg = ''    
    
    app.run(host=host_ip ,port=8998 ,debug=False)