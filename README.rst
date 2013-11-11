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

Quick-start
~~~~~~~~~~~

- Create an instance of Resampler
- Call the process() method of the Resampler object in order to process data.
- src_reset and src_set_ratio are implemented as Resampler.reset and 
  Resampler.set_ratio respectively.

More
~~~~

There are three ways of using src.py

- Call process() repeteadly with blocks of data. When processing the last block
  set the "end_of_input" keyword argument in process.
- Just like above, call process() repeteadly with blocks of data, but do not set
  the "end_of_input" flag. After processing all blocks, call end_input to gather
  any remaining output frames.
- Call process_iter() with an iterator yielding input blocks and an iterator
  yielding resample ratios, or just a number specifying a fixed ratio.
  process_iter() is a generator that will yield output blocks.

TODO
----

This code has not been yet tested on Windows.
