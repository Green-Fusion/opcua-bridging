import logging

_logger = logging.getLogger('asyncua')


class SubscriptionHandler:
    def __init__(self, client, server):
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
        await client_node.set_value(val)