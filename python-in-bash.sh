#!/bin/bash

### https://hackaday.com/2021/05/04/linux-fu-mixing-bash-and-python/

echo Welcome to our shell script
 
python <<__EOF_PYTHON_SCRIPT
print 'Howdy from Python!'
__EOF_PYTHON_SCRIPT
 
echo "And we are back!"
