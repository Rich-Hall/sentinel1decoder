//! Huffman decoder implementation for FDBAQ data.
//!
//! This module provides structures and functions for decoding Huffman-encoded
//! data from Sentinel-1 packets using lookup tables.

use std::collections::HashSet;

/// A Huffman code is a bit pattern that maps to a symbol.
///
/// The symbol type `T` can be any type that implements `Clone` (and optionally `Copy` for better performance).
/// Common choices are `u8`, `u16`, `i32`, or tuples like `(bool, u8)`.
#[derive(Clone)]
pub(crate) struct HuffmanCode<T> {
    pub(crate) bits: u16,      // The bit pattern (right-aligned)
    pub(crate) bit_len: u8,    // Number of bits in the code
    pub(crate) symbol: T,      // The decoded symbol/magnitude value
}

/// A lookup table entry for Huffman decoding.
///
/// We read our data stream byte by byte and look up the resulting symbols in a table.
/// We have no guarantee that the data stream will be aligned to a byte boundary, so we
/// need to handle partial bytes. Therefore, a lookup table entry produces a list of
/// symbols, as well as any leftover bits (the state) that we need to carry over to the next byte.
pub(crate) struct HuffmanTableEntry<T> {
    pub(crate) symbols: Vec<T>,
    pub(crate) next_state: HuffmanDecodingState,
}

impl<T> Default for HuffmanTableEntry<T> {
    fn default() -> Self {
        Self {
            symbols: Vec::new(),
            next_state: HuffmanDecodingState::zero(),
        }
    }
}

#[derive(Clone, Copy, Hash, Eq, PartialEq)]
pub(crate) struct HuffmanDecodingState {
    // We need to keep track of both bits and bit lengths to distinguish e.g. 0b0 from 0b00 from 0b000 from 0b0000, etc.
    pub(crate) state_bits: u16,
    pub(crate) state_len: u8,
}

impl HuffmanDecodingState {
    /// Create a new decoding state from bits and bit length.
    pub(crate) fn new(state_bits: u16, state_len: u8) -> Self {
        Self { state_bits, state_len }
    }

    /// Create a zero state (no leftover bits).
    pub(crate) fn zero() -> Self {
        Self { state_bits: 0, state_len: 0 }
    }

    /// Calculate state ID from leftover bits and bit length.
    ///
    /// State IDs are assigned sequentially by bit length, then by value.
    /// For a given length `n`, there are `2^n` possible states.
    /// States with length `n` are assigned IDs from `(2^n - 1)` to `(2^(n+1) - 2)`.
    ///
    /// Examples:
    /// - State (bits=0, len=0) → ID = 0
    /// - State (bits=0, len=1) → ID = 1
    /// - State (bits=1, len=1) → ID = 2
    /// - State (bits=0, len=2) → ID = 3
    /// - State (bits=3, len=2) → ID = 6
    ///
    /// # Returns
    ///
    /// A unique state ID that encodes both the bit length and value.
    pub(crate) fn to_state_id(self) -> u16 {
        let base = if self.state_len == 0 {
            0
        } else {
            (1u16 << self.state_len) - 1
        };
        base + self.state_bits
    }
}

/// A Huffman decoder using pre-computed lookup tables.
///
/// This decoder maps a state and a byte to a list of symbols, the next state, and the next length.
/// The lookup tables are pre-computed for efficient byte-wise decoding.
///
/// The symbol type `T` must implement `Clone` to allow storing symbols in vectors.
/// For best performance, `T` should also implement `Copy` to avoid cloning overhead.
pub(crate) struct HuffmanDecoder<T> {
    pub(crate) entries: Vec<[HuffmanTableEntry<T>; 256]>,
    pub(crate) huffman_tree: Vec<HuffmanCode<T>>,
}

// pub(crate) type HuffmanDecoderU8 = HuffmanDecoder<u8>;
pub(crate) type HuffmanDecoderSampleCode = HuffmanDecoder<(bool, u8)>;

impl<T: Clone> HuffmanDecoder<T> {

    /// Build a lookup table decoder from a set of Huffman codes.
    ///
    /// This constructor:
    /// 1. Enumerates all possible states (leftover bit patterns)
    /// 2. For each state and each possible input byte, determines:
    ///    - Which symbols are decoded
    ///    - The next state (remaining leftover bits)
    ///
    /// # Arguments
    ///
    /// * `codes` - Slice of Huffman codes to build the decoder from
    ///
    /// # Returns
    ///
    /// A `HuffmanDecoder` instance with pre-computed lookup tables.
    pub(crate) fn from_huffman_codes(codes: &[HuffmanCode<T>]) -> Self {
        // Sort codes by length (shortest first) once for optimal matching performance.
        // Huffman trees are typically constructed with shorter codes matching more common symbols.
        let mut sorted_codes: Vec<HuffmanCode<T>> = codes.to_vec();
        sorted_codes.sort_by_key(|c| c.bit_len);

        // Build a set of all possible states.
        let mut states: HashSet<HuffmanDecodingState> = HashSet::new();
        states.insert(HuffmanDecodingState::zero());
        for huffman_code in &sorted_codes {
            let mut bits = huffman_code.bits;
            let mut bit_len = huffman_code.bit_len;
            while bit_len > 1 {
                bits >>= 1;
                bit_len -= 1;
                states.insert(HuffmanDecodingState::new(bits, bit_len));
            }
        }

        // Now build the lookup table
        let max_state_id = states.iter()
            .map(|state| state.to_state_id())
            .max()
            .unwrap_or(0);

        let mut lookup_table = Vec::with_capacity((max_state_id + 1) as usize);

        for _ in 0..=(max_state_id as usize) {
            let arr: [HuffmanTableEntry<T>; 256] = std::array::from_fn(|_| HuffmanTableEntry::default());
            lookup_table.push(arr);
        }

        for state in states {
            let state_id = state.to_state_id();
            for byte_val in 0..=255u8 {
                // The bitstream is the concatenation of the state bits and the byte value bits.
                let bitstream = (state.state_bits as u32) << 8 | byte_val as u32;
                let bitstream_len = state.state_len + 8;

                let (symbols, leftover_state) = Self::read_bitstream_impl(bitstream, bitstream_len, &sorted_codes);

                let table_entry = HuffmanTableEntry::<T> {
                    symbols,
                    next_state: leftover_state,
                };

                lookup_table[state_id as usize][byte_val as usize] = table_entry;
            }
        }

        HuffmanDecoder::<T> {
            entries: lookup_table,
            huffman_tree: sorted_codes,
        }
    }

    /// Core implementation for decoding a bitstream against Huffman codes.
    ///
    /// This is the internal implementation that can be used both during construction
    /// (where `self` doesn't exist yet) and by instance methods.
    ///
    /// # Arguments
    ///
    /// * `bitstream` - The bitstream to decode (right-aligned in the u32)
    /// * `bitstream_len` - The number of valid bits in the bitstream
    /// * `codes` - Slice of Huffman codes to match against
    ///
    /// # Returns
    ///
    /// A tuple containing:
    /// - `Vec<T>`: Decoded symbols
    /// - `HuffmanDecodingState`: Leftover state (bits and bit length)
    fn read_bitstream_impl(bitstream: u32, bitstream_len: u8, codes: &[HuffmanCode<T>]) -> (Vec<T>, HuffmanDecodingState) {
        let mut bitstream = bitstream;
        let mut bitstream_len = bitstream_len;
        let mut symbols = Vec::new();

        while bitstream_len > 0 {
            let mut matched = false;

            for code in codes.iter() {
                if code.bit_len <= bitstream_len {
                    // Extract the top 'code.bit_len' bits from the bitstream.
                    // We shift right by (bitstream_len - code.bit_len) to align the
                    // most significant bits, then mask to get exactly code.bit_len bits.
                    let extracted = (bitstream >> (bitstream_len - code.bit_len)) & ((1 << code.bit_len) - 1);

                    // Compare with code (both should be right-aligned)
                    if extracted as u16 == (code.bits & ((1 << code.bit_len) - 1)) {
                        symbols.push(code.symbol.clone());
                        // Remove matched bits: mask off the top bits
                        bitstream = bitstream & ((1 << (bitstream_len - code.bit_len)) - 1);
                        bitstream_len -= code.bit_len;
                        matched = true;
                        break;
                    }
                }
            }

            if !matched {
                break;
            }
        }

        (symbols, HuffmanDecodingState::new(bitstream as u16, bitstream_len))
    }

    /// Decode a bitstream using this decoder's Huffman codes.
    ///
    /// This method extracts symbols from a bitstream by matching against the decoder's
    /// stored Huffman codes. It can be used with any bitstream length (e.g., 5 bits for
    /// BRC remaining bits, 8 bits for a full byte, or 8+state bits).
    ///
    /// # Arguments
    ///
    /// * `bitstream` - The bitstream to decode (right-aligned in the u32)
    /// * `bitstream_len` - The number of valid bits in the bitstream
    ///
    /// # Returns
    ///
    /// A tuple containing:
    /// - `Vec<T>`: Decoded symbols
    /// - `HuffmanDecodingState`: Leftover state (bits and bit length)
    pub(crate) fn read_bitstream(&self, bitstream: u32, bitstream_len: u8) -> (Vec<T>, HuffmanDecodingState) {
        Self::read_bitstream_impl(bitstream, bitstream_len, &self.huffman_tree)
    }

    /// Decode a byte given the current state.
    ///
    /// This method looks up the byte in the pre-computed lookup table for the
    /// given state and returns any decoded symbols along with the next state.
    ///
    /// # Arguments
    ///
    /// * `state_id` - Current state ID (leftover bits from previous decoding)
    /// * `byte` - Input byte to decode
    ///
    /// # Returns
    ///
    /// A tuple containing:
    /// - `Vec<T>`: Decoded symbols from this byte (may be empty)
    /// - `HuffmanDecodingState`: Next state for subsequent decoding
    pub(crate) fn decode_byte(&self, state_id: u16, byte: u8) -> (Vec<T>, HuffmanDecodingState) {
        let table_entry = &self.entries[state_id as usize][byte as usize];
        (table_entry.symbols.clone(), table_entry.next_state)
    }

}
