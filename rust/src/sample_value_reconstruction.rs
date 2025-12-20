use crate::lookup_tables::*;
use crate::huffman_codes::NUM_OF_UNSIGNED_VALUES_PER_BRC;

use std::sync::LazyLock;

static UNSIGNED_SAMPLE_VALUE_TABLE: LazyLock<Vec<f32>> = LazyLock::new(|| {
    let mut table = Vec::new();
    for brc in 0..5 {
        let mcode_count = NUM_OF_UNSIGNED_VALUES_PER_BRC[brc as usize];
        for thidx in 0..256 {
            for mcode in 0..mcode_count {
                table.push(reconstruct_unsigned_sample_value(mcode as u8, brc as u8, thidx as u8));
            }
        }
    }

    table
});

// We're using a flat lookup table for BRC/THIDX combos.
// There are always 256 possible THIDXs, and a variable number of mcodes per each BRC
const LOOKUP_TABLE_BRC_OFFSETS: [usize; 5] = [
    0,
    256*NUM_OF_UNSIGNED_VALUES_PER_BRC[0],
    256*(NUM_OF_UNSIGNED_VALUES_PER_BRC[0] + NUM_OF_UNSIGNED_VALUES_PER_BRC[1]),
    256*(NUM_OF_UNSIGNED_VALUES_PER_BRC[0] + NUM_OF_UNSIGNED_VALUES_PER_BRC[1] + NUM_OF_UNSIGNED_VALUES_PER_BRC[2]),
    256*(NUM_OF_UNSIGNED_VALUES_PER_BRC[0] + NUM_OF_UNSIGNED_VALUES_PER_BRC[1] + NUM_OF_UNSIGNED_VALUES_PER_BRC[2] + NUM_OF_UNSIGNED_VALUES_PER_BRC[3]),
];

#[inline(always)]
fn get_lookup_table_block_offset(brc: u8, thidx: u8) -> usize {
    LOOKUP_TABLE_BRC_OFFSETS[brc as usize] + (thidx as usize) * NUM_OF_UNSIGNED_VALUES_PER_BRC[brc as usize]
}

#[inline(always)]
fn lookup_unsigned_sample_value(mcode: u8, brc: u8, thidx: u8) -> f32 {
    let offset = get_lookup_table_block_offset(brc, thidx);
    let idx = offset + (mcode as usize);
    *UNSIGNED_SAMPLE_VALUE_TABLE.get(idx).unwrap()
}

#[cold]
#[inline(never)]
fn unhandled_reconstruction_case( mcode: u8, brc: u8, thidx: u8) -> ! {
    panic!("Unhandled reconstruction case: mcode={}, brc={}, thidx={}", mcode, brc, thidx);
}

#[inline(always)]
pub fn reconstruct_unsigned_sample_value(mcode: u8, brc: u8, thidx: u8) -> f32 {
    match brc {
        0 => {
            if thidx <= 3 {
                if mcode < 3 {
                    mcode as f32
                } else if mcode == 3 {
                    B0[thidx as usize]
                } else {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
            } else {
                if mcode >= 4 {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
                NRL_B0[mcode as usize] * SIGMA_FACTORS[thidx as usize]
            }
        }
        1 => {
            if thidx <= 3 {
                if mcode < 4 {
                    mcode as f32
                } else if mcode == 4 {
                    B1[thidx as usize]
                } else {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
            } else {
                if mcode >= 5 {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
                NRL_B1[mcode as usize] * SIGMA_FACTORS[thidx as usize]
            }
        }
        2 => {
            if thidx <= 5 {
                if mcode < 6 {
                    mcode as f32
                } else if mcode == 6 {
                    B2[thidx as usize]
                } else {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
            } else {
                if mcode >= 7 {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
                NRL_B2[mcode as usize] * SIGMA_FACTORS[thidx as usize]
            }
        }
        3 => {
            if thidx <= 6 {
                if mcode < 9 {
                    mcode as f32
                } else if mcode == 9 {
                    B3[thidx as usize]
                } else {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
            } else {
                if mcode >= 10 {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
                NRL_B3[mcode as usize] * SIGMA_FACTORS[thidx as usize]
            }
        }
        4 => {
            if thidx <= 8 {
                if mcode < 15 {
                    mcode as f32
                } else if mcode == 15 {
                    B4[thidx as usize]
                } else {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
            } else {
                if mcode >= 16 {
                    unhandled_reconstruction_case(mcode, brc, thidx);
                }
                NRL_B4[mcode as usize] * SIGMA_FACTORS[thidx as usize]
            }
        }
        _ => {
            unhandled_reconstruction_case(mcode, brc, thidx);
        }
    }
}

#[inline(always)]
pub fn reconstruct_channel(data: &[(bool, u8)], brcs: &[u8], thidxs: &[u8]) -> Vec<f32> {
    if brcs.len() != thidxs.len() {
        panic!("Mismatched lengths of BRC and THIDX arrays");
    }

    let vals_to_process = data.len();

    let mut out_vals = Vec::with_capacity(vals_to_process);
    let mut n = 0;

    for (&brc, &thidx) in brcs.iter().zip(thidxs.iter()) {
        let data_remaining = data.len() - n;
        let samples_in_block = 128.min(data_remaining);

        if samples_in_block == 0 {
            break;
        }

        for (sign, mcode) in data[n..n + samples_in_block].iter() {
            let sign_mult = if *sign { -1.0 } else { 1.0 };
            out_vals.push(sign_mult * lookup_unsigned_sample_value(*mcode, brc, thidx));
        }

        n += samples_in_block;
    }

    out_vals
}
