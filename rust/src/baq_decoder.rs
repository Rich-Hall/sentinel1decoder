//! BAQ decoder implementation.
//!
//! This module contains the core BAQ (Block Adaptive Quantization) decoding logic for Sentinel-1 packets.
//! It supports 3-bit, 4-bit and 5-bit BAQ modes.

use rayon::prelude::*;
use num_complex::Complex32;
use crate::sample_value_reconstruction::reconstruct_unsigned_sample_value_baq;


/// Extract an integer of the given width from a bitstream at a bit offset.
///
/// Handles extraction across byte boundaries (at most two bytes since the max bit width in BAQ modes is 5 bits).
#[inline(always)]
fn extract_bits(data: &[u8], bit_offset: usize, num_bits: usize) -> u8 {
    let byte_start = bit_offset / 8;
    let byte_end = (bit_offset + num_bits - 1) / 8;

    if byte_start == byte_end {
        let bit_shift = 8 - (bit_offset % 8) - num_bits;
        (data[byte_start] >> bit_shift) & ((1 << num_bits) - 1) as u8
    } else {
        let bits_in_first = 8 - (bit_offset % 8);
        let bits_in_second = num_bits - bits_in_first;

        let first_part = data[byte_start] & ((1 << bits_in_first) - 1) as u8;
        let second_part = data[byte_end] >> (8 - bits_in_second);

        (first_part << bits_in_second) | second_part
    }
}

pub fn decode_single_baq_packet_inner(data: &[u8], num_quads: usize, baq_bits: u8) -> Result<Vec<Complex32>, String> {
    // Number of BAQ blocks (128 quads per block)
    let num_baq_blocks = (num_quads + 127) / 128;

    // Compute word counts (in 16-bit words) for each channel based on BAQ bit width
    let nw_ie_io_qo = ((baq_bits as usize * num_quads + 15) / 16) as usize;
    let nw_qe = ((baq_bits as usize * num_quads + 8 * num_baq_blocks + 15) / 16) as usize;

    let ie_len = nw_ie_io_qo * 2;
    let io_len = nw_ie_io_qo * 2;
    let qe_len = nw_qe * 2;
    let qo_len = nw_ie_io_qo * 2;

    if data.len() < ie_len + io_len + qe_len + qo_len {
        return Err(format!("Data too short for BAQ {} decoding. Expected minimum {} bytes, got {}", baq_bits, ie_len + io_len + qe_len + qo_len, data.len()));
    }

    let ie_data = &data[0..ie_len];
    let io_data = &data[ie_len..ie_len + io_len];
    let qe_data = &data[ie_len + io_len..ie_len + io_len + qe_len];
    let qo_data = &data[ie_len + io_len + qe_len..];

    let mut out = Vec::with_capacity(num_quads * 2);

    for block_idx in 0..num_baq_blocks {
        let block_start_quad = block_idx * 128;
        let block_end_quad = std::cmp::min(block_start_quad + 128, num_quads);
        let block_size = block_end_quad - block_start_quad;

        // THIDX is stored at the start of each block in the QE channel
        let qe_thidx_bit_offset = block_start_quad * baq_bits as usize + block_idx * 8;
        let thidx = extract_bits(qe_data, qe_thidx_bit_offset, 8);

        for q in 0..block_size {
            let quad_idx = block_start_quad + q;
            let bit_offset_normal = quad_idx * baq_bits as usize;

            // Decode IE 
            let ie_bits = extract_bits(ie_data, bit_offset_normal, baq_bits as usize);
            let ie_sign = (ie_bits >> (baq_bits - 1)) & 1 == 1;
            let ie_mcode = ie_bits & ((1 << (baq_bits - 1)) - 1);
            let ie_mag = reconstruct_unsigned_sample_value_baq(ie_mcode, baq_bits, thidx);
            let ie_val = if ie_sign { -ie_mag } else { ie_mag };

            // Decode IO
            let io_bits = extract_bits(io_data, bit_offset_normal, baq_bits as usize);
            let io_sign = (io_bits >> (baq_bits - 1)) & 1 == 1;
            let io_mcode = io_bits & ((1 << (baq_bits - 1)) - 1);
            let io_mag = reconstruct_unsigned_sample_value_baq(io_mcode, baq_bits, thidx);
            let io_val = if io_sign { -io_mag } else { io_mag };

            // Decode QE
            // QE samples are preceded by THIDX bytes for each block, so adjust offset
            let qe_bit_offset = bit_offset_normal + (block_idx + 1) * 8;
            let qe_bits = extract_bits(qe_data, qe_bit_offset, baq_bits as usize);
            let qe_sign = (qe_bits >> (baq_bits - 1)) & 1 == 1;
            let qe_mcode = qe_bits & ((1 << (baq_bits - 1)) - 1);
            let qe_mag = reconstruct_unsigned_sample_value_baq(qe_mcode, baq_bits, thidx);
            let qe_val = if qe_sign { -qe_mag } else { qe_mag };

            // Decode QO
            let qo_bits = extract_bits(qo_data, bit_offset_normal, baq_bits as usize);
            let qo_sign = (qo_bits >> (baq_bits - 1)) & 1 == 1;
            let qo_mcode = qo_bits & ((1 << (baq_bits - 1)) - 1);
            let qo_mag = reconstruct_unsigned_sample_value_baq(qo_mcode, baq_bits, thidx);
            let qo_val = if qo_sign { -qo_mag } else { qo_mag };

            out.push(Complex32::new(ie_val, qe_val));
            out.push(Complex32::new(io_val, qo_val));
        }
    }

    Ok(out)
}

pub fn decode_batched_baq_packets_inner(
    packets: &[Vec<u8>],
    num_quads: usize,
    baq_bits: u8,
) -> Result<Vec<Vec<Complex32>>, String> {
    packets
        .par_iter()
        .map(|packet| decode_single_baq_packet_inner(packet, num_quads, baq_bits))
        .collect()
}
