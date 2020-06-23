import rpieGlobals
import misc
if rpieGlobals.osinuse == "":
 rpieGlobals.osinuse = misc.getosname(0)
if rpieGlobals.osinuse=="linux":
 from linux_os import *
elif rpieGlobals.osinuse=="windows":
 from win_os import *
