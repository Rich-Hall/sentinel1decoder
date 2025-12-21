//! Bypass decoder implementation.
//!
//! This module contains the core bypass decoder logic for Sentinel-1 packets.
//! Bypass mode encodes samples as simple 10-bit signed integers (1 sign bit + 9 magnitude bits).

use rayon::prelude::*;
use num_complex::Complex32;

/// Convert a 10-bit unsigned integer to a signed integer.
///
/// The first bit is the sign, the next 9 bits are the magnitude.
///
/// # Arguments
///
/// * `ten_bit` - Raw 10-bit unsigned integer extracted from packet
///
/// # Returns
///
/// A signed integer value
fn ten_bit_unsigned_to_signed_int(ten_bit: u16) -> i16 {
    let sign = if (ten_bit >> 9) & 0x1 == 1 { -1 } else { 1 };
    sign * ((ten_bit & 0x1FF) as i16)
}

/// Decode a single channel's data (one quarter of the quad data).
///
/// This function decodes a single channel (IE, IO, QE, or QO) which consists of
/// 10-bit samples packed into bytes. Each sample is 10 bits (1 sign + 9 magnitude).
/// Four samples fit into 5 bytes (40 bits total).
///
/// # Arguments
///
/// * `data` - The raw byte data
/// * `start_byte_idx` - Starting byte position for this channel
/// * `num_quads` - Total number of quads to decode
///
/// # Returns
///
/// A vector of decoded sample values as f32
fn decode_channel(
    data: &[u8],
    start_byte_idx: usize,
    num_quads: usize,
) -> Result<Vec<f32>, String> {
    let mut channel_samples = Vec::with_capacity(num_quads);
    let mut samples_processed = 0;
    let mut byte_idx = start_byte_idx;

    while samples_processed < num_quads {
        // We extract 4 samples from every 5 bytes
        // Sample 1: bits 0-9 from bytes 0-1
        // Sample 2: bits 2-11 from bytes 1-2
        // Sample 3: bits 4-13 from bytes 2-3
        // Sample 4: bits 6-15 from bytes 3-4

        if samples_processed < num_quads {
            // Sample 1: (data[0] << 2 | data[1] >> 6) & 1023
            if byte_idx + 1 >= data.len() {
                return Err("Unexpected end of data when decoding channel".to_string());
            }
            let s_code = ((data[byte_idx] as u16) << 2 | (data[byte_idx + 1] as u16) >> 6) & 1023;
            channel_samples.push(ten_bit_unsigned_to_signed_int(s_code) as f32);
            samples_processed += 1;
        } else {
            break;
        }

        if samples_processed < num_quads {
            // Sample 2: (data[1] << 4 | data[2] >> 4) & 1023
            if byte_idx + 2 >= data.len() {
                return Err("Unexpected end of data when decoding channel".to_string());
            }
            let s_code = ((data[byte_idx + 1] as u16) << 4 | (data[byte_idx + 2] as u16) >> 4) & 1023;
            channel_samples.push(ten_bit_unsigned_to_signed_int(s_code) as f32);
            samples_processed += 1;
        } else {
            break;
        }

        if samples_processed < num_quads {
            // Sample 3: (data[2] << 6 | data[3] >> 2) & 1023
            if byte_idx + 3 >= data.len() {
                return Err("Unexpected end of data when decoding channel".to_string());
            }
            let s_code = ((data[byte_idx + 2] as u16) << 6 | (data[byte_idx + 3] as u16) >> 2) & 1023;
            channel_samples.push(ten_bit_unsigned_to_signed_int(s_code) as f32);
            samples_processed += 1;
        } else {
            break;
        }

        if samples_processed < num_quads {
            // Sample 4: (data[3] << 8 | data[4] >> 0) & 1023
            if byte_idx + 4 >= data.len() {
                return Err("Unexpected end of data when decoding channel".to_string());
            }
            let s_code = ((data[byte_idx + 3] as u16) << 8 | (data[byte_idx + 4] as u16) >> 0) & 1023;
            channel_samples.push(ten_bit_unsigned_to_signed_int(s_code) as f32);
            samples_processed += 1;
        } else {
            break;
        }

        byte_idx += 5;
    }

    Ok(channel_samples)
}

/// Decode bypass data from Sentinel-1 packets.
///
/// This is the pure Rust implementation that performs the actual decoding logic.
/// It has no Python dependencies and returns a Result with Vec<Complex32>.
///
/// Bypass mode encodes samples as simple 10-bit signed integers (1 sign bit + 9 magnitude bits).
/// The data is arranged into IE, IO, QE, QO channels, and each channel is zero-padded
/// to the next 16-bit word boundary.
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
pub fn decode_single_bypass_packet_inner(data: &[u8], num_quads: usize) -> Result<Vec<Complex32>, String> {
    // Calculate the number of bytes per channel (aligned to 16-bit word boundary)
    // Each channel needs ceil((10 * num_quads) / 16) * 2 bytes
    let num_words = ((num_quads * 10 + 15) / 16) as usize;  // Round up to next 16-bit word
    let num_bytes_per_channel = num_words * 2;

    // Decode IE channel (starts at byte 0)
    let ie = decode_channel(data, 0, num_quads)?;

    // Decode IO channel (starts at num_bytes_per_channel)
    let io = decode_channel(data, num_bytes_per_channel, num_quads)?;

    // Decode QE channel (starts at 2 * num_bytes_per_channel)
    let qe = decode_channel(data, 2 * num_bytes_per_channel, num_quads)?;

    // Decode QO channel (starts at 3 * num_bytes_per_channel)
    let qo = decode_channel(data, 3 * num_bytes_per_channel, num_quads)?;

    // Combine channels into interleaved complex samples: IE[i]+QE[i]j, IO[i]+QO[i]j, ...
    let mut complex_samples = Vec::with_capacity(ie.len() * 2);
    for i in 0..ie.len() {
        complex_samples.push(Complex32::new(ie[i], qe[i]));  // IE[i] + QE[i]j
        complex_samples.push(Complex32::new(io[i], qo[i]));  // IO[i] + QO[i]j
    }

    Ok(complex_samples)
}

pub fn decode_batched_bypass_packets_inner(
    packets: &[Vec<u8>],
    num_quads: usize,
) -> Result<Vec<Vec<Complex32>>, String> {
    packets
        .par_iter()
        .map(|packet| decode_single_bypass_packet_inner(packet, num_quads))
        .collect()
}
