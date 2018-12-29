/*
 * Wiegand IO library in C for Python
 * 
 * Based on Wiegand API Raspberry Pi By Kyle Mallory All rights reserved.12/01/2013
 *
 */

#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <wiringPi.h>
#include <time.h>
#include <unistd.h>
#include <memory.h>
#include <string.h>

#define D0_PIN 6
#define D1_PIN 5

#define WIEGANDMAXDATA   32
#define WIEGANDTIMEOUT   3000000

static unsigned char __wiegandData[WIEGANDMAXDATA];    // can capture upto 32 bytes of data
static unsigned long __wiegandBitCount;                // number of bits currently captured
static struct timespec __wiegandBitTime;               // timestamp of the last bit received (used for timeouts)

void data0Pulse(void) {
    if (__wiegandBitCount / 8 < WIEGANDMAXDATA) {
        __wiegandData[__wiegandBitCount / 8] <<= 1;
        __wiegandBitCount++;
    }
    clock_gettime(CLOCK_MONOTONIC, &__wiegandBitTime);
}

void data1Pulse(void) {
    if (__wiegandBitCount / 8 < WIEGANDMAXDATA) {
        __wiegandData[__wiegandBitCount / 8] <<= 1;
        __wiegandData[__wiegandBitCount / 8] |= 1;
        __wiegandBitCount++;
    }
    clock_gettime(CLOCK_MONOTONIC, &__wiegandBitTime);
}

int wiegandInit(int d0pin, int d1pin) {
    //printf("Init Wiegand");
    wiringPiSetupGpio();
    pinMode(d0pin, INPUT);
    pinMode(d1pin, INPUT);
    wiringPiISR(d0pin, INT_EDGE_FALLING, data0Pulse);
    wiringPiISR(d1pin, INT_EDGE_FALLING, data1Pulse);
    return 0;
}

void wiegandReset(void) {
    memset((void *)__wiegandData, 0, WIEGANDMAXDATA);
    __wiegandBitCount = 0;
}

int wiegandGetPendingBitCount(void) {
    struct timespec now, delta;
    clock_gettime(CLOCK_MONOTONIC, &now);
    delta.tv_sec = now.tv_sec - __wiegandBitTime.tv_sec;
    delta.tv_nsec = now.tv_nsec - __wiegandBitTime.tv_nsec;

    if ((delta.tv_sec > 1) || (delta.tv_nsec > WIEGANDTIMEOUT))
        return __wiegandBitCount;

    return 0;
}

int wiegandReadData(void* data, int dataMaxLen) {
    if (wiegandGetPendingBitCount() > 0) {
        int bitCount = __wiegandBitCount;
        int byteCount = (__wiegandBitCount / 8) + 1;
        memcpy(data, (void *)__wiegandData, ((byteCount > dataMaxLen) ? dataMaxLen : byteCount));

        wiegandReset();
        return bitCount;
    }
    return 0;
}

void printbincharpad(char c, char *resarr)
{
    int i;
    memset(&resarr[0], 0, 9);
    for (i = 7; i >= 0; --i)
    {
     resarr[7-i] = ( (c & (1 << i)) ? '1' : '0' );
    }
}

static PyObject* py_initreader(PyObject* self, PyObject* args)
{
  int a;
  int b;
  if (!PyArg_ParseTuple(args, "ii", &a, &b)) {
      return NULL;
  }  
//  printf("%d\n", a);
//  printf("%d\n", b);
  wiegandInit(a,b);
  return Py_BuildValue("");
}

static PyObject* py_pendingbitcount(PyObject* self, PyObject* args)
{
  return Py_BuildValue("i",wiegandGetPendingBitCount());
}

static PyObject* py_wiegandread(PyObject* self, PyObject* args)
{
  char data[WIEGANDMAXDATA];
  char binstr[100];
  char bstr[9];
  int bitlen;
  int slen;
  int i;
  memset(&data[0], 0, WIEGANDMAXDATA);
  bitlen = wiegandReadData((void *)data,WIEGANDMAXDATA);
  memset(&binstr[0], 0, 100);
  slen = (bitlen / 8 + 1);
  for (i = 0; i<slen; i++)
  {
   printbincharpad(data[i],bstr);
   strcat(binstr,bstr);
//   printf("CP: %s\n",bstr);
  }
//  printf("Blen: %d\n",bitlen);
//  printf("DS: %s\n",data);
//  printf("BS: %s\n",binstr);
  return Py_BuildValue("si", binstr, bitlen);
}

static PyMethodDef wiegand_io_methods[] = {
  {"initreader", py_initreader, METH_VARARGS, ""},
  {"pendingbitcount", py_pendingbitcount, METH_NOARGS, ""},
  {"wiegandread", py_wiegandread, METH_NOARGS, ""},
  {0} 
};

static struct PyModuleDef wiegand_io =
{
    PyModuleDef_HEAD_INIT,
    "wiegand_io", /* name of module */
    "",          /* module documentation, may be NULL */
    -1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    wiegand_io_methods
};

PyMODINIT_FUNC PyInit_wiegand_io(void)
{
    return PyModule_Create(&wiegand_io);
}
