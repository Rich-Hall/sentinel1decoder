from termcolor import colored
from .l0file import Level0File
from . import _field_names
from .enums import SignalType
import logging
logger = logging.getLogger(__name__)



def extract_IW_chunk_info(inputfile, visualize=True):

    l0file = Level0File(inputfile)
    packet_metadata = l0file.packet_metadata
    chunk_ids = sorted(packet_metadata.index.get_level_values(_field_names.ACQUISITION_CHUNK_NUM_DECODED).unique())
    
    result = {
        'IW1': [], 'IW2': [], 'IW3': [],
        'noise': [], 'rx_cal_chunks': [], 'tx_cal_chunks': [],
        'ta_or_txiso_cal_chunks': [], 'tx_cal_iso_chunks': [],
        'epdn_cal_chunks': [], 'apdn_cal_chunks': [],
        'skipped_chunks': []
    }
    
    count = 0
    swath_IW1  = 10
    swath_IW2  = 11
    swath_IW3  = 12
    count_valid = 0
    
    for chunk in chunk_ids:
        count += 1
        selection_chunk = l0file.get_acquisition_chunk_metadata(chunk)
        signal_type = selection_chunk['Signal Type'].unique()
        
        if signal_type[0] == SignalType.NOISE:
            result['noise'].append(chunk)
            continue
        if len(selection_chunk) == 8:
            result['skipped_chunks'].append(chunk)
            continue
            
        swath_num = selection_chunk['Swath Number'].iloc[0]
        if signal_type[0] == SignalType.RX_CAL:
            result['rx_cal_chunks'].append(chunk)
        elif signal_type[0] == SignalType.TX_CAL:
            result['tx_cal_chunks'].append(chunk)
        elif signal_type[0] == SignalType.EPDN_CAL:
            result['epdn_cal_chunks'].append(chunk) 
        elif signal_type[0] == SignalType.APDN_CAL_S1AB_ONLY:
            result['apdn_cal_chunks'].append(chunk)
        elif signal_type[0] == SignalType.TA_CAL_OR_TX_CAL_ISO:
            result['ta_or_txiso_cal_chunks'].append(chunk)
        elif signal_type[0] == SignalType.TXH_CAL_ISO_S1AB_ONLY:
            result['tx_cal_iso_chunks'].append(chunk)
        elif swath_num in (swath_IW1, swath_IW2, swath_IW3):
        
            count_valid += 1
        
            if swath_num == swath_IW1:
                result['IW1'].append(chunk)
            elif swath_num == swath_IW2:
                result['IW2'].append(chunk)
            elif swath_num == swath_IW3:
                result['IW3'].append(chunk)



    if visualize:
        logger.info("noise chunks:", result['noise'])
        logger.info("skipped_chunks:", result['skipped_chunks'])
        logger.info("rx_cal_chunks:", result['rx_cal_chunks'])
        logger.info("tx_cal_chunks:", result['tx_cal_chunks'])
        logger.info("epdn_cal_chunks:", result['epdn_cal_chunks'])
        logger.info("apdn_cal_chunks:", result['apdn_cal_chunks'])
        logger.info("ta_or_txiso_cal_chunks:", result['ta_or_txiso_cal_chunks'])
        logger.info("tx_cal_iso_chunks:", result['tx_cal_iso_chunks'])
        logger.info(f"This product has {count} chunks, {count_valid} of which are valid image chunks")
        logger.info(f"{colored('IW1 chunks', 'blue')}:", result['IW1'])
        logger.info(f"{colored('IW2 chunks', 'blue')}:", result['IW2'])
        logger.info(f"{colored('IW3 chunks', 'blue')}:", result['IW3'])
    
    return l0file, result

