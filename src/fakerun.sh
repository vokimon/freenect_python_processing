#!/bin/bash

PREFIX=${PREFIX:-~/local}

if [ "$1" == "setup" ]
then
	for package in thanksgiving0 legos0 sophie0
	do
		wget http://dl.dropbox.com/u/15736519/$package.tar.bz2
		tar xvfj $package.tar.bz2
	done
else
	export FAKENECT_PATH=thanksgiving0
	export FAKENECT_PATH=kinectcaptures/record-people
	export LD_LIBRARY_PATH=$PREFIX/lib/fakenect/:$PREFIX/lib/ 
	echo LD_LIBRARY_PATH: $LD_LIBRARY_PATH
	$*
fi

