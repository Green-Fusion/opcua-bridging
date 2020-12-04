from asyncua import Client, Server, Node
from asyncua_utils.bridge.subscription import ClientServerNodeMapping


class MethodForwardingHandler:
    def __init__(self, client: Client, server: Server, client_server_node_mapper: ClientServerNodeMapping):
        self._client = client
        self._server = server
        self._client_server_node_mapper = client_server_node_mapper
        self._function_directory = {}

    async def make_function_link(self, client_node_id: str, server_node: Node):
        # print(dir(self._client.get_node(client_node_id))
        method_node = await self._client.nodes.server.add_method()
        method_node.add_variable()

    def add_connection(self, server_node_id, client_node_id):
        self._client_server_node_mapper.add_connection(server_node_id, client_node_id)

