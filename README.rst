================================
src.py: Libsamplerate for Python
================================

Description
-----------

This module provides a interface to libsamplerate (aka "Secret Rabbit Code").
The interface to libsamplerate was made with ctypes. Data input and outpus
happend over numpy arrays.

In contrast to most modules out there, this one implements the "Full API" of
libsamplerate. This allows to process data block by block and to change the
samplerate.

For more information, see: http://www.mega-nerd.com/SRC/api_full.html

Authors
-------

This code was written as part of of an assigment for the subject Voice 
Processing, by

- Juan I Carrano
- Juan M Oxoby
- Marcelo Lerendegui

Usage
-----

You must have libsamplerate installed on you system.

- Create an instance of Resampler
- Call the process() method of the Resampler object in order to process data.
- src_reset and src_set_ratio are implemented as Resampler.reset and 
  Resampler.set_ratio respectively.

This code has not been yet tested on Windows.
