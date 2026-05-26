from termcolor import colored
from .l0file import Level0File
from . import _field_names
from .enums import SignalType
import logging

logger = logging.getLogger(__name__)


def _get_chunk_ids(l0file: "Level0File") -> list:
    packet_metadata = l0file.packet_metadata
    return sorted(
        packet_metadata.index.get_level_values(_field_names.ACQUISITION_CHUNK_NUM_DECODED).unique()
    )


def _append_chunk(result: dict[str, list], key: str, chunk: int) -> None:
    result[key].append(chunk)


def _route_by_signal_type(
        result: dict[str, list],
        signal_type: SignalType,
        chunk: int,
        signal_map: dict[SignalType, str]
    ) -> bool:
    key = signal_map.get(signal_type)
    if key is None:
        return False
    _append_chunk(result, key, chunk)
    return True


def extract_SM_chunk_info(
        inputfile: str,
        visualize: bool = True
    ) -> tuple["Level0File", dict[str, list]]:
    """
    Extract the data block information of the Sentinel-1 SM mode
    Important Note:
    When visualize=True, the function will output logs using logger.info.
    Please configure logging before calling the function
    """
    l0file = Level0File(inputfile)
    chunk_ids = _get_chunk_ids(l0file)

    result = {
        'SM': [],
        'noise': [], 'rx_cal_chunks': [], 'tx_cal_chunks': [],
        'ta_or_txiso_cal_chunks': [], 'tx_cal_iso_chunks': [],
        'epdn_cal_chunks': [], 'apdn_cal_chunks': []
    }

    count = 0
    count_valid = 0
    signal_map = {
        SignalType.NOISE: 'noise',
        SignalType.RX_CAL: 'rx_cal_chunks',
        SignalType.TX_CAL: 'tx_cal_chunks',
        SignalType.EPDN_CAL: 'epdn_cal_chunks',
        SignalType.APDN_CAL_S1AB_ONLY: 'apdn_cal_chunks',
        SignalType.TA_CAL_OR_TX_CAL_ISO: 'ta_or_txiso_cal_chunks',
        SignalType.TXH_CAL_ISO_S1AB_ONLY: 'tx_cal_iso_chunks',
    }

    for chunk in chunk_ids:
        count += 1
        selection_chunk = l0file.get_acquisition_chunk_metadata(chunk)
        signal_type = selection_chunk['Signal Type'].unique()[0]

        if signal_type == SignalType.ECHO:
            count_valid += 1
            _append_chunk(result, 'SM', chunk)
            continue

        _route_by_signal_type(result, signal_type, chunk, signal_map)

    if visualize:
        logger.info(f"noise chunks: {result['noise']}")
        logger.info(f"rx_cal_chunks: {result['rx_cal_chunks']}")
        logger.info(f"tx_cal_chunks: {result['tx_cal_chunks']}")
        logger.info(f"epdn_cal_chunks: {result['epdn_cal_chunks']}")
        logger.info(f"apdn_cal_chunks: {result['apdn_cal_chunks']}")
        logger.info(f"ta_or_txiso_cal_chunks: {result['ta_or_txiso_cal_chunks']}")
        logger.info(f"tx_cal_iso_chunks: {result['tx_cal_iso_chunks']}")
        logger.info(f"This product has {colored(count, 'green')} chunks, {colored(count_valid, 'yellow')} of which are valid image chunks")
        logger.info(f"{colored('SM chunks', 'blue')}: {result['SM']}")

    return l0file, result


def extract_IW_chunk_info(
        inputfile: str,
        visualize: bool = True
    ) -> tuple["Level0File", dict[str, list]]:
    """
    Extract the data block information of the Sentinel-1 IW mode
    Important Note:
    When visualize=True, the function will output logs using logger.info.
    Please configure logging before calling the function
    """
    l0file = Level0File(inputfile)
    chunk_ids = _get_chunk_ids(l0file)

    result = {
        'IW1': [], 'IW2': [], 'IW3': [],
        'noise_IW1': [], 'noise_IW2': [], 'noise_IW3': [],
        'rx_cal_chunks': [], 'tx_cal_chunks': [],
        'ta_or_txiso_cal_chunks': [], 'tx_cal_iso_chunks': [],
        'epdn_cal_chunks': [], 'apdn_cal_chunks': [],
        'skipped_chunks': []
    }

    count = 0
    swath_IW1 = 10
    swath_IW2 = 11
    swath_IW3 = 12
    swath_to_key = {
        swath_IW1: 'IW1',
        swath_IW2: 'IW2',
        swath_IW3: 'IW3',
    }
    count_valid = 0
    signal_map = {
        SignalType.RX_CAL: 'rx_cal_chunks',
        SignalType.TX_CAL: 'tx_cal_chunks',
        SignalType.EPDN_CAL: 'epdn_cal_chunks',
        SignalType.APDN_CAL_S1AB_ONLY: 'apdn_cal_chunks',
        SignalType.TA_CAL_OR_TX_CAL_ISO: 'ta_or_txiso_cal_chunks',
        SignalType.TXH_CAL_ISO_S1AB_ONLY: 'tx_cal_iso_chunks',
    }

    for chunk in chunk_ids:
        count += 1
        selection_chunk = l0file.get_acquisition_chunk_metadata(chunk)
        signal_type = selection_chunk['Signal Type'].unique()[0]

        swath_num = selection_chunk['Swath Number'].iloc[0]
        if signal_type == SignalType.NOISE:
            noise_key = f'noise_{swath_to_key.get(swath_num, "")}'
            _append_chunk(result, noise_key, chunk)
            continue
        if len(selection_chunk) == 8 and signal_type == SignalType.ECHO:
            _append_chunk(result, 'skipped_chunks', chunk)
            continue

        if _route_by_signal_type(result, signal_type, chunk, signal_map):
            continue

        if swath_num in swath_to_key:
            count_valid += 1
            _append_chunk(result, swath_to_key[swath_num], chunk)

    if visualize:
        logger.info(f"noise_IW1 chunks: {result['noise_IW1']}")
        logger.info(f"noise_IW2 chunks: {result['noise_IW2']}")
        logger.info(f"noise_IW3 chunks: {result['noise_IW3']}")
        logger.info(f"skipped chunks: {result['skipped_chunks']}")
        logger.info(f"rx_cal_chunks: {result['rx_cal_chunks']}")
        logger.info(f"tx_cal_chunks: {result['tx_cal_chunks']}")
        logger.info(f"epdn_cal_chunks: {result['epdn_cal_chunks']}")
        logger.info(f"apdn_cal_chunks: {result['apdn_cal_chunks']}")
        logger.info(f"ta_or_txiso_cal_chunks: {result['ta_or_txiso_cal_chunks']}")
        logger.info(f"tx_cal_iso_chunks: {result['tx_cal_iso_chunks']}")
        logger.info(f"This product has {colored(count, 'green')} chunks, {colored(count_valid, 'yellow')} of which are valid image chunks")
        logger.info(f"{colored('IW1 chunks', 'blue')}: {result['IW1']}")
        logger.info(f"{colored('IW2 chunks', 'blue')}: {result['IW2']}")
        logger.info(f"{colored('IW3 chunks', 'blue')}: {result['IW3']}")

    return l0file, result

