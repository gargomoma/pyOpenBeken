from flask import Flask, render_template, request, redirect,Response
import sys,time,json

from pyopenbeken import BoardManager, ThreadManager

# Opening JSON Settings file
# If using docker might be better to use env variables
settings = json.load( open('pyOpenBekenSettings.json') )
host_ip     = settings['host_ip']
gh_api_token = settings['gh_api_token']
list_ips     = settings['list_ips'] #WIP in scanning IPs, but takes +6min ATM

app = Flask(__name__)
thmanager = ThreadManager()
boardmgr = BoardManager(list_ips=list_ips,gh_token=gh_api_token)

release = boardmgr.releases

@app.route('/', methods=['GET', 'POST'])
def index():
    global list_ips,boards,release,boardmgr
    if request.method == 'POST':
        list_ips = request.form.get('IPs', '').split(',')
        boardmgr = BoardManager(list_ips=list_ips,gh_token=gh_api_token)
        #TODO more elegan way to get the release?
    return render_template('home_table.html', data=boardmgr.boards, list_ips=list_ips, release= release)

def update_ips(request):
    global list_ips
    list_ips = request.form.get('IPs', '').split(',')

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

##TODO check when a board has stopped doing OTA and refresh.
#@app.route('/updates')
#def updates():
#    #def generate():
#    #    # Perform some loop and yield the results
#    #    for i in range(10):
#    #        time.sleep(10)  # Simulate some processing time
#    #        yield 'data: {}\n\n'.format(i)  # SSE data format
#    #
#    # Return a Response object with the SSE MIME type
#    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host=host_ip,port=8051, debug=False)