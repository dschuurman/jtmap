# Connect to WSJTX and query QRZ.com to display contact details
# (C) 2020 Derek Schuurman
# License: GNU General Public License (GPL) v3
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import sys, os
import urllib.request
import json
import xml.etree.ElementTree as ET 
import socket
import adif_io
import geopy.distance
import configparser
import datetime
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade
import cartopy.feature
import matplotlib.pyplot as plt
import tkinter as tk
from select import select

VERSION=0.93

### Function definitions

def get_latitude_longitude(gridsquare):
    ''' Converts four character gridsquare to latitude,longitude at center of gridsquare
    '''
    longitude = -180.0 + (ord(gridsquare[0]) - ord('A')) * 20.0
    latitude = -90.0 + (ord(gridsquare[1]) - ord('A')) * 10.0
    longitude += float(gridsquare[2]) * 2.0
    latitude += float(gridsquare[3])
    longitude += 1.0
    latitude += 0.5

    return latitude, longitude

def compute_distance(location1, location2, units):
    ''' Computes distance between two latitude/longitude coordinates
        returns distnace in specified units
    '''
    if units == 'kilometers' or units == 'km':
        distance = geopy.distance.distance(location1, location2).kilometers
        units = 'km'
        logging.info("distance: {:.0f} km\n\n".format(distance))
    else:
        distance = geopy.distance.distance(location1, location2).miles
        units = 'miles'
        logging.info("distance: {:.0f} miles\n\n".format(distance))
    return distance

def create_GUI():
    ''' Create a main GUI window with a quit button to terminate program
    '''
    window = tk.Tk()
    window.title("JTmap")
    title = tk.Label(text="JTmap",font=("Arial Bold", 20))
    title.pack()
    info = tk.Label(text="by W8DCS version {:.2f}".format(VERSION),font=("Arial", 10))
    info.pack()
    status = tk.Label(text="Waiting for contacts from WSJT-X...",font=("Arial", 12))
    status.pack()

    # create a quit button
    button = tk.Button(master=window, text='Quit', command=lambda: os._exit(0))
    button.pack(side=tk.BOTTOM)
    return window

def lookup_callsign(callsign, database, user='', pwd=''):
    ''' Lookup callsign in an online database 
        Optional parameters may be required if database requires a username and password
        Returns a dictionary with contact details
        TO-DO: Add support for additional open online databases?
    '''
    # Initialize a dictionary to store contact data
    contact = {'callsign':callsign, 'name':'','qth':'','gridsquare':'','latitude':0.0,'longitude':0.0}

    logging.info('Looking up: {} using {}'.format(callsign,database))
    # CALLBOOK.info
    if database == "callbook.info":
        try:
            response = urllib.request.urlopen('http://callook.info/{}/json'.format(callsign))
        except:
            return None
        json_data = response.read()   #.decode('utf-8')
        data = json.loads(json_data)
        if data['status'] == 'INVALID':
            logging.info('callsign {} not found in {}.'.format(callsign,database))
            contact = None
        else:
            contact['name'] = data['name']
            contact['qth'] = data['address']['line2']
            contact['gridsquare'] = data['location']['gridsquare']
            contact['latitude'] = float(data['location']['latitude'])
            contact['longitude'] = float(data['location']['longitude'])
    # HAMDB.org
    elif database == "hamdb.org":
        try:
            response = urllib.request.urlopen('http://api.hamdb.org/{}/json/JTmap'.format(callsign))
        except:
            return None
        json_data = response.read()  #.decode("utf-8") 
        data = json.loads(json_data)
        if data['hamdb']['callsign']['call'] == 'NOT_FOUND':
            logging.info('callsign {} not found in {}.'.format(callsign,database))
            contact = None
        else:  # Get contact details and a more accurate latitute/longitude
            contact['name'] = data['hamdb']['callsign']['fname'] + ' ' + data['hamdb']['callsign']['name']
            contact['qth'] = data['hamdb']['callsign']['addr2'] + ', ' + data['hamdb']['callsign']['state'] + ', ' + data['hamdb']['callsign']['country']
            if data['hamdb']['callsign']['grid'] != 'Unknown':
                contact['gridsquare'] = data['hamdb']['callsign']['grid']
            if data['hamdb']['callsign']['lat']!='':
                contact['latitude'] = float(data['hamdb']['callsign']['lat'])
                contact['longitude'] = float(data['hamdb']['callsign']['lon'])
    # QRZ.com
    elif database == "qrz.com":
        # If this is the first query then request a session key
        # Note: session key should last 24 hours (however, specs say this is not guaranteed)
        if not hasattr(lookup_callsign, "session"):
            try:
                response = urllib.request.urlopen('https://xmldata.qrz.com/xml/current/?username={};password={}'.format(user,pwd))
                root = ET.fromstring(response.read())
                key = root.find('.//{http://xmldata.qrz.com}Key')
                if key == None:
                    logging.info('Session key not received from {}.'.format(database))
                    return None
                logging.info('Session key obtained from {}.'.format(database))
                lookup_callsign.session = key.text
            except:
                logging.info('No session key response from {}.'.format(database))
                return None
        # Send query using saved session key
        try:
            response = urllib.request.urlopen('http://xmldata.qrz.com/xml/current/?s={};callsign={}'.format(lookup_callsign.session,callsign))
        except:
            return None
        data = response.read()
        logging.info('{} replies with: {}.'.format(database,data))
        root = ET.fromstring(data)
        # Check for error(s)
        error = root.find('.//{http://xmldata.qrz.com}Error')
        if error != None:
            logging.info('{} returned error: {}'.format(database,error.text))
            if error.text == 'Session Timeout':
                # if session key is invalid, delete it so a new one will be requested on next call
                del lookup_callsign.session
            return None
        # If no errors, get information returned
        name = root.find('.//{http://xmldata.qrz.com}name').text
        fname = root.find('.//{http://xmldata.qrz.com}fname')
        if fname != None:
            contact['name'] = fname.text + ' ' + name
        else:
            contact['name'] = name
        address = root.find('.//{http://xmldata.qrz.com}addr2')
        if address != None:
            contact['qth'] = address.text
        else:
            contact['qth'] = ''
        state = root.find('.//{http://xmldata.qrz.com}state')
        if state != None:
            contact['qth'] += ', ' + state.text
        country = root.find('.//{http://xmldata.qrz.com}country')
        if state != None:
            contact['qth'] += ' ' + country.text
        # That's all - more information requires a subscription with qrz.com
    else:
        contact = None
    
    if contact != None:
        logging.info('Online data returned = {}'.format(str(contact)))
    return contact

##################### main code ########################

# Read constants from configuration file (assumed to be in the same folder as the program)
conf = configparser.ConfigParser()
if conf.read('jtmap.conf') == []:
    print('jtmap.conf file missing... please place it in the same folder as the program.')

# If localhost is selected, then bind to local loopback only
if conf.getboolean('jtmap','LOCALHOST'):
    UDP_IP = "127.0.0.1"
else:
    UDP_IP = "0.0.0.0"   # otherwise bind to all local ports
UDP_PORT = conf.getint('jtmap','PORT')

# Use latitude/longitude of present, otherwise use gridsquare reported in WSJT-X
if conf.has_option('jtmap','LATITUDE'):
    my_latitude = conf.getfloat('jtmap','LATITUDE')
else:
    my_latitude = None
if conf.has_option('jtmap','LONGITUDE'):
    my_longitude = conf.getfloat('jtmap','LONGITUDE')
else:
    my_longitude = None
WEB_DATABASE = conf.get('jtmap','WEB_DATABASE').lower()
if conf.has_option('jtmap','WEB_USER'):
    USER = conf.get('jtmap','WEB_USER')
else:
    USER = ''
if conf.has_option('jtmap','WEB_PASSWORD'):
    PWD = conf.get('jtmap','WEB_PASSWORD')
else:
    PWD = ''

LOGGING = conf.get('jtmap','LOG_LEVEL')
if conf.has_option('jtmap','DISTANCE_UNITS'):
    DISTANCE_UNITS = conf.get('jtmap','DISTANCE_UNITS')
else:
    DISTANCE_UNITS = 'miles'  # Show miles by default

# Set logging level; default to reporting errors only
if LOGGING == 'debug':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
elif LOGGING == 'info':
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
else:
    logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

# Disable annoying font warning messages
logging.getLogger('matplotlib.font_manager').disabled = True

# Create UDP server socket for listening to WSJT-X
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
server.bind((UDP_IP, UDP_PORT))
server.setblocking(False)
logging.info('listening on {}:{}'.format(UDP_IP, UDP_PORT))

# create main window with a quit button to terminate
window = create_GUI()

while True:
    # Loop to wait for a UDP packet; service figure event loop while waiting
    while True:
        # Wait for packets
        # Note that tkinter and matplotlib prefer to run in the main thread
        # so use a timeout after 50ms and service any pending events
        ready = select([server],[],[],0.05)
        if ready[0]:
            data,addr = server.recvfrom(2048)  # buffer size is 2 kbytes
            logging.debug('Recv UDP: {}'.format(data))
            break
        # Service event loop on figure (if presemt)
        if len(plt.get_fignums()) != 0:
            fig.canvas.draw_idle()
            fig.canvas.flush_events()

        # Update tkinter GUI (run this periodically rather than using a blocking mainloop)
        window.update()

    # Proceed only if a QSO is completed (indicated by byte 12 in header)
    if data[11] != 0x0c:
        continue

    # Parse completed QSO and extract ADIF payload
    logging.info('QSO completed!')
    header = data[:16]
    adif = data[26:].decode('utf-8')
    logging.debug("WSJT-X header: {}\nWSJT-X ADIF payload: {}".format(header, adif))

    # Parse ADIF data
    qsos, header =  adif_io.read_from_string(adif)
    qso = qsos[0]
    logging.info("ADIF data: {}\nADIF Header: {}\n".format(qsos, header))
    
    # Extract call from ADIF data
    callsign = qso['CALL']
    my_callsign = qso['STATION_CALLSIGN']
    gridsquare = qso['GRIDSQUARE']
    my_gridsquare = qso['MY_GRIDSQUARE']
    
    # If no home station latitude/longitude was specified in conf file, 
    # use center of my_gridsquare reported in WSJT-X to approximate my latitude/longitude
    if my_latitude == None:
        my_latitude, my_longitude = get_latitude_longitude(my_gridsquare)

    # Lookup callsign information in an online database
    contact = lookup_callsign(callsign, WEB_DATABASE, USER, PWD)

    # If online database returns nothing, just use data available from WSJT-X
    if contact == None:
        # Initialize a dictionary with the basic data we know from WSJT-X
        contact = {'callsign':callsign, 'name':'', 'qth':'', 'gridsquare':gridsquare, 'latitude':0.0, 'longitude':0.0}

    # If no latitude/longitude set, use station's gridsquare to get approximate latitude/longitude
    if gridsquare != '' and contact['latitude'] == 0.0 and contact['longitude'] == 0.0:
        latitude, longitude = get_latitude_longitude(gridsquare)
        contact['latitude'] = latitude
        contact['longitude'] = longitude

    # If there is still no position information available at this point, skip map and loop again (this should be rare)
    if contact['latitude'] == 0.0 and contact['longitude'] == 0.0:
        continue

    # Compute distance of contact
    distance = compute_distance((my_latitude,my_longitude), (contact['latitude'], contact['longitude']), DISTANCE_UNITS)

    # Plot communication on a map
    # close the current plot and create a new figure
    plt.close()
    fig = plt.figure()
    fig.canvas.set_window_title('WSJT-X QSO confirmed')

    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") 
    ax.set_title('WSJT-X QSO confirmed on {}'.format(date))

    # Zoom in on region of interest on map
    ax.set_extent([min(contact['longitude'],my_longitude)-5, max(contact['longitude'],my_longitude)+5, 
                   min(contact['latitude'],my_latitude)-5, max(contact['latitude'],my_latitude)+5],crs=ccrs.PlateCarree())

    # Add map features
    ax.add_feature(cartopy.feature.OCEAN)
    ax.add_feature(cartopy.feature.LAND, edgecolor='black')
    ax.add_feature(cartopy.feature.LAKES, edgecolor='black')
    ax.add_feature(Nightshade(datetime.datetime.utcnow(), alpha=0.2))

    # show contact details in a text box if it was found in database
    if contact['name'] != '':
        contact_details = 'call: {}\nname: {}\n{}\ndistance: {:.0f} {}'.format(contact['callsign'], contact['name'], contact['qth'], distance, DISTANCE_UNITS)
        plt.figtext(0.5, 0.00, contact_details, ha="center", fontsize=12, bbox={"facecolor":"white", 'edgecolor':'none', "alpha":1.0, "pad":5})
    else:  # otherwise show basic information
        contact_details = 'call: {}\ndistance: {:.0f} {}'.format(contact['callsign'], distance, DISTANCE_UNITS)
        plt.figtext(0.5, 0.00, contact_details, ha="center", fontsize=12, bbox={"facecolor":"white", 'edgecolor':'none', "alpha":1.0, "pad":5})

    at_x, at_y = ax.projection.transform_point(my_longitude, my_latitude, src_crs=ccrs.PlateCarree())
    plt.annotate(my_callsign, xy=(at_x, at_y), color='green', ha='left', fontweight='bold')

    at_x, at_y = ax.projection.transform_point(contact['longitude'], contact['latitude'], src_crs=ccrs.PlateCarree())
    plt.annotate(callsign, xy=(at_x, at_y), color='green', ha='right', fontweight='bold')

    plt.plot([my_longitude, contact['longitude']], [my_latitude, contact['latitude']], color='blue', linewidth=2, marker='o', transform=ccrs.Geodetic())

    # This will draw and fit things nicely in the window
    # Note: tight_layout() must be called after draw()
    fig.canvas.draw()
    fig.tight_layout()
 
    plt.show(block = False)
