#########################
# WHOSBALL              #
#########################

# Automated foosball table



#########################
# SETUP PI              #
#########################

# Download Raspbian OS
# https://www.raspberrypi.org/downloads/raspbian/
# Download Etcher
# https://www.balena.io/etcher/

# Update packages, enable  camera & SSH
sudo apt update && sudo apt upgrade
sudo raspi-config

# Remove packages to reclaim ~1GB of space
sudo apt purge -y wolfram-engine libreoffice*
sudo apt clean && sudo apt -y autoremove

# Set default python version to python3
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2

# Install packages
#sudo apt install -y git python3-gpiozero python3-numpy python3-pip vim
sudo apt install -y vim
pip3 install --upgrade imutils


#########################
# INSTALL OPENCV        #
#########################

# Setup OpenCV
# https://www.pyimagesearch.com/2019/09/16/install-opencv-4-on-raspberry-pi-4-and-raspbian-buster/

# Install developer tools
sudo apt install -y build-essential cmake pkg-config

# Install image I/O packages so we can read image file formats (JPEG, PNG, TIFF, etc)
sudo apt install -y libjpeg-dev libtiff5-dev libjasper-dev libpng-dev

# Install video I/O packages so we can read video file formats and work directly with video streams
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev

# Install GTK development library and prerequisites (so we can compile the highgui module)
sudo apt install -y libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev libgtk2.0-dev libgtk-3-dev

# Install optimization libraries
sudo apt install -y libatlas-base-dev gfortran

# Install dependencies for opencv and so we can compile OpenCV with python bindings
sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5 python3-dev

# Install PiCamera API
pip3 install --upgrade "picamera[array]"

# Install OpenCV
pip3 install --upgrade opencv-contrib-python==4.1.0.25

# Install missing dependencies
# ImportError: libImath-2_2.so.12: cannot open shared object file: No such file or directory
# ImportError: libIlmImf-2_2.so.22: cannot open shared object file: No such file or directory
#sudo apt install -y libilmbase23 libopenexr-dev



#########################
# FINISH SETUP          #
#########################

# Clean up unused packages
sudo apt clean && sudo apt -y autoremove

# Python default version
python --version

# GPIO
pinout

# Camera
vcgencmd get_camera
raspistill -v -o test.jpg

# Clone GIT repo
git clone https://github.com/justinmiller24/whosball.git
cd whosball

# Shut down
sudo shutdown -h now
