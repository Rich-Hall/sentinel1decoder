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

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::{PyList, PyBytes};
use numpy::{PyArray2, IntoPyArray, PyArrayMethods};
use num_complex::Complex32;

mod huffman;
mod huffman_codes;
mod lookup_tables;
mod sample_value_reconstruction;
mod fdbaq_decoder;
mod bypass_decoder;

use crate::fdbaq_decoder::{decode_single_fdbaq_packet_inner, decode_batched_fdbaq_packets_inner};
use crate::bypass_decoder::{decode_single_bypass_packet_inner, decode_batched_bypass_packets_inner};

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
            return Err(PyValueError::new_err(
                format!("packets[{}] must be bytes, got {}", i, item.get_type().name()?)
            ));
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
    let output = PyArray2::<Complex32>::zeros(
        py,
        [num_packets, samples_per_packet],
        false,
    );

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
    let complex_samples = decode_single_fdbaq_packet_inner(data, num_quads)
        .map_err(|e| PyValueError::new_err(e))?;

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
    let complex_samples = decode_single_bypass_packet_inner(data, num_quads)
        .map_err(|e| PyValueError::new_err(e))?;

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
    Ok(())
}
