from asyncua import Client, Server, Node, ua
from asyncua_utils.bridge.subscription import DownstreamBridgeNodeMapping
from asyncua.ua.uaprotocol_hand import Argument
from asyncua.ua.uatypes import NodeId, LocalizedText
from asyncua.ua.uaerrors import UaStatusCodeError
from asyncua.ua import StatusCode
import logging
import pprint
from asyncua_utils.nodes import extract_node_id


class MethodForwardingHandler:
    def __init__(self, client: Client, server: Server, client_server_node_mapper: DownstreamBridgeNodeMapping):
        self._client = client
        self._server = server
        self._client_server_node_mapper = client_server_node_mapper
        self._function_directory = {}

    async def make_function_link(self, server_node_id: NodeId, base_node: Node, node_dict: dict):
        children = node_dict.get('children')
        func_id = node_dict['id']
        func_name = node_dict['name']
        input_args, output_args = await self.get_input_output(children)
        mirrored_func = await self.generate_downstream_function(func_id, func_name)
        method_node = await base_node.add_method(server_node_id, node_dict['name'], mirrored_func, input_args, output_args)
        return method_node.nodeid

    async def generate_downstream_function(self, func_node_id, func_name):
        func_node = self._client.get_node(func_node_id)
        parent = await func_node.get_parent()

        async def downstream_func_call(node_id, *args):
            try:
                output = await parent.call_method(func_name, *args)
            except UaStatusCodeError as e:
                status_code = e.code
                logging.warning(f"method {func_name} failed with status code {status_code}")
                return StatusCode(status_code)
            if not isinstance(output, list):
                return [ua.Variant(output)]
            else:
                return output
        return downstream_func_call

    @staticmethod
    def fake_func(*args):
        return [ua.Variant(True, ua.VariantType.Boolean)]

    async def get_input_output(self, children: list):
        if children is None:
            return None, None
        input_dicts = [child for child in children if 'Input' in child['name']]
        if len(input_dicts) > 1:
            raise KeyError
        elif len(input_dicts) == 0:
            input_args = None
        elif input_dicts[0].get('extension_object') is None:
            input_args = None
        else:
            input_args = [self.make_argument(arg_dict) for arg_dict in input_dicts[0]['extension_object']]
        output_dicts = [child for child in children if 'Output' in child['name']]
        if len(output_dicts) == 0:
            output_args = None
        elif len(output_dicts) == 1:
            output_args = [self.make_argument(arg_dict) for arg_dict in output_dicts[0]['extension_object']]
        else:
            raise KeyError

        return input_args, output_args

    @staticmethod
    def make_argument(argument_dict):
        arg = Argument()
        arg.ArrayDimensions = argument_dict['ArrayDimensions']
        data_type_node_id = extract_node_id(argument_dict['DataType'])
        arg.DataType = NodeId(data_type_node_id)
        arg.ValueRank = argument_dict['ValueRank']
        arg.Description = LocalizedText(text=argument_dict['Description'], locale='en')
        return arg
