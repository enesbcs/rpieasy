from distutils.core import setup, Extension
module = Extension('wiegand_io', sources=['wiegand_io.c'],
libraries = ['wiringPi','pthread','rt'],
extra_compile_args=['-lpthread', '-lrt', '-I/usr/local/include', '-L/usr/local/lib','-lwiringPi'])
setup(ext_modules=[module],name='Wiegand_IO',install_requires=["wiringPi"])
