from asyncua_utils.nodes import browse_nodes, clone_nodes
from asyncua import Client, Server, Node
from asyncua.common.subscription import Subscription
import logging
from asyncua.common.callback import CallbackType
import asyncua.ua.uaerrors

_logger = logging.getLogger('asyncua')


def subscribe_with_handler_from_list(sub_handler, mapping_list):
    for map_dict in mapping_list:
        downstream_id = map_dict['original_id']
        bridge_id = map_dict['mapped_id']
        sub_handler.add_connection(downstream_id, bridge_id)


class DownstreamBridgeNodeMapping:
    def __init__(self):
        self._downstream_bridge_mapping = {}
        self.setup_types()

    def setup_types(self):
        """
        function to add all of the object types into the node mapping. This means in practice that the bridged items will
        use types defined in the bridge instead of requiring their type directories also mirrored.
        """
        object_ids = asyncua.ua.object_ids.ObjectIds.__dict__
        [self.add_connection(f"i={node_id}", f"i={node_id}") for _, node_id in object_ids.items() if isinstance(node_id, int)]
        # logging.warning(self._downstream_bridge_mapping)
        # exit(1)

    def add_connection(self, downstream_node_id, bridge_node_id):
        downstream_node_id = strip_namespace(downstream_node_id)
        if downstream_node_id in self._downstream_bridge_mapping.keys():
            _logger.warning(f"node {downstream_node_id} being assigned multiple times.")
        self._downstream_bridge_mapping[downstream_node_id] = bridge_node_id

    def get_downstream_id(self, bridge_node_id):
        keys = [key for key, value in self._downstream_bridge_mapping.items() if value == bridge_node_id]
        if len(keys) != 1:
            raise KeyError
        return keys[0]

    def get_bridge_id(self, downstream_node_id):

        downstream_node_id = strip_namespace(downstream_node_id)
        return self._downstream_bridge_mapping.get(downstream_node_id)


class SubscriptionHandler:
    def __init__(self, client: Client, server: Server, client_server_mapping: DownstreamBridgeNodeMapping):
        """
        :param client:
        :type client: Client
        :param server:
        :type server: Server
        """
        self._client = client
        self._server = server
        self._client_server_mapping = client_server_mapping

    def add_connection(self, server_node_id, client_node_id):
        self._client_server_mapping.add_connection(server_node_id, client_node_id)

    async def datachange_notification(self, node, val, data):
        node_id = node.nodeid.to_string()
        client_id = self._client_server_mapping.get_bridge_id(node_id)
        if client_id is None:
            _logger.exception(f"mapped connection with host node {node_id} has no mapping in the subscription handler")
            return
        client_node = self._server.get_node(client_id)
        try:
            await client_node.set_value(val)
        except asyncua.ua.uaerrors.UaError:
            _logger.warning(f"client node {node_id} tried to set a bad value of {val} and instead has been nullified")
            await client_node.set_value(None)

    def server_id_from_client_id(self, client_id):
        return self._client_server_mapping.get_downstream_id(client_id)

    def client_id_from_server_id(self, server_id):
        return self._client_server_mapping.get_bridge_id(server_id)

    async def inverse_forwarding(self, event, dispatch):
        response_params = event.response_params
        request_params = event.request_params
        user = event.user
        if user.name is not None:
            _logger.warning(
                f"inverse forwarding called with response params {event.response_params} and request params {event.request_params}")
            for idx in range(len(request_params.NodesToWrite)):
                write_params = request_params.NodesToWrite[idx]
                source_node_id = write_params.NodeId.to_string()
                forward_node_id = self.server_id_from_client_id(source_node_id)
                value = write_params.Value
                val = self._client.get_node(forward_node_id)
                await val.set_value(value)
                _logger.warning(f'value set of {value}')

    def subscribe_to_writes(self):
        # need some way of awaiting this
        _logger.warning('this is happening')
        self._server.subscribe_server_callback(CallbackType.PreWrite, self.inverse_forwarding)

    @staticmethod
    async def _safe_set(node, value):
        try:
            await node.set_value(value)
        except asyncua.ua.uaerrors._base.UaError:
            _logger.warning('node failed to be set with value %s', value)


async def clone_and_subscribe(client: Client, node_dict: dict, server_node: Node, sub_handler: SubscriptionHandler,
                              subscription_obj: Subscription, server_object: Server, method_handler):
    namespace_array = await client.get_namespace_array()
    mapping_list = await clone_nodes(node_dict, server_node, namespace_array, server_object, method_handler)
    subscribe_with_handler_from_list(sub_handler, mapping_list)
    var_nodes = [client.get_node(elem['original_id']) for elem in mapping_list if elem['type'] == 'Variable']
    sub_node_lists = [var_nodes[x:x + 50] for x in range(0, len(var_nodes), 50)]
    for node_list in sub_node_lists:
        await subscription_obj.subscribe_data_change(node_list)
    return mapping_list


def strip_namespace(node_id_str: str):
    potential_strs = node_id_str.split(';')
    potential_strs = [sub_str for sub_str in potential_strs if not sub_str.startswith('ns=')]
    if len(potential_strs) == 1:
        return potential_strs[0]
    else:
        _logger.warning(f"node_id:{node_id_str} ill-served by strip_namespace")
        raise NotImplementedError