# JTmap
A companion program for [WSJT-X](http://physics.princeton.edu/pulsar/K1JT/wsjtx.html)
that listens for information and displays a friendly map with additional information after each contact is confirmed.
The program obtains additional information about each contact by querying an online callsign database
(online databases supported currently include hamdb.org, callbook.info, and qrz.com).

## Installing and running JTmap
The program requires python version 3.7 or later. Before running the program a few dependencies need to be installed.
Here are instructions for installing these dependencies and running on Windows/OSX/Linux:

---
### For Linux

To download the program folder from guthub, use the following command line:

`git clone https://github.com/dschuurman/jtmap.git`

Note that if `git` is not already installed, it can be installed using the following command:

`sudo apt install git`

Python version 3.7 or later is required (tested using Python 3.x under Ubuntu 20.04).
This should be installed by default in most modern Linux distros.

To install the required dependencies, type the following in a terminal:

```
sudo apt install libatlas-base-dev python3-cartopy
pip3 install adif_io geopy matplotlib scipy
```
To run the program from the terminal, change directories into the program folder and type:
```
python3 jtmap.py
```

---
### For OSX

To download the program folder from guthub, use the following command line:

`git clone https://github.com/dschuurman/jtmap.git`

Note that if git is not already installed, install it using the following command (assuming you are using the Homebrew package manager):

`brew install git`

Python ver. 3.7 or later is required. To install dependencies, type the following in a terminal:

```
pip3 install adif_io geopy matplotlib scipy
brew install proj geos
pip3 install cartopy
pip3 install --upgrade certificates
```
To run the program from the terminal, change directories into the program folder and type:

`python3 jtmap.py`


---
### For Windows

Download the JTmap program from guthub (downloading using zip may be easiest) and extract the files into a local folder.

Next, download and install [Python version 3.8.x](https://www.python.org/downloads/windows/). Select "Add Python to PATH" during installation.

Next, download and install [miniconda](https://docs.conda.io/en/latest/miniconda.html). Select "Add miniconda to my PATH" during installation so it can be easily run in a terminal window.

Open a terminal window and type the following:

```
conda install -c conda-forge cartopy
pip install adif_io geopy
```

Once these dependencies are installed, open a terminal window, change directories into the local jtmap folder, and run the program as follows:

`python jtmap.py`

To launch the program by simply double clicking, use a plain text editor (like Notepad) and create a `pymap.bat` file in the 
same folder as `jtmap.py` which contains just the command shown above.
You should now be able to double-click on the `pymap.bat` file to launch the program.

---

### Configuring WSJT-X

Configure WSJT-X so that the UDP server is set to the IP address where JTmap
is running. If JTmap and WSJT-X are running on the same machine, WSJT-X should have the UDP 
server configured to the loopback interface (`127.0.0.1`, which is the default) and 
the `jtmap.conf` file should be set with `LOCALHOST = yes` (which is the default).
If WSJT-X and JTmap are running on different machines, set the IP address in WSJT-X
and the `LOCALHOST` setting in `jtmap.conf` accordingly. 

The `jtmap.conf` file contains additional configuration information that may be configured before
launching the program (if unsure, it should work "out of the box" using the defaults).
You may specify a precise latitude and longitude for your QTH which will be used for more
precise distance calculations (by default, distances are computed using your gridsquare).

Note that if you configure QRZ.com for callsign lookups, you will need to enter your QRZ.com
username and password in `jtmap.conf` since QRZ.com cannot be used anonymously.

One setup is compelte, launch JTmap and start WSJT-X then wait for contacts to be displayed in a pop-up
window showing a map of the contact.
