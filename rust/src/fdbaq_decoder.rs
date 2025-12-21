//! FDBAQ decoder implementation.
//!
//! This module contains the core FDBAQ (Flexible Dynamic Block Adaptive Quantization)
//! decoding logic for Sentinel-1 packets.

use std::sync::LazyLock;
use rayon::prelude::*;
use num_complex::Complex32;

use crate::huffman::{HuffmanDecoderSampleCode, HuffmanDecodingState, HuffmanCode};
use crate::huffman_codes::get_huffman_codes;
use crate::sample_value_reconstruction::reconstruct_channel;

// Lazy static cache of decoders for each BRC value
static DECODERS: [LazyLock<HuffmanDecoderSampleCode>; 5] = [
    LazyLock::new(|| {
        let codes = get_huffman_codes(0);
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(1);
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(2);
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(3);
        HuffmanDecoderSampleCode::from_huffman_codes(codes)
    }),
    LazyLock::new(|| {
        let codes = get_huffman_codes(4);
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
) -> Result<Vec<(bool, u8)>, String> {
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
                return Err(format!("Invalid BRC value: {}", brc));
            }
            brcs.push(brc);

            let remaining_bits = boundary_state_bits & ((1 << (boundary_state_len - 3)) - 1);
            let remaining_len = boundary_state_len - 3;
            decoder = get_decoder(brc).ok_or_else(|| format!("Invalid BRC value: {}", brc))?;
            let (symbols, next_state) = decoder.read_bitstream(remaining_bits, remaining_len);
            initial_symbols = symbols;
            state = next_state;
        } else if read_thidx {
            // The first 8 bits of the boundary state are the THIDX. The remaining bits are symbols.
            let thidx = ((boundary_state_bits >> (boundary_state_len - 8)) & 0xFF) as u8;
            thidxs.push(thidx);

            brc = *brcs.get(block_idx).ok_or_else(|| format!("Not enough BRC codes for block {}", block_idx))?;
            let remaining_bits = boundary_state_bits & ((1 << (boundary_state_len - 8)) - 1);
            let remaining_len = boundary_state_len - 8;
            decoder = get_decoder(brc).ok_or_else(|| format!("Invalid BRC value: {}", brc))?;
            let (symbols, next_state) = decoder.read_bitstream(remaining_bits, remaining_len);
            initial_symbols = symbols;
            state = next_state;
        } else {
            brc = *brcs.get(block_idx).ok_or_else(|| format!("Not enough BRC codes for block {}", block_idx))?;
            decoder = get_decoder(brc).ok_or_else(|| format!("Invalid BRC value: {}", brc))?;
            let (symbols, next_state) = decoder.read_bitstream(boundary_state_bits, boundary_state_len);
            initial_symbols = symbols;
            state = next_state;
        }


        // Start with symbols from BRC byte (if any)
        let mut block_symbols = initial_symbols;

        // Decode remaining symbols for this block
        while block_symbols.len() < symbols_needed {
            if *byte_idx >= data.len() {
                return Err("Unexpected end of data when decoding symbols".to_string());
            }
            let byte = *data.get(*byte_idx)
                .ok_or_else(|| "Unexpected end of data when decoding symbols".to_string())?;
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
/// This is the pure Rust implementation that performs the actual decoding logic.
/// It has no Python dependencies and returns a Result with Vec<Complex32>.
///
/// # Arguments
///
/// * `data` - Raw bytes containing the encoded data
/// * `num_quads` - Number of quad samples to decode
///
/// # Returns
///
/// A vector of complex numbers representing the decoded samples. The samples are interleaved:
/// - `complex(IE[0], QE[0])`, `complex(IO[0], QO[0])`, `complex(IE[1], QE[1])`, `complex(IO[1], QO[1])`, ...
pub fn decode_single_fdbaq_packet_inner(data: &[u8], num_quads: usize) -> Result<Vec<Complex32>, String> {
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

    // Reconstruct the sample values
    let ie = reconstruct_channel(&s_ie, &brcs, &thidxs);
    let io = reconstruct_channel(&s_io, &brcs, &thidxs);
    let qe = reconstruct_channel(&s_qe, &brcs, &thidxs);
    let qo = reconstruct_channel(&s_qo, &brcs, &thidxs);

    // Combine channels into interleaved complex samples: IE[i]+QE[i]j, IO[i]+QO[i]j, ...
    let mut complex_samples = Vec::with_capacity(ie.len() * 2);
    for i in 0..ie.len() {
        complex_samples.push(Complex32::new(ie[i], qe[i]));  // IE[i] + QE[i]j
        complex_samples.push(Complex32::new(io[i], qo[i]));  // IO[i] + QO[i]j
    }

    Ok(complex_samples)
}


pub fn decode_batched_fdbaq_packets_inner(
    packets: &[Vec<u8>],
    num_quads: usize,
) -> Result<Vec<Vec<Complex32>>, String> {
    packets
        .par_iter()
        .map(|packet| decode_single_fdbaq_packet_inner(packet, num_quads))
        .collect()
}
