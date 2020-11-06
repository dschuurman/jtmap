# JTmap
A program that listens for information sent from [WSJT-X](http://physics.princeton.edu/pulsar/K1JT/wsjtx.html)
and displays a friendly map with additional information after each contact is confirmed.

## Installing and running JTmap
The program requires python ver. 3.x. Before running the program a few dependencies need to be installed.
Here are instructions for installing these dependencies and running on Windows/OSX/Linux:

---
### For Linux

To download the program folder from guthub, use the following command line:

`git clone https://github.com/dschuurman/jtmap.git`

Note that if git is not already installed, it can be installed using the following command:

`sudo apt install git`

Python version 3.x is required (tested using Python 3.8.x under Ubuntu 20.04).
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

Python ver. 3.x is required. To install dependencies, type the following in a terminal:

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

Download the JTmap program from guthub (downloadng using zip may be easiest) and extract the files into local folder.

Next, download and install [Python version 3.x](https://www.python.org/downloads/windows/). Select "Add Python to PATH" during installation.

Next, download and install [miniconda](https://docs.conda.io/en/latest/miniconda.html). Select "Add miniconda to my PATH" during installation so it can be easily run in a terminal window.

Open a terminal window and type the following:

```
conda install -c conda-forge cartopy
pip install adif_io geopy
```

Once these dependencies are installed, open a terminal window. Change directories into your jtmap folder and run the program as follows:

`python jtmap.py`

To launch the program by simply double clicking, use a plain text editor (like Notepad) and create a `pymap.bat` file in the 
same folder as `jtmap.py` which contains just the command shown above.
You should now be able to double-click on the `pymap.bat` file to launch the program.

---

### Configuring WSJT-X

Configure WSJT-X so that the UDP server is set to the IP address where JTmap
is running (if it's the same machine, use the default which is the local loopback interface: 127.0.0.1).
Launch JTmap and start WSJT-X then wait for contacts to be displayed in a pop-up
window showing a map of the contact.

Note that `jtmap.py` and `jtmap.conf` should be kept in the same folder.
The `jtmap.conf` file contains configuration information that should be setup before
launching the program (if unsure, it should work "out of the box" using the defaults).

