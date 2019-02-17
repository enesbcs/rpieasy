#include <Python.h>
#include "rc-switch/RCSwitch.h"
#include <wiringPi.h>
#include <stdio.h> // printf only!

using namespace std;

class RF: public RCSwitch {
 public:
  RF():RCSwitch()
  {
   this->initok=0;
  }

  int initpin() {
   if (this->initok==0) {
    try {
     if (wiringPiSetupGpio() < 0) {
      this->initok=0;
      this->disableReceive();
      this->disableTransmit();
     } else {
      this->initok=1;
     }
    } catch (...) {
     this->initok=0;
    }
   }
   return this->initok;
  }

  int isinitok() {
   return this->initok;
  }
 private:
  int initok;
};

PyObject* construct(PyObject* self, PyObject* args)
{
 RF* rf = new RF();
 PyObject* rfCapsule = PyCapsule_New((void *)rf, "RFPtr", NULL);
 PyCapsule_SetPointer(rfCapsule, (void *)rf);
 return Py_BuildValue("O",rfCapsule);
}

PyObject* initpin(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 return Py_BuildValue("I",rf->initpin());
}

PyObject* isinitok(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 return Py_BuildValue("I",rf->isinitok());
}

PyObject* setProtocol(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 unsigned int protocol_;
 PyArg_ParseTuple(args, "OI", &rfCapsule_,&protocol_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->setProtocol(protocol_);
 return Py_BuildValue("");
}

PyObject* setPulseLength(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 unsigned int pulselength_;
 PyArg_ParseTuple(args, "OI", &rfCapsule_,&pulselength_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->setPulseLength(pulselength_);
 return Py_BuildValue("");
}

PyObject* setRepeatTransmit(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 unsigned int repeat_;
 PyArg_ParseTuple(args, "OI", &rfCapsule_,&repeat_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->setRepeatTransmit(repeat_);
 return Py_BuildValue("");
}

PyObject* setReceiveTolerance(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 unsigned int percent_;
 PyArg_ParseTuple(args, "OI", &rfCapsule_,&percent_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->setReceiveTolerance(percent_);
 return Py_BuildValue("");
}

PyObject* enableTransmit(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 int pin_ = -1;
 PyArg_ParseTuple(args, "Oi", &rfCapsule_, &pin_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 if (rf->isinitok()==1) {
  rf->enableTransmit(pin_);
 }
 return Py_BuildValue("");
}

PyObject* disableTransmit(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->disableTransmit();
 return Py_BuildValue("");
}

PyObject* send_binstr(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 const char * sCodeWord_;
 PyArg_ParseTuple(args, "Os", &rfCapsule_,&sCodeWord_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->send(sCodeWord_);
 return Py_BuildValue("");
}

PyObject* send(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 unsigned long code_ = 0;
 unsigned int length_ = 0;
// printf("send called");
 PyArg_ParseTuple(args, "OkI", &rfCapsule_,&code_,&length_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
// printf("code [%i] length [%i]",code_,length_);
 rf->send(code_,length_);
 return Py_BuildValue("");
}

PyObject* enableReceive(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 int pin_ = -1;
 PyArg_ParseTuple(args, "Oi", &rfCapsule_, &pin_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 if ((rf->isinitok()==1) && (pin_ != -1)) {
  rf->enableReceive(pin_);
 }
 return Py_BuildValue("");
}

PyObject* disableReceive(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->disableReceive();
 return Py_BuildValue("");
}

PyObject* available(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 int retval;
 if (rf->available()) {
  retval = 1;
 } else {
 retval = 0;
 }
 return Py_BuildValue("i",retval);
}

PyObject* resetAvailable(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->resetAvailable();
 return Py_BuildValue("");
}

PyObject* getReceivedValue(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 return Py_BuildValue("k",rf->getReceivedValue());
}

PyObject* getReceivedBitlength(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 return Py_BuildValue("I",rf->getReceivedBitlength());
}

PyObject* getReceivedProtocol(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 return Py_BuildValue("I",rf->getReceivedProtocol());
}

PyObject* delete_object(PyObject* self, PyObject* args)
{
 PyObject* rfCapsule_;
 PyArg_ParseTuple(args, "O", &rfCapsule_);
 RF* rf = (RF*)PyCapsule_GetPointer(rfCapsule_, "RFPtr");
 rf->disableReceive();
 rf->disableTransmit();
 delete rf;
 return Py_BuildValue("");
}

PyMethodDef cRFFunctions[] =  // define functions to export
{
 {"construct", construct, METH_VARARGS, "Create RF object"},
 {"initpin", initpin, METH_VARARGS, "Init wiringpi in BCM mode"},
 {"isinitok", isinitok, METH_VARARGS, "1 if wiringpi init successful"},
 {"setProtocol", setProtocol, METH_VARARGS, "Set transmit protocol"},
 {"setPulseLength", setPulseLength, METH_VARARGS, "Set transmit pulse length"},
 {"setRepeatTransmit", setRepeatTransmit, METH_VARARGS, "Set transmit repeat time"},
 {"setReceiveTolerance", setReceiveTolerance, METH_VARARGS, "Set receiver tolerance"},
 {"enableTransmit", enableTransmit, METH_VARARGS, "Enable transmitting on specified pin"},
 {"disableTransmit", disableTransmit, METH_VARARGS, "Disable transmitting"},
 {"send_binstr", send_binstr, METH_VARARGS, "Sending binary string data"},
 {"send", send, METH_VARARGS, "Sending integer with specified bitlength"},
 {"enableReceive", enableReceive, METH_VARARGS, "Enable receiving on specified pin"},
 {"disableReceive", disableReceive, METH_VARARGS, "Disable receiving"},
 {"available", available, METH_VARARGS, "1 if code received, otherwise 0"},
 {"resetAvailable", resetAvailable, METH_VARARGS, "Reset code receiver buffer"},
 {"getReceivedValue", getReceivedValue, METH_VARARGS, "Get received code"},
 {"getReceivedBitlength", getReceivedBitlength, METH_VARARGS, "Get received bitlength"},
 {"getReceivedProtocol", getReceivedProtocol, METH_VARARGS, "Get received code bitlength"},
 {"delete_object",delete_object,METH_VARARGS,"Delete RF object"},
 { NULL, NULL,0,NULL}
};

struct PyModuleDef cRFModule = // define structures
{
 PyModuleDef_HEAD_INIT,
 "py_rcswitch",                // module name
 NULL,
 -1,
 cRFFunctions
};

PyMODINIT_FUNC PyInit_py_rcswitch(void)
{
 return PyModule_Create(&cRFModule);
}
