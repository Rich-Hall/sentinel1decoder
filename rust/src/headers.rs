/// Columnar representation of packet headers.
/// Primary header fields: one value per packet (always present).
/// Secondary header fields: Option for each packet (absent when secondary header flag is 0).
/// Field widths match the SAR Space Protocol Data Unit spec (S1-IF-ASD-PL-0007).
///
/// Field names match the code names in the specification.
/// Translations to human-readable names are provided in the python `field_names` module.
#[derive(Debug, Default)]
pub struct PacketHeaderColumns {
    // -------------------------------------------------------------------------
    // Primary header fields (6 bytes total)
    // -------------------------------------------------------------------------
    pub packet_ver_num: Vec<u8>,         // 3 bits
    pub packet_type: Vec<u8>,            // 1 bit
    pub secondary_header: Vec<u8>,       // 1 bit
    pub pid: Vec<u8>,                    // 7 bits
    pub pcat: Vec<u8>,                   // 4 bits
    pub sequence_flags: Vec<u8>,         // 2 bits
    pub packet_sequence_count: Vec<u16>, // 14 bits
    pub packet_data_len: Vec<u16>,       // 16 bits

    // -------------------------------------------------------------------------
    // Secondary header fields - Datation service (6 bytes)
    // -------------------------------------------------------------------------
    pub tcoar: Vec<Option<u32>>, // 4 bytes
    pub tfine: Vec<Option<u16>>, // 2 bytes

    // -------------------------------------------------------------------------
    // Secondary header fields - Fixed ancillary data (14 bytes)
    // -------------------------------------------------------------------------
    pub sync: Vec<Option<u32>>,  // 4 bytes
    pub dtid: Vec<Option<u32>>,  // 4 bytes
    pub ecc: Vec<Option<u8>>,    // 1 byte
    pub tstmod: Vec<Option<u8>>, // 3 bits
    pub rxchid: Vec<Option<u8>>, // 4 bits
    pub icid: Vec<Option<u32>>,  // 4 bytes

    // -------------------------------------------------------------------------
    // Secondary header fields - Sub-commutated ancillary data (3 bytes)
    // -------------------------------------------------------------------------
    pub adwidx: Vec<Option<u8>>, // 1 byte
    pub adw: Vec<Option<u16>>,   // 2 bytes

    // -------------------------------------------------------------------------
    // Secondary header fields - Counters service (8 bytes)
    // -------------------------------------------------------------------------
    pub spct: Vec<Option<u32>>,  // 4 bytes
    pub prict: Vec<Option<u32>>, // 4 bytes

    // -------------------------------------------------------------------------
    // Secondary header fields - Radar configuration support service (27 bytes)
    // -------------------------------------------------------------------------
    pub errflg: Vec<Option<u8>>,  // 1 bit
    pub baqmod: Vec<Option<u8>>,  // 5 bits
    pub baqbl: Vec<Option<u8>>,   // 1 byte
    pub rgdec: Vec<Option<u8>>,   // 1 byte
    pub rxg: Vec<Option<u8>>,     // 1 byte
    pub txprr: Vec<Option<u16>>,  // 2 bytes
    pub txpsf: Vec<Option<u16>>,  // 2 bytes
    pub txpl: Vec<Option<u32>>,   // 3 bytes (24 bits)
    pub rank: Vec<Option<u8>>,    // 5 bits
    pub pri: Vec<Option<u32>>,    // 3 bytes (24 bits)
    pub swst: Vec<Option<u32>>,   // 3 bytes (24 bits)
    pub swl: Vec<Option<u32>>,    // 3 bytes (24 bits)
    pub ssbflag: Vec<Option<u8>>, // 1 bit
    pub pol: Vec<Option<u8>>,     // 3 bits
    pub tcmp: Vec<Option<u8>>,    // 2 bits
    pub ebadr: Vec<Option<u8>>,   // 4 bits (imaging mode)
    pub abadr: Vec<Option<u16>>,  // 10 bits (imaging mode)
    pub sastm: Vec<Option<u8>>,   // 1 bit (calibration mode)
    pub caltyp: Vec<Option<u8>>,  // 3 bits (calibration mode)
    pub cbadr: Vec<Option<u16>>,  // 10 bits (calibration mode)
    pub calmod: Vec<Option<u8>>,  // 2 bits
    pub txpno: Vec<Option<u8>>,   // 5 bits
    pub sigtyp: Vec<Option<u8>>,  // 4 bits
    pub swap: Vec<Option<u8>>,    // 1 bit
    pub swath: Vec<Option<u8>>,   // 1 byte

    // -------------------------------------------------------------------------
    // Secondary header fields - Radar sample count service (3 bytes)
    // -------------------------------------------------------------------------
    pub nq: Vec<Option<u16>>, // 2 bytes
}

const PRIMARY_HEADER_LEN: usize = 6;
const SECONDARY_HEADER_LEN: usize = 62;

/// Decode the primary header from bytes.
///
/// The primary header consists of exactly 6 bytes.
/// Returns the secondary header flag and the packet data length,
/// as we need these values to decode the secondary header.
fn decode_primary_header(
    primary_header_bytes: &[u8; PRIMARY_HEADER_LEN],
    output_columns: &mut PacketHeaderColumns,
) -> (u8, u16) {
    let tmp16 = u16::from_be_bytes([primary_header_bytes[0], primary_header_bytes[1]]);
    let packet_version_number = (tmp16 >> 13) as u8; // Bit 0-2
    let packet_type = ((tmp16 >> 12) & 0x01) as u8; // Bit 3
    let secondary_header_flag = ((tmp16 >> 11) & 0x01) as u8; // Bit 4
    let process_id = ((tmp16 >> 4) & 0x7F) as u8; // Bit 5-11
    let packet_category = (tmp16 & 0xF) as u8; // Bit 12-15

    let tmp16 = u16::from_be_bytes([primary_header_bytes[2], primary_header_bytes[3]]);
    let sequence_flags = (tmp16 >> 14) as u8; // Bit 0-1
    let packet_seq_count = tmp16 & 0x3FFF; // Bit 2-15

    let tmp16 = u16::from_be_bytes([primary_header_bytes[4], primary_header_bytes[5]]);
    let packet_data_len = tmp16 + 1; // Bit 0-15

    output_columns.packet_ver_num.push(packet_version_number);
    output_columns.packet_type.push(packet_type);
    output_columns.secondary_header.push(secondary_header_flag);
    output_columns.pid.push(process_id);
    output_columns.pcat.push(packet_category);
    output_columns.sequence_flags.push(sequence_flags);
    output_columns.packet_sequence_count.push(packet_seq_count);
    output_columns.packet_data_len.push(packet_data_len);

    (secondary_header_flag, packet_data_len)
}

/// Decode the secondary header from bytes.
///
/// The secondary header consists of exactly 62 bytes.
/// It is only present when the secondary header flag is 1.
/// The secondary header is decoded into the output columns.
fn decode_secondary_header(
    secondary_header_bytes: &[u8; SECONDARY_HEADER_LEN],
    output_columns: &mut PacketHeaderColumns,
) {
    // ---------------------------------------------------------
    // Datation service (6 bytes)
    // ---------------------------------------------------------
    let tcoar = u32::from_be_bytes([
        secondary_header_bytes[0],
        secondary_header_bytes[1],
        secondary_header_bytes[2],
        secondary_header_bytes[3],
    ]);
    let tfine = u16::from_be_bytes([secondary_header_bytes[4], secondary_header_bytes[5]]);

    output_columns.tcoar.push(Some(tcoar));
    output_columns.tfine.push(Some(tfine));

    // ---------------------------------------------------------
    // Fixed ancillary data (14 bytes)
    // ---------------------------------------------------------
    let sync = u32::from_be_bytes([
        secondary_header_bytes[6],
        secondary_header_bytes[7],
        secondary_header_bytes[8],
        secondary_header_bytes[9],
    ]);
    let dtid = u32::from_be_bytes([
        secondary_header_bytes[10],
        secondary_header_bytes[11],
        secondary_header_bytes[12],
        secondary_header_bytes[13],
    ]);
    let ecc = secondary_header_bytes[14];
    // Byte 15 bit 1 is unused
    let tstmod = ((secondary_header_bytes[15] >> 4) & 0x07) as u8; // Byte 15 Bits 1-3
    let rxchid = (secondary_header_bytes[15] & 0x0F) as u8; // Byte 15 Bits 4-7
    let icid = u32::from_be_bytes([
        secondary_header_bytes[16],
        secondary_header_bytes[17],
        secondary_header_bytes[18],
        secondary_header_bytes[19],
    ]);

    output_columns.sync.push(Some(sync));
    output_columns.dtid.push(Some(dtid));
    output_columns.ecc.push(Some(ecc));
    output_columns.tstmod.push(Some(tstmod));
    output_columns.rxchid.push(Some(rxchid));
    output_columns.icid.push(Some(icid));

    // ---------------------------------------------------------
    // Sub-commutated ancillary data (3 bytes)
    // ---------------------------------------------------------
    let adwidx = secondary_header_bytes[20];
    let adw = u16::from_be_bytes([secondary_header_bytes[21], secondary_header_bytes[22]]);

    output_columns.adwidx.push(Some(adwidx));
    output_columns.adw.push(Some(adw));

    // ---------------------------------------------------------
    // Counters service (8 bytes)
    // ---------------------------------------------------------
    let spct = u32::from_be_bytes([
        secondary_header_bytes[23],
        secondary_header_bytes[24],
        secondary_header_bytes[25],
        secondary_header_bytes[26],
    ]);
    let prict = u32::from_be_bytes([
        secondary_header_bytes[27],
        secondary_header_bytes[28],
        secondary_header_bytes[29],
        secondary_header_bytes[30],
    ]);

    output_columns.spct.push(Some(spct));
    output_columns.prict.push(Some(prict));

    // ---------------------------------------------------------
    // Radar configuration support service (27 bytes)
    // ---------------------------------------------------------
    let errflg = (secondary_header_bytes[31] >> 7) as u8; // Byte 31 Bit 0
                                                          // Byte 31 Bits 1-2 are unused.
    let baqmod = (secondary_header_bytes[31] & 0x1F) as u8; // Byte 31 Bits 3-7
    let baqbl = secondary_header_bytes[32];
    // The byte at packet_data[33] is unused
    let rgdec = secondary_header_bytes[34];
    let rxg = secondary_header_bytes[35];
    let txprr = u16::from_be_bytes([secondary_header_bytes[36], secondary_header_bytes[37]]);
    let txpsf = u16::from_be_bytes([secondary_header_bytes[38], secondary_header_bytes[39]]);
    let txpl = u32::from_be_bytes([
        0,
        secondary_header_bytes[40],
        secondary_header_bytes[41],
        secondary_header_bytes[42],
    ]);
    // Byte 43 bits 0-2 are unused
    let rank = (secondary_header_bytes[43] & 0x1F) as u8; // Byte 43 bits 3-7
    let pri = u32::from_be_bytes([
        0,
        secondary_header_bytes[44],
        secondary_header_bytes[45],
        secondary_header_bytes[46],
    ]);
    let swst = u32::from_be_bytes([
        0,
        secondary_header_bytes[47],
        secondary_header_bytes[48],
        secondary_header_bytes[49],
    ]);
    let swl = u32::from_be_bytes([
        0,
        secondary_header_bytes[50],
        secondary_header_bytes[51],
        secondary_header_bytes[52],
    ]);

    // The SAS SSB message contents are dependent on the value of ssbflag
    // However, the flag itself, the polarisation, and the temperature compensation
    // fields are shared between both message types.
    let ssbflag = (secondary_header_bytes[53] >> 7) as u8; // Byte 53 Bit 0
    let pol = ((secondary_header_bytes[53] >> 4) & 0x07) as u8; // Byte 53 Bits 1-3
    let tcmp = ((secondary_header_bytes[53] >> 2) & 0x03) as u8; // Byte 53 Bits 4-5

    let ebadr: Option<u8>;
    let abadr: Option<u16>;
    let sastm: Option<u8>;
    let caltyp: Option<u8>;
    let cbadr: Option<u16>;
    if ssbflag == 0 {
        // Imaging or noise operation
        let tmp16 = u16::from_be_bytes([secondary_header_bytes[54], secondary_header_bytes[55]]);
        ebadr = Some((tmp16 >> 12) as u8); // Byte 54 Bits 0-3
                                           // Byte 54 Bits 4-5 are unused
        abadr = Some((tmp16 & 0x03FF) as u16); // Byte 54 bits 6-7 and all of byte 55
        sastm = None;
        caltyp = None;
        cbadr = None;
    } else if ssbflag == 1 {
        // Calibration operation
        let tmp16 = u16::from_be_bytes([secondary_header_bytes[54], secondary_header_bytes[55]]);
        ebadr = None;
        abadr = None;
        sastm = Some((tmp16 >> 15) as u8); // Byte 54 bit 0
        caltyp = Some(((tmp16 >> 12) & 0x07) as u8); // Byte 54 bits 1-3
        cbadr = Some((tmp16 & 0x03FF) as u16); // Byte 54 bits 6-7 and all of byte 55
    } else {
        // This should never happen as we only extract one bit for the flag
        panic!("Invalid SAS SSB flag. Received {}", ssbflag);
    }

    let calmod = (secondary_header_bytes[56] >> 6) as u8; // Byte 56 Bits 0-1
                                                          // Byte 56 Bit 2 is unused
    let txpno = (secondary_header_bytes[56] & 0x1F) as u8; // Byte 56 Bits 3-7
    let sigtyp = (secondary_header_bytes[57] >> 4) as u8; // Byte 57 Bits 0-3
                                                          // Byte 57 Bits 4-6 are unused
    let swap = (secondary_header_bytes[57] & 0x01) as u8; // Byte 57 Bit 7
    let swath = secondary_header_bytes[58];

    output_columns.errflg.push(Some(errflg));
    output_columns.baqmod.push(Some(baqmod));
    output_columns.baqbl.push(Some(baqbl));
    output_columns.rgdec.push(Some(rgdec));
    output_columns.rxg.push(Some(rxg));
    output_columns.txprr.push(Some(txprr));
    output_columns.txpsf.push(Some(txpsf));
    output_columns.txpl.push(Some(txpl));
    output_columns.rank.push(Some(rank));
    output_columns.pri.push(Some(pri));
    output_columns.swst.push(Some(swst));
    output_columns.swl.push(Some(swl));
    output_columns.ssbflag.push(Some(ssbflag));
    output_columns.pol.push(Some(pol));
    output_columns.tcmp.push(Some(tcmp));

    // These fields are already Option as they are set in the if/else blocks above
    output_columns.ebadr.push(ebadr);
    output_columns.abadr.push(abadr);
    output_columns.sastm.push(sastm);
    output_columns.caltyp.push(caltyp);
    output_columns.cbadr.push(cbadr);

    output_columns.calmod.push(Some(calmod));
    output_columns.txpno.push(Some(txpno));
    output_columns.sigtyp.push(Some(sigtyp));
    output_columns.swap.push(Some(swap));
    output_columns.swath.push(Some(swath));

    // ---------------------------------------------------------
    // Radar sample count service (3 bytes)
    // ---------------------------------------------------------
    let nq = u16::from_be_bytes([secondary_header_bytes[59], secondary_header_bytes[60]]);
    // The byte at packet_data[61] is unused
    output_columns.nq.push(Some(nq));
}

/// Decode all packet headers from file bytes.
///
/// Iterates through `file_bytes`, reading primary (6 bytes) and secondary (62 bytes, if present)
/// headers for each packet, then advancing past the packet data field (secondary + user data)
/// using `packet_data_length` from the primary header.
///
/// Returns a tuple of (output_columns, user_data_bounds).
/// `output_columns` is a `PacketHeaderColumns` struct with one row for each packet.
/// `user_data_bounds` is a vector of tuples, containing the start and length of the user data for each packet.
pub fn decode_packet_headers_inner(
    file_bytes: &[u8],
) -> (PacketHeaderColumns, Vec<(usize, usize)>) {
    let mut output_columns: PacketHeaderColumns = PacketHeaderColumns::default();
    let mut pos: usize = 0;
    let mut user_data_bounds: Vec<(usize, usize)> = Vec::new();

    while pos + PRIMARY_HEADER_LEN <= file_bytes.len() {
        // Primary header: exactly 6 bytes
        let primary_header_bytes: [u8; PRIMARY_HEADER_LEN] = file_bytes
            [pos..pos + PRIMARY_HEADER_LEN]
            .try_into()
            .expect("Primary header length");
        pos += PRIMARY_HEADER_LEN;

        // Decode primary header into columns (append one row)
        let (secondary_header_flag, packet_data_len) =
            decode_primary_header(&primary_header_bytes, &mut output_columns);

        // Packet data field (between 62 and 65534 bytes)
        // The secondary header (if present) is the first 62 bytes of the packet data field.
        // It is present if the secondary header flag is 1.
        //
        // Decode secondary header if present and append one row to the output columns.
        // Also append the user data bounds to the output.
        if secondary_header_flag != 0 {
            let secondary_header_bytes: [u8; SECONDARY_HEADER_LEN] = file_bytes
                .get(pos..pos + SECONDARY_HEADER_LEN)
                .expect("File unexpectedly ended before claimed length of secondary header")
                .try_into()
                .expect("Secondary header length");
            decode_secondary_header(&secondary_header_bytes, &mut output_columns);
            user_data_bounds.push((
                pos + SECONDARY_HEADER_LEN,
                packet_data_len as usize - SECONDARY_HEADER_LEN,
            ));
        } else {
            append_secondary_row_all_none(&mut output_columns);
            user_data_bounds.push((pos, packet_data_len as usize));
        }

        pos += packet_data_len as usize;
    }

    (output_columns, user_data_bounds)
}

/// Append a row of all None values to the secondary header columns.
///
/// This is used when the secondary header flag is 0.
/// The secondary header is not present in this case.
fn append_secondary_row_all_none(dest: &mut PacketHeaderColumns) {
    dest.tcoar.push(None);
    dest.tfine.push(None);
    dest.sync.push(None);
    dest.dtid.push(None);
    dest.ecc.push(None);
    dest.tstmod.push(None);
    dest.rxchid.push(None);
    dest.icid.push(None);
    dest.adwidx.push(None);
    dest.adw.push(None);
    dest.spct.push(None);
    dest.prict.push(None);
    dest.errflg.push(None);
    dest.baqmod.push(None);
    dest.baqbl.push(None);
    dest.rgdec.push(None);
    dest.rxg.push(None);
    dest.txprr.push(None);
    dest.txpsf.push(None);
    dest.txpl.push(None);
    dest.rank.push(None);
    dest.pri.push(None);
    dest.swst.push(None);
    dest.swl.push(None);
    dest.ssbflag.push(None);
    dest.pol.push(None);
    dest.tcmp.push(None);
    dest.ebadr.push(None);
    dest.abadr.push(None);
    dest.sastm.push(None);
    dest.caltyp.push(None);
    dest.cbadr.push(None);
    dest.calmod.push(None);
    dest.txpno.push(None);
    dest.sigtyp.push(None);
    dest.swap.push(None);
    dest.swath.push(None);
    dest.nq.push(None);
}
