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
    regex_string = "i=(\d*)"
    int_matches = re.findall(regex_string, node_id_str)
    if len(int_matches) == 1:
        return int(int_matches[0])
    else:
        raise NotImplementedError