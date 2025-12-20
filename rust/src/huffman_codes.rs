//! Huffman code tables for Sentinel-1 FDBAQ decoding.
//!
//! This module contains the Huffman code tables for all 5 Bit Rate Code (BRC) values
//! used in Sentinel-1 FDBAQ encoding. The codes are derived from ESA documentation
//! and are stored as right-aligned bit patterns.

use super::huffman::HuffmanCode;

pub(crate) const TREE_BRC_ZERO_CODES: &[HuffmanCode<(bool, u8)>] = &[
    HuffmanCode { bits: 0b00, bit_len: 2, symbol: (false, 0) },
    HuffmanCode { bits: 0b10, bit_len: 2, symbol: (true, 0) },

    HuffmanCode { bits: 0b010, bit_len: 3, symbol: (false, 1) },
    HuffmanCode { bits: 0b110, bit_len: 3, symbol: (true, 1) },

    HuffmanCode { bits: 0b0110, bit_len: 4, symbol: (false, 2) },
    HuffmanCode { bits: 0b1110, bit_len: 4, symbol: (true, 2) },

    HuffmanCode { bits: 0b0111, bit_len: 4, symbol: (false, 3) },
    HuffmanCode { bits: 0b1111, bit_len: 4, symbol: (true, 3) },
];

pub(crate) const TREE_BRC_ONE_CODES: &[HuffmanCode<(bool, u8)>] = &[
    HuffmanCode { bits: 0b00, bit_len: 2, symbol: (false, 0) },
    HuffmanCode { bits: 0b10, bit_len: 2, symbol: (true, 0) },

    HuffmanCode { bits: 0b010, bit_len: 3, symbol: (false, 1) },
    HuffmanCode { bits: 0b110, bit_len: 3, symbol: (true, 1) },

    HuffmanCode { bits: 0b0110, bit_len: 4, symbol: (false, 2) },
    HuffmanCode { bits: 0b1110, bit_len: 4, symbol: (true, 2) },

    HuffmanCode { bits: 0b01110, bit_len: 5, symbol: (false, 3) },
    HuffmanCode { bits: 0b11110, bit_len: 5, symbol: (true, 3) },

    HuffmanCode { bits: 0b01111, bit_len: 5, symbol: (false, 4) },
    HuffmanCode { bits: 0b11111, bit_len: 5, symbol: (true, 4) },
];

pub(crate) const TREE_BRC_TWO_CODES: &[HuffmanCode<(bool, u8)>] = &[
    HuffmanCode { bits: 0b00, bit_len: 2, symbol: (false, 0) },
    HuffmanCode { bits: 0b10, bit_len: 2, symbol: (true, 0) },

    HuffmanCode { bits: 0b010, bit_len: 3, symbol: (false, 1) },
    HuffmanCode { bits: 0b110, bit_len: 3, symbol: (true, 1) },

    HuffmanCode { bits: 0b0110, bit_len: 4, symbol: (false, 2) },
    HuffmanCode { bits: 0b1110, bit_len: 4, symbol: (true, 2) },

    HuffmanCode { bits: 0b01110, bit_len: 5, symbol: (false, 3) },
    HuffmanCode { bits: 0b11110, bit_len: 5, symbol: (true, 3) },

    HuffmanCode { bits: 0b011110, bit_len: 6, symbol: (false, 4) },
    HuffmanCode { bits: 0b111110, bit_len: 6, symbol: (true, 4) },

    HuffmanCode { bits: 0b0111110, bit_len: 7, symbol: (false, 5) },
    HuffmanCode { bits: 0b1111110, bit_len: 7, symbol: (true, 5) },

    HuffmanCode { bits: 0b0111111, bit_len: 7, symbol: (false, 6) },
    HuffmanCode { bits: 0b1111111, bit_len: 7, symbol: (true, 6) },
];

pub(crate) const TREE_BRC_THREE_CODES: &[HuffmanCode<(bool, u8)>] = &[
    HuffmanCode { bits: 0b000, bit_len: 3, symbol: (false, 0) },
    HuffmanCode { bits: 0b100, bit_len: 3, symbol: (true, 0) },

    HuffmanCode { bits: 0b001, bit_len: 3, symbol: (false, 1) },
    HuffmanCode { bits: 0b101, bit_len: 3, symbol: (true, 1) },

    HuffmanCode { bits: 0b010, bit_len: 3, symbol: (false, 2) },
    HuffmanCode { bits: 0b110, bit_len: 3, symbol: (true, 2) },

    HuffmanCode { bits: 0b0110, bit_len: 4, symbol: (false, 3) },
    HuffmanCode { bits: 0b1110, bit_len: 4, symbol: (true, 3) },

    HuffmanCode { bits: 0b01110, bit_len: 5, symbol: (false, 4) },
    HuffmanCode { bits: 0b11110, bit_len: 5, symbol: (true, 4) },

    HuffmanCode { bits: 0b011110, bit_len: 6, symbol: (false, 5) },
    HuffmanCode { bits: 0b111110, bit_len: 6, symbol: (true, 5) },

    HuffmanCode { bits: 0b0111110, bit_len: 7, symbol: (false, 6) },
    HuffmanCode { bits: 0b1111110, bit_len: 7, symbol: (true, 6) },

    HuffmanCode { bits: 0b01111110, bit_len: 8, symbol: (false, 7) },
    HuffmanCode { bits: 0b11111110, bit_len: 8, symbol: (true, 7) },

    HuffmanCode { bits: 0b011111110, bit_len: 9, symbol: (false, 8) },
    HuffmanCode { bits: 0b111111110, bit_len: 9, symbol: (true, 8) },

    HuffmanCode { bits: 0b011111111, bit_len: 9, symbol: (false, 9) },
    HuffmanCode { bits: 0b111111111, bit_len: 9, symbol: (true, 9) },
];

pub(crate) const TREE_BRC_FOUR_CODES: &[HuffmanCode<(bool, u8)>] = &[
    HuffmanCode { bits: 0b000, bit_len: 3, symbol: (false, 0) },
    HuffmanCode { bits: 0b100, bit_len: 3, symbol: (true, 0) },

    HuffmanCode { bits: 0b0010, bit_len: 4, symbol: (false, 1) },
    HuffmanCode { bits: 0b1010, bit_len: 4, symbol: (true, 1) },

    HuffmanCode { bits: 0b0011, bit_len: 4, symbol: (false, 2) },
    HuffmanCode { bits: 0b1011, bit_len: 4, symbol: (true, 2) },

    HuffmanCode { bits: 0b0100, bit_len: 4, symbol: (false, 3) },
    HuffmanCode { bits: 0b1100, bit_len: 4, symbol: (true, 3) },

    HuffmanCode { bits: 0b0101, bit_len: 4, symbol: (false, 4) },
    HuffmanCode { bits: 0b1101, bit_len: 4, symbol: (true, 4) },

    HuffmanCode { bits: 0b01100, bit_len: 5, symbol: (false, 5) },
    HuffmanCode { bits: 0b11100, bit_len: 5, symbol: (true, 5) },

    HuffmanCode { bits: 0b01101, bit_len: 5, symbol: (false, 6) },
    HuffmanCode { bits: 0b11101, bit_len: 5, symbol: (true, 6) },

    HuffmanCode { bits: 0b01110, bit_len: 5, symbol: (false, 7) },
    HuffmanCode { bits: 0b11110, bit_len: 5, symbol: (true, 7) },

    HuffmanCode { bits: 0b011110, bit_len: 6, symbol: (false, 8) },
    HuffmanCode { bits: 0b111110, bit_len: 6, symbol: (true, 8) },

    HuffmanCode { bits: 0b0111110, bit_len: 7, symbol: (false, 9) },
    HuffmanCode { bits: 0b1111110, bit_len: 7, symbol: (true, 9) },

    HuffmanCode { bits: 0b011111100, bit_len: 9, symbol: (false, 10) },
    HuffmanCode { bits: 0b111111100, bit_len: 9, symbol: (true, 10) },

    HuffmanCode { bits: 0b011111101, bit_len: 9, symbol: (false, 11) },
    HuffmanCode { bits: 0b111111101, bit_len: 9, symbol: (true, 11) },

    HuffmanCode { bits: 0b0111111100, bit_len: 10, symbol: (false, 12) },
    HuffmanCode { bits: 0b1111111100, bit_len: 10, symbol: (true, 12) },

    HuffmanCode { bits: 0b0111111101, bit_len: 10, symbol: (false, 13) },
    HuffmanCode { bits: 0b1111111101, bit_len: 10, symbol: (true, 13) },

    HuffmanCode { bits: 0b0111111110, bit_len: 10, symbol: (false, 14) },
    HuffmanCode { bits: 0b1111111110, bit_len: 10, symbol: (true, 14) },

    HuffmanCode { bits: 0b0111111111, bit_len: 10, symbol: (false, 15) },
    HuffmanCode { bits: 0b1111111111, bit_len: 10, symbol: (true, 15) },
];

/// Get the Huffman codes for a given Bit Rate Code (BRC).
///
/// # Arguments
///
/// * `brc` - Bit Rate Code value (0-4)
///
/// # Returns
///
/// A reference to the Huffman code table for the given BRC.
///
/// # Panics
///
/// Panics if `brc` is not in the range 0-4.
pub(crate) fn get_huffman_codes(brc: u8) -> &'static [HuffmanCode<(bool, u8)>] {
    match brc {
        0 => TREE_BRC_ZERO_CODES,
        1 => TREE_BRC_ONE_CODES,
        2 => TREE_BRC_TWO_CODES,
        3 => TREE_BRC_THREE_CODES,
        4 => TREE_BRC_FOUR_CODES,
        _ => panic!("invalid BRC: expected 0-4"),
    }
}

// Get the number of possible unsigned sample values for a given BRC.
// We use this when building and accessing a lookup table for sample value reconstruction.
pub(crate) const NUM_OF_UNSIGNED_VALUES_PER_BRC: [usize; 5] = [
    TREE_BRC_ZERO_CODES.len() / 2,
    TREE_BRC_ONE_CODES.len() / 2,
    TREE_BRC_TWO_CODES.len() / 2,
    TREE_BRC_THREE_CODES.len() / 2,
    TREE_BRC_FOUR_CODES.len() / 2,
];
