from distutils.core import setup, Extension
module = Extension('py_rcswitch', sources=['py_rcswitch.cpp','rc-switch/RCSwitch.cpp'],
libraries = ['wiringPi','wiringPiDev','crypt'],
extra_compile_args=['-DRPI','-lcrypt', '-lwiringPiDev', '-I/usr/local/include', '-L/usr/local/lib','-Lrc-switch/','-lwiringPi'])
setup(ext_modules=[module],name='py_rcswitch',install_requires=["wiringPi"])
