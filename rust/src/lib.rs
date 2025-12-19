//! Python bindings for Sentinel-1 decoder.
//!
//! This module provides Python bindings for the Rust implementation of the
//! Sentinel-1 FDBAQ decoder.
//!
//! # Module Organization
//!
//! - `huffman.rs`: Core Huffman decoder structures and lookup table building logic
//! - `huffman_codes.rs`: Huffman code tables for all 5 BRC values
//! - `lib.rs`: Python bindings and module setup

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyList;

use std::sync::LazyLock;

mod huffman;
mod huffman_codes;

use crate::huffman::{HuffmanDecoderSampleCode, HuffmanDecodingState, HuffmanCode};
use crate::huffman_codes::get_huffman_codes;

// Lazy static cache of decoders for each BRC value
static DECODERS: [LazyLock<HuffmanDecoderSampleCode>; 5] = [
    LazyLock::new(|| {
        let codes = get_huffman_codes(0).unwrap();
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(1).unwrap();
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(2).unwrap();
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(3).unwrap();
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(4).unwrap();
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
];

/// Get the decoder for a given BRC value.
///
/// # Arguments
///
/// * `brc` - Bit Rate Code value (0-4)
///
/// # Returns
///
/// A reference to the decoder for the given BRC, or `None` if the BRC is invalid.
fn get_decoder(brc: u8) -> Option<&'static HuffmanDecoderSampleCode> {
    DECODERS.get(brc as usize).map(LazyLock::force)
}

/// Reconstruct the bitstream from the excess symbols and the Huffman codes.
///
/// Block boundaries do not line up with byte boundaries. Since we work byte-by-byte,
/// at block boundaries we sometimes return excess symbols beyond the 128th. We therefore
/// need a method of reconstructing the bits in the byte that were turned into excess symbols.
/// We can then use these to seed the decoding of the next block.
///
/// # Arguments
///
/// * `excess_symbols` - The excess symbols to reconstruct the bitstream from
/// * `excess_symbol_codes` - The Huffman codes used to turn bits into excess symbols
/// * `state` - The current state. This is the state of the Huffman decoder at the end of the byte containing the block boundary.
///
/// # Returns
///
/// The reconstructed bitstream
fn reconstruct_bitstream(excess_symbols: &Vec<(bool, u8)>, excess_symbol_codes: &Vec<HuffmanCode<(bool, u8)>>, state: HuffmanDecodingState) -> HuffmanDecodingState {
    let mut bitstream = state.state_bits;
    let mut bitstream_len = state.state_len;
    for symbol in excess_symbols.iter().rev() {
        let code = excess_symbol_codes.iter().find(|code| code.symbol == *symbol).unwrap();
        bitstream |= (code.bits as u16) << bitstream_len;
        bitstream_len += code.bit_len;
    }
    HuffmanDecodingState::new(bitstream, bitstream_len)
}


/// Decode a channel's data (one quarter of the quad data).
///
/// This function decodes a single channel (IE, IO, QE, or QO) which consists of
/// multiple BAQ blocks. Each block may have up to 128 symbols (or fewer for the last block).
///
/// # Arguments
///
/// * `data` - The raw byte data
/// * `byte_idx` - Current byte position in the data (will be updated)
/// * `num_quads` - Total number of quads to decode
/// * `num_baq_blocks` - Number of BAQ blocks
/// * `brcs` - Vector of BRC codes (will be updated if `read_brc` is true)
/// * `read_brc` - If true, read BRC from data; if false, reuse existing BRCs
///
/// # Returns
///
/// A vector of decoded symbols `(sign, magnitude)` tuples
fn decode_channel(
    data: &[u8],
    byte_idx: &mut usize,
    num_quads: usize,
    brcs: &mut Vec<u8>,
    thidxs: &mut Vec<u8>,
    read_brc: bool,
    read_thidx: bool,
) -> PyResult<Vec<(bool, u8)>> {
    let mut channel_symbols = Vec::new();
    let mut values_processed = 0;
    let mut state = HuffmanDecodingState::zero();

    let num_baq_blocks = (num_quads + 127) / 128;

    for block_idx in 0..num_baq_blocks {
        let symbols_needed = 128.min(num_quads - values_processed);

        // We need to handle the bits around the block boundary carefully. The previous block may have given us
        // enough bits for several symbols. On the other hand, it may have given us too few bits to reconstruct
        // this block's BRC or THIDX, if we need to read them. We therefore need to build a larger state made up
        // of the remaining bits from the previous byte and an addittional full byte, and then process it manually
        // rather than using a lookup table.
        // It's possible this full byte does not exist - one BRC and one symbol can be as few as 5 bits. We need
        // to handle this case gracefully.
        let boundary_state_bits: u32;
        let boundary_state_len: u8;
        if let Some(&byte) = data.get(*byte_idx) {
            boundary_state_bits = (state.state_bits as u32) << 8 | byte as u32;
            boundary_state_len = state.state_len + 8;
            *byte_idx += 1;
        } else {
            boundary_state_bits = state.state_bits as u32;
            boundary_state_len = state.state_len;
        }

        // Get or read BRC or THIDX from the boundary state, along with any symbols, then transition into table lookup mode.
        let brc;
        let initial_symbols;
        let decoder: &HuffmanDecoderSampleCode;

        if read_brc {
            // The first 3 bits of the boundary state are the BRC. The remaining bits are symbols.
            brc = ((boundary_state_bits >> (boundary_state_len - 3)) & 0x07) as u8;
            if brc >= 5 {
                return Err(PyValueError::new_err(format!("Invalid BRC value: {}", brc)));
            }
            brcs.push(brc);

            let remaining_bits = boundary_state_bits & ((1 << (boundary_state_len - 3)) - 1);
            let remaining_len = boundary_state_len - 3;
            decoder = get_decoder(brc).ok_or_else(|| PyValueError::new_err(format!("Invalid BRC value: {}", brc)))?;
            let (symbols, next_state) = decoder.read_bitstream(remaining_bits, remaining_len);
            initial_symbols = symbols;
            state = next_state;
        } else if read_thidx {
            // The first 8 bits of the boundary state are the THIDX. The remaining bits are symbols.
            let thidx = ((boundary_state_bits >> (boundary_state_len - 8)) & 0xFF) as u8;
            thidxs.push(thidx);

            brc = *brcs.get(block_idx).ok_or_else(|| PyValueError::new_err(format!("Not enough BRC codes for block {}", block_idx)))?;
            let remaining_bits = boundary_state_bits & ((1 << (boundary_state_len - 8)) - 1);
            let remaining_len = boundary_state_len - 8;
            decoder = get_decoder(brc).ok_or_else(|| PyValueError::new_err(format!("Invalid BRC value: {}", brc)))?;
            let (symbols, next_state) = decoder.read_bitstream(remaining_bits, remaining_len);
            initial_symbols = symbols;
            state = next_state;
        } else {
            brc = *brcs.get(block_idx).ok_or_else(|| PyValueError::new_err(format!("Not enough BRC codes for block {}", block_idx)))?;
            decoder = get_decoder(brc).ok_or_else(|| PyValueError::new_err(format!("Invalid BRC value: {}", brc)))?;
            let (symbols, next_state) = decoder.read_bitstream(boundary_state_bits, boundary_state_len);
            initial_symbols = symbols;
            state = next_state;
        }


        // Start with symbols from BRC byte (if any)
        let mut block_symbols = initial_symbols;

        // Decode remaining symbols for this block
        while block_symbols.len() < symbols_needed {
            if *byte_idx >= data.len() {
                return Err(PyValueError::new_err("Unexpected end of data when decoding symbols"));
            }
            let byte = *data.get(*byte_idx)
                .ok_or_else(|| PyValueError::new_err("Unexpected end of data when decoding symbols"))?;
            *byte_idx += 1;

            let state_id = state.to_state_id();
            let (new_symbols, next_state) = decoder.decode_byte(state_id, byte);

            block_symbols.extend(new_symbols);
            state = next_state;
        }

        // Take only the symbols we need (in case we decoded too many)
        if block_symbols.len() > symbols_needed {
            let excess_symbols = block_symbols.split_off(symbols_needed);
            let new_block_state = reconstruct_bitstream(&excess_symbols, &decoder.huffman_tree, state);
            state = new_block_state;
        }

        channel_symbols.extend(block_symbols);
        values_processed += symbols_needed;
    }

    // Align to 16-bit word boundary at the end of each channel
    if *byte_idx % 2 != 0 {
        *byte_idx += 1;
    }

    Ok(channel_symbols)
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
/// A tuple containing `(brcs, thidxs, s_ie, s_io, s_qe, s_qo)` where:
/// - `brcs`: Bit Rate Codes for each block
/// - `thidxs`: Threshold Index codes for each block
/// - `s_ie`: Even-indexed I channel sample codes (list of `(sign, magnitude)` tuples)
/// - `s_io`: Odd-indexed I channel sample codes (list of `(sign, magnitude)` tuples)
/// - `s_qe`: Even-indexed Q channel sample codes (list of `(sign, magnitude)` tuples)
/// - `s_qo`: Odd-indexed Q channel sample codes (list of `(sign, magnitude)` tuples)
#[pyfunction]
fn decode_fdbaq(data: &[u8], num_quads: usize, py: Python) -> PyResult<(PyObject, PyObject, Vec<(bool, u8)>, Vec<(bool, u8)>, Vec<(bool, u8)>, Vec<(bool, u8)>)> {
    let mut byte_idx = 0;

    let mut brcs: Vec<u8> = Vec::new();
    let mut thidxs: Vec<u8> = Vec::new();

    // Decode IE channel (reads BRCs)
    let s_ie = decode_channel(data, &mut byte_idx, num_quads, &mut brcs, &mut thidxs, true, false)?;

    // Decode IO channel (reuses BRCs)
    let s_io = decode_channel(data, &mut byte_idx, num_quads, &mut brcs, &mut thidxs, false, false)?;

    // Decode QE channel (reuses BRCs, reads THIDXs)
    let s_qe = decode_channel(data, &mut byte_idx, num_quads, &mut brcs, &mut thidxs, false, true)?;

    // Decode QO channel (reuses BRCs)
    let s_qo = decode_channel(data, &mut byte_idx, num_quads, &mut brcs, &mut thidxs, false, false)?;

    // Convert Vec<u8> to Python lists
    // Convert u8 to i32 so PyO3 treats them as Python ints in a list, not bytes
    let brcs_list = PyList::new(py, brcs.iter().map(|&x| x as i32))?.unbind();
    let thidxs_list = PyList::new(py, thidxs.iter().map(|&x| x as i32))?.unbind();

    Ok((
        brcs_list.into(),
        thidxs_list.into(),
        s_ie,
        s_io,
        s_qe,
        s_qo,
    ))
}

/// Initialize the Python module.
///
/// This function is called by Python when the module is imported. It registers
/// all the functions and types exposed to Python.
#[pymodule]
fn _sentinel1decoder(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(decode_fdbaq, m)?)?;
    Ok(())
}
