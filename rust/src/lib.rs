//! Python bindings for Sentinel-1 decoder.
//!
//! This module provides Python bindings for the Rust implementation of the
//! Sentinel-1 FDBAQ and bypass decoders.
//!
//! # Module Organization
//!
//! - `huffman.rs`: Core Huffman decoder structures and lookup table building logic
//! - `huffman_codes.rs`: Huffman code tables for all 5 BRC values
//! - `fdbaq_decoder.rs`: Core FDBAQ decoding logic
//! - `bypass_decoder.rs`: Core bypass decoding logic
//! - `lib.rs`: Python bindings and module setup

use num_complex::Complex32;
use numpy::{IntoPyArray, PyArray2, PyArrayMethods};
use pyo3::conversion::IntoPyObject;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};

mod bypass_decoder;
mod fdbaq_decoder;
mod headers;
mod huffman;
mod huffman_codes;
mod lookup_tables;
mod sample_value_reconstruction;

use crate::bypass_decoder::{
    decode_batched_bypass_packets_inner, decode_single_bypass_packet_inner,
};
use crate::fdbaq_decoder::{decode_batched_fdbaq_packets_inner, decode_single_fdbaq_packet_inner};
use crate::headers::{decode_packet_headers_inner, PacketHeaderColumns};

/// Helper function for batched packet decoding.
///
/// This function handles the common logic of validating packets, extracting data,
/// running the decode function without holding the GIL, and creating the NumPy output array.
///
/// # Arguments
///
/// * `packets` - Python list of bytes objects
/// * `num_quads` - Number of quad samples to decode per packet
/// * `py` - Python GIL token
/// * `decode_fn` - Function that performs the actual batched decoding
fn decode_batched_packets_helper<F>(
    packets: &Bound<'_, PyList>,
    num_quads: usize,
    py: Python,
    decode_fn: F,
) -> PyResult<Py<PyAny>>
where
    F: FnOnce(&[Vec<u8>], usize) -> Result<Vec<Vec<Complex32>>, String> + Send,
{
    let num_packets = packets.len();

    // Validate all items are bytes first
    for (i, item) in packets.iter().enumerate() {
        if !item.is_instance_of::<PyBytes>() {
            return Err(PyValueError::new_err(format!(
                "packets[{}] must be bytes, got {}",
                i,
                item.get_type().name()?
            )));
        }
    }

    // Now extract the data
    let mut packet_data: Vec<Vec<u8>> = Vec::with_capacity(num_packets);
    for item in packets.iter() {
        let bytes_obj = item.cast::<PyBytes>()?;
        packet_data.push(bytes_obj.as_bytes().to_vec());
    }

    // Run the heavy work without holding the GIL
    let decoded_packets = py
        .detach(|| decode_fn(&packet_data, num_quads))
        .map_err(|e| PyValueError::new_err(e))?;

    let num_packets = decoded_packets.len();
    let samples_per_packet = num_quads * 2;

    // Allocate a 2D NumPy array: (num_packets, samples_per_packet)
    let output = PyArray2::<Complex32>::zeros(py, [num_packets, samples_per_packet], false);

    // Copy decoded data into NumPy array
    for (i, packet_samples) in decoded_packets.iter().enumerate() {
        debug_assert_eq!(packet_samples.len(), samples_per_packet);
        unsafe {
            std::ptr::copy_nonoverlapping(
                packet_samples.as_ptr(),
                output.uget_mut([i, 0]),
                samples_per_packet,
            );
        }
    }

    Ok(output.into())
}

#[pyfunction]
fn decode_batched_fdbaq_packets(
    packets: &Bound<'_, PyList>,
    num_quads: usize,
    py: Python,
) -> PyResult<Py<PyAny>> {
    decode_batched_packets_helper(packets, num_quads, py, decode_batched_fdbaq_packets_inner)
}

/// Decode FDBAQ (Flexible Dynamic Block Adaptive Quantization) data from Sentinel-1 packets.
///
/// This function extracts sample codes from FDBAQ-encoded data, which uses Huffman
/// encoding for efficient compression of radar echo data.
///
/// # Arguments
///
/// * `data` - Raw bytes containing the encoded data
/// * `num_quads` - Number of quad samples to decode
///
/// # Returns
///
/// A NumPy array of complex numbers representing the decoded samples. The samples are interleaved:
/// - `complex(IE[0], QE[0])`, `complex(IO[0], QO[0])`, `complex(IE[1], QE[1])`, `complex(IO[1], QO[1])`, ...
#[pyfunction]
fn decode_single_fdbaq_packet(data: &[u8], num_quads: usize, py: Python) -> PyResult<Py<PyAny>> {
    let complex_samples =
        decode_single_fdbaq_packet_inner(data, num_quads).map_err(|e| PyValueError::new_err(e))?;

    // Create NumPy array with complex64 dtype (two f32s per complex number)
    // into_pyarray creates a PyArray1<Complex32> which NumPy sees as complex64
    Ok(complex_samples.into_pyarray(py).to_owned().into())
}

/// Decode bypass data from Sentinel-1 packets.
///
/// This function decodes bypass-encoded data, where samples are encoded as simple
/// 10-bit signed integers (1 sign bit + 9 magnitude bits). This is used for
/// user data format types A and B ("Bypass" or "Decimation Only").
///
/// # Arguments
///
/// * `data` - Raw bytes containing the encoded data
/// * `num_quads` - Number of quad samples to decode
///
/// # Returns
///
/// A NumPy array of complex numbers representing the decoded samples. The samples are interleaved:
/// - `complex(IE[0], QE[0])`, `complex(IO[0], QO[0])`, `complex(IE[1], QE[1])`, `complex(IO[1], QO[1])`, ...
#[pyfunction]
fn decode_single_bypass_packet(data: &[u8], num_quads: usize, py: Python) -> PyResult<Py<PyAny>> {
    let complex_samples =
        decode_single_bypass_packet_inner(data, num_quads).map_err(|e| PyValueError::new_err(e))?;

    // Create NumPy array with complex64 dtype (two f32s per complex number)
    // into_pyarray creates a PyArray1<Complex32> which NumPy sees as complex64
    Ok(complex_samples.into_pyarray(py).to_owned().into())
}

#[pyfunction]
fn decode_batched_bypass_packets(
    packets: &Bound<'_, PyList>,
    num_quads: usize,
    py: Python,
) -> PyResult<Py<PyAny>> {
    decode_batched_packets_helper(packets, num_quads, py, decode_batched_bypass_packets_inner)
}

/// Convert the PacketHeaderColumns to a Python dictionary.
impl PacketHeaderColumns {
    fn into_pydict(self, py: Python<'_>) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);

        // Primary header fields
        dict.set_item("packet_ver_num", vec_u8_to_pylist(self.packet_ver_num, py)?)?;
        dict.set_item("packet_type", vec_u8_to_pylist(self.packet_type, py)?)?;
        dict.set_item(
            "secondary_header",
            vec_u8_to_pylist(self.secondary_header, py)?,
        )?;
        dict.set_item("pid", vec_u8_to_pylist(self.pid, py)?)?;
        dict.set_item("pcat", vec_u8_to_pylist(self.pcat, py)?)?;
        dict.set_item("sequence_flags", vec_u8_to_pylist(self.sequence_flags, py)?)?;
        dict.set_item("packet_sequence_count", self.packet_sequence_count)?;
        dict.set_item("packet_data_len", self.packet_data_len)?;

        // Datation service
        dict.set_item("TCOAR", self.tcoar)?;
        dict.set_item("TFINE", self.tfine)?;

        // Fixed ancillary data
        dict.set_item("SYNC", self.sync)?;
        dict.set_item("DTID", self.dtid)?;
        dict.set_item("ECC", self.ecc)?;
        dict.set_item("TSTMOD", self.tstmod)?;
        dict.set_item("RXCHID", self.rxchid)?;
        dict.set_item("ICID", self.icid)?;

        // Sub-commutated
        dict.set_item("ADWIDX", self.adwidx)?;
        dict.set_item("ADW", self.adw)?;

        // Counters
        dict.set_item("SPCT", self.spct)?;
        dict.set_item("PRICT", self.prict)?;

        // Radar configuration support
        dict.set_item("ERRFLG", self.errflg)?;
        dict.set_item("BAQMOD", self.baqmod)?;
        dict.set_item("BAQBL", self.baqbl)?;
        dict.set_item("RGDEC", self.rgdec)?;
        dict.set_item("RXG", self.rxg)?;
        dict.set_item("TXPRR", self.txprr)?;
        dict.set_item("TXPSF", self.txpsf)?;
        dict.set_item("TXPL", self.txpl)?;
        dict.set_item("RANK", self.rank)?;
        dict.set_item("PRI", self.pri)?;
        dict.set_item("SWST", self.swst)?;
        dict.set_item("SWL", self.swl)?;
        dict.set_item("SSBFLAG", self.ssbflag)?;
        dict.set_item("POL", self.pol)?;
        dict.set_item("TCMP", self.tcmp)?;
        dict.set_item("EBADR", self.ebadr)?;
        dict.set_item("ABADR", self.abadr)?;
        dict.set_item("SASTM", self.sastm)?;
        dict.set_item("CALTYP", self.caltyp)?;
        dict.set_item("CBADR", self.cbadr)?;
        dict.set_item("CALMOD", self.calmod)?;
        dict.set_item("TXPNO", self.txpno)?;
        dict.set_item("SIGTYP", self.sigtyp)?;
        dict.set_item("SWAP", self.swap)?;
        dict.set_item("SWATH", self.swath)?;

        // Radar sample count
        dict.set_item("NQ", self.nq)?;

        Ok(dict.into())
    }
}

/// Convert the user data bounds to a Python list of tuples.
fn bounds_to_pylist(bounds: Vec<(usize, usize)>, py: Python<'_>) -> PyResult<Py<PyList>> {
    let list = PyList::empty(py);
    for (start, end) in bounds {
        list.append((start, end))?;
    }
    Ok(list.into())
}

/// Convert a vector of u8 to a Python list.
/// This ensures it does not get interpreted as a python bytes object.
fn vec_u8_to_pylist(v: Vec<u8>, py: Python<'_>) -> PyResult<Py<PyList>> {
    let list = PyList::empty(py);
    for b in v {
        list.append(b)?;
    }
    Ok(list.into())
}

#[pyfunction]
fn decode_packet_headers(data: &[u8], py: Python) -> PyResult<Py<PyAny>> {
    let (columns, bounds) = decode_packet_headers_inner(data);

    let columns_dict = columns.into_pydict(py)?;
    let bounds_list = bounds_to_pylist(bounds, py)?;

    // Use into_pyobject for tuples with elements of different types (PyDict vs PyList)
    let ret_tuple = (columns_dict, bounds_list).into_pyobject(py)?;
    Ok(ret_tuple.into_any().unbind())
}

/// Initialize the Python module.
///
/// This function is called by Python when the module is imported. It registers
/// all the functions and types exposed to Python.
#[pymodule]
fn _sentinel1decoder(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(decode_single_fdbaq_packet, m)?)?;
    m.add_function(wrap_pyfunction!(decode_batched_fdbaq_packets, m)?)?;
    m.add_function(wrap_pyfunction!(decode_single_bypass_packet, m)?)?;
    m.add_function(wrap_pyfunction!(decode_batched_bypass_packets, m)?)?;
    m.add_function(wrap_pyfunction!(decode_packet_headers, m)?)?;
    Ok(())
}
