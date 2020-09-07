from asyncua_utils.nodes import browse_nodes, clone_nodes
import logging
from asyncua.common.callback import CallbackType
import asyncua.ua.uaerrors

_logger = logging.getLogger('asyncua')


def subscribe_with_handler_from_list(sub_handler, mapping_list):
    for server_id, client_id in mapping_list:
        sub_handler.add_connection(server_id, client_id)


async def create_simple_bridge(client_node, server_node, sub_handler, subscription_obj, client, node_id_prefix=''):
    node_dict = await browse_nodes(client_node)
    await clone_and_subscribe(client, node_dict, node_id_prefix, server_node, sub_handler, subscription_obj)


async def clone_and_subscribe(client, node_dict, node_id_prefix, server_node, sub_handler, subscription_obj,
                              namespace_idx):
    mapping_list = await clone_nodes(node_dict, server_node, node_id_prefix=node_id_prefix, idx=namespace_idx)
    subscribe_with_handler_from_list(sub_handler, mapping_list)
    nodes = [client.get_node(srv_node_id) for srv_node_id, _ in mapping_list]
    sub_node_lists = [nodes[x:x + 50] for x in range(0, len(nodes), 50)]
    for node_list in sub_node_lists:
        await subscription_obj.subscribe_data_change(node_list)


class SubscriptionHandler:
    def __init__(self, client, server):
        """
        :param client:
        :type client: Client
        :param server:
        :type server: Server
        """
        self._client = client
        self._server = server
        self._client_server_mapping = {}

    def add_connection(self, server_node_id, client_node_id):
        if server_node_id in self._client_server_mapping.keys():
            _logger.warning(f"node {server_node_id} being assigned multiple times.")
        self._client_server_mapping[server_node_id] = client_node_id

    async def datachange_notification(self, node, val, data):
        node_id = node.nodeid.to_string()
        client_id = self._client_server_mapping.get(node_id)
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
        keys = [key for key, value in self._client_server_mapping.items() if value == client_id]
        if len(keys) != 1:
            raise KeyError
        return keys[0]

    def client_id_from_server_id(self, server_id):
        return self._client_server_mapping[server_id]

    async def inverse_forwarding(self, event, dispatch):
        response_params = event.response_params
        request_params = event.request_params
        _logger.warning(f"inverse forwarding called with response params {event.response_params} and request params {event.request_params}")
        user = event.user
        if user.name is not None:
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