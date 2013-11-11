#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  src.py
#
#  Made for VOX 2013
#  by
#  J I Carrano
#  M Lerendegui
#  J M Oxoby
#
"""
Sample rate conversion using libsamplerate (aka "Secret Rabbit Code")

This module implements the "full API" of libsamplerate using ctypes.
Data inputs and ouputs is done via numpy arrays.

Note: Libsamplerate uses floats for samples. Numpy defaults to using doubles
    (float64). This means data should be converted. This module will do the
    conversion automatically. However, for improved efficiency is is recommended
    that you create arrays as float in the first place.

For details on the API, see http://www.mega-nerd.com/SRC/api_full.html
"""

import ctypes
import ctypes.util
import numpy as np
from itertools import repeat

# try to load libsamplerate
LIBNAME = "samplerate"

ext_lib_name = ctypes.util.find_library(LIBNAME)
if not ext_lib_name:
    raise RuntimeError("Cannot find libsamplerate")

c_src = ctypes.cdll.LoadLibrary(ext_lib_name)

# Libsamplerate uses floats for samples.

_SAMPLE_FORMAT = ctypes.c_float
_SAMPLE_FORMAT_dtype = np.float32
_SAMPLE_BYTES = ctypes.sizeof(_SAMPLE_FORMAT)

# This structure is used to pass data to the resampler

class _SRC_DATA(ctypes.Structure):
    """
    data_in       : A pointer to the input data samples.
    input_frames  : The number of frames of data pointed to by data_in.
    data_out      : A pointer to the output data samples.
    output_frames : Maximum number of frames pointer to by data_out.
    src_ratio     : Equal to output_sample_rate / input_sample_rate.
    end_of_input  : Equal to 0 if more input data is available and 1
                      otherwise.
    """
    _fields_ = [
        ("data_in", ctypes.POINTER(ctypes.c_float)),
        ("data_out", ctypes.POINTER(ctypes.c_float)),
        ("input_frames", ctypes.c_long),
        ("output_frames", ctypes.c_long),
        ("input_frames_used", ctypes.c_long),
        ("output_frames_gen", ctypes.c_long),
        ("end_of_input", ctypes.c_int),
        ("src_ratio", ctypes.c_double),
    ]


# Converter types

_MIN_CONVERTER = 0
SINC_BEST = 0
SINC_MEDIUM = 1
SINC_FASTEST = 2
ZERO_ORDER_HOLD = 3
LINEAR = 4
_MAX_CONVERTER = 4

def _get_error_str(n):
    """Convert numeric code into a error string

    calls:
            const char* src_strerror (int error) ;
    """
    spointer = c_src.src_strerror(n);
    return ctypes.c_char_p(spointer).value

def _fail(r):
    """Parse the return code of C functions and raise an exception if there is
    an error.
    """
    if r != 0:
        msg = _get_error_str(r)
        raise RuntimeError(msg)

class Resampler(object):
    """The resampler object takes a block of samples and outputs a resampled signal
    It is is used to resample a long signal by feeding it block by block.
    Blocks do not need to be the same size.
    """
    def __init__(self, converter_type, channels = 1, default_ratio = None):
        """Create a new resampler object.

        Input:
            converter_type: mus be one of SINC_BEST, SINC_MEDIUM, SINC_FASTEST,
                            ZERO_ORDER_HOLD, LINEAR
            channels: Number of input channels.
            ratio: Default resampling ratio
        """
        if not _MIN_CONVERTER <= converter_type <= _MAX_CONVERTER:
            raise ValueError("Invalid value for parameter 'converter_type'")

        err_code = ctypes.c_int()
        self._state = c_src.src_new(int(converter_type), int(channels),
                                                        ctypes.byref(err_code))

        if self._state == 0:
            _fail(err_code)

        self.channels = channels
        self.converter_type = converter_type
        self.default_ratio = default_ratio

        # this is to determine the size of the last output buffer
        self.frames_remaining = 0.0

    def process(self, data_in, ratio = None, end_of_input = False):
        """Process a block of samples

        Input:
            data_in: A numpy array on input samples. In the case of multi-channel
                input, each channel must be in a column
            ratio: The resampling ratio. Changing this parameter will cause a
                smooth transition between the old and new ratio. If you want an
                abrupt change, use "set_ratio()". If this parameter is None, then
                the default ratio will be used. If the default ratio is not set,
                i.e., it is None, a error will be raised.
            end_of_input: Set this flag to True when you want to process the last
                block of input

        Output:
                (data_out, input_frames_used)
            Where:
                data_out: Resampled data. The 'dtype' for this array is the one
                    used by libsamplerate
                input_frames_used: Number of input frames used in the conversion
        """

        try:
            actual_ratio = float(ratio or self.default_ratio)
        except TypeError:
            raise RuntimeError("'ratio' not given and default ratio not set")

        # for an explanation on the memory layout of a numpy array, see
        # http://docs.scipy.org/doc/numpy/reference/arrays.ndarray.html#internal-memory-layout-of-an-ndarray

        # Now let'see if we have the correct number of channels
        if data_in.ndim > 2:  # array too big
            raise ValueError("data_in has more than 2 dimensions")

        if self.channels > 1 and (data_in.ndim < 2
                                    or data_in.shape[1] != self.channels):
            raise ValueError("data_in must have the same number of columns as channels")

        if self.channels == 1:
            in_squeezed = data_in.squeeze()
            if in_squeezed.ndim > 2 or (in_squeezed.ndim == 2
                                        and(0 not in in_squeezed.shape
                                            and 1 not in in_squeezed.shape)):
                raise ValueError("data_in has more than one non-singleton dimension but Resampler has one channel")

        # now lets check out the strides. We need the input to be in interleaved
        # format, which means that traversing the array linearly in memory is the
        # same as traversing its rows.

        if data_in.strides[-1] != data_in.itemsize:
            raise ValueError("data_in has incorrect memory layout. The stride for the last dimension must be one entry")

        # Lets convert the array to src's sample format
        data_in_formatted = (data_in.astype(_SAMPLE_FORMAT_dtype) if
                            data_in.dtype != _SAMPLE_FORMAT_dtype else data_in)

        data_in_raw = data_in_formatted.ctypes.data_as(ctypes.POINTER(_SAMPLE_FORMAT))
        data_in_frames = data_in_formatted.size / self.channels

        # Let's build the out array
        self.frames_remaining += data_in_frames * actual_ratio

        data_out_frames0 = self.frames_remaining if end_of_input else data_in_frames * actual_ratio
        data_out_frames = int(np.ceil(data_out_frames0)) + 1
        data_out = np.ndarray((data_out_frames, self.channels),
                                    dtype = _SAMPLE_FORMAT_dtype, order = 'C')
        data_out_raw = data_out.ctypes.data_as(ctypes.POINTER(_SAMPLE_FORMAT))

        srcdata = _SRC_DATA(
                        data_in = data_in_raw, data_out = data_out_raw,

                        input_frames = data_in_frames, output_frames = data_out_frames,

                        end_of_input = int(end_of_input),

                        src_ratio = ctypes.c_double(actual_ratio)
                    )

        # do the real processing
        _fail(c_src.src_process(self._state, ctypes.byref(srcdata)))

        input_frames_used = srcdata.input_frames_used
        real_data_out = data_out[:srcdata.output_frames_gen,:]

        self.frames_remaining -= srcdata.output_frames_gen

        return real_data_out, input_frames_used

    def end_input(self, ratio = None):
        """Signal an end-of-input and return the last output samples.

        This function is equivalent to calling process() with zero input frames.

        Output:
            (data_out, input_frames_used)

            Note that input_frames_used will probaby be different from zero even
            though we are calling process with zero samples, due to buffering
            from previous frames.
        """
        return self.process(np.empty((0, self.channels)), ratio = ratio,
                                                            end_of_input = True)

    def process_iter(self, iterable, ratio = None):
        """Iterate over "iterable", converting each block.

        Ratio can be another iterable yieldig the conversion ratios, or it can be
        a value. ratio = None will use the default ratio.

        This iterator calls process with the values yielded for iterable.
        At the end of the iteration, end_input is called and an extra block is
        output.
        The values yielded are blocks of data NOT tuples as returned process()
        """
        iterobj = iter(iterable)
        try:
            iterratios = iter(ratios)
        except TypeError:
            iterratios = repeat(ratios)

        while True:
            try:
                in_block = next(iterobj)
                this_ratio = next(iterratios)
            except StopIteration:
                break

            yield self.process(in_block, this_ratio)[0]

        try:
            this_ratio = next(iterratios)
        except StopIteration:
            pass

        yield end_input(this_ratio)[0]


    def set_default_ratio(self, new_default_ratio):
        """Change the default ratio
        """
        self.default_ratio = new_default_ratio

    def set_ratio(self, new_ratio):
        """Abruptly change sample rate

        calls:
                int src_set_ratio (SRC_STATE *state, double new_ratio) ;
        """
        _fail(c_src.src_set_ratio(self._state, float(new_ratio)))

    def reset(self):
        """Reset Resampler to initial state

        calls:
                int src_reset (SRC_STATE *state) ;
        """
        self.frames_remaining = 0.0
        _fail(c_src.src_reset(self._state))

    def __del__(self):
        """Free the state pointer

        calls:
                SRC_STATE* src_delete (SRC_STATE *state) ;
        """
        #try
        c_src.src_delete(self._state)
        #except AttributeError:
        #    pass
