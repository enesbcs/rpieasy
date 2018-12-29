#Run this script when you experiencing GPIO usage problems when running with non-root user!
sudo usermod -a -G gpio "$USER"
sudo chgrp gpio /sys/class/gpio/export
sudo chgrp gpio /sys/class/gpio/unexport
sudo chmod 775 /sys/class/gpio/export
sudo chmod 775 /sys/class/gpio/unexport
