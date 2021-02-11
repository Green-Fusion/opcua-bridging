import logging
import re

_logger = logging.getLogger('opcua_bridging')


def strip_namespace(node_id_str: str):
    potential_strs = node_id_str.split(';')
    potential_strs = [sub_str for sub_str in potential_strs if not sub_str.startswith('ns=')]
    if len(potential_strs) == 1:
        return potential_strs[0]
    else:
        _logger.warning(f"node_id:{node_id_str} ill-served by strip_namespace")
        raise NotImplementedError


def extract_node_id(node_id_str):
    if node_id_str is None:
        return None
    int_regex_string = "i=(\d*)"
    int_matches = re.findall(int_regex_string, node_id_str)
    str_regex_string = 'g=(\d*)'
    if len(int_matches) == 1:
        return int(int_matches[0])
    elif len(int_matches) == 0:
        str_matches = re.findall(str_regex_string, node_id_str)
        if len(str_matches) == 1:
            return str_matches

    logging.warning(f"extract_node_id failed with node_id_str={node_id_str}")
    raise NotImplementedError