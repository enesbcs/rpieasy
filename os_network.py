import rpieGlobals
import misc
if rpieGlobals.osinuse == "":
 rpieGlobals.osinuse = misc.getosname(0)
if rpieGlobals.osinuse=="linux":
 from linux_network import *
elif rpieGlobals.osinuse=="windows":
 from win_network import *
