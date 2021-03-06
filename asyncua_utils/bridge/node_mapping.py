import logging

from asyncua_utils.node_utils import strip_namespace

_logger = logging.getLogger('opcua_bridge')


class DownstreamBridgeNodeMapping:
    def __init__(self, initial_nodes: list):
        self._downstream_bridge_mapping = {}
        self.setup_types(initial_nodes)

    def setup_types(self, initial_nodes: list):
        """
        function to add all of the object types into the node mapping. This means in practice that the bridged items will
        use types defined in the bridge instead of requiring their type directories also mirrored.
        """
        # object_ids = asyncua.ua.object_ids.ObjectIds.__dict__
        [self.add_connection(node_id, node_id) for node_id in initial_nodes]
        logging.warning('type cloning done')

    def add_connection(self, downstream_node_id, bridge_node_id):
        downstream_node_id = strip_namespace(downstream_node_id)
        if downstream_node_id in self._downstream_bridge_mapping.keys():
            _logger.warning(f"node {downstream_node_id} being assigned multiple times.")
        self._downstream_bridge_mapping[downstream_node_id] = bridge_node_id

    def get_downstream_id(self, bridge_node_id):
        keys = [key for key, value in self._downstream_bridge_mapping.items() if value == bridge_node_id]
        if len(keys) != 1:
            _logger.warning(keys)
            _logger.warning(bridge_node_id)
            raise KeyError
        return keys[0]

    def get_bridge_id(self, downstream_node_id):

        downstream_node_id = strip_namespace(downstream_node_id)
        return self._downstream_bridge_mapping.get(downstream_node_id)