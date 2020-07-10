from asyncua import Client
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua_utils.nodes import browse_nodes
import asyncio
import oyaml as yaml
import itertools
from pprint import pprint as pp


async def create_nested_node_dict(server_url, client_certificate=None, client_private_key=None):
    client = Client(url=server_url)
    if client_certificate and client_private_key:
        await client.set_security(SecurityPolicyBasic256Sha256,
                            certificate_path=client_certificate,
                            private_key_path=client_private_key)
    async with client:
        out = await browse_nodes(client.nodes.objects, to_export=True)
    return out


async def make_variable_dict(server_url, client_certificate=None, client_private_key=None):
    sock = 'opc.tcp://'
    if not server_url.startswith(sock):
        server_url = sock + server_url
    nested_dict = await create_nested_node_dict(server_url, client_certificate, client_private_key)
    output_variables = []
    get_variables(nested_dict, output_variables=output_variables)
    with open('debug.yaml', 'w') as f:
        f.write(yaml.dump(output_variables))


def get_variables(nested_dict, path='', output_variables=None):
    if output_variables is None:
        output_variables = []
    new_path = f"{path}/{nested_dict['name']}"
    if nested_dict['cls'] == 'Variable':
        variable_entry = {
            'path': new_path,
            'type': nested_dict['type'],
            'id': nested_dict['id'],
            'current_value': nested_dict['current_value']
        }
        output_variables.append(variable_entry)
    elif nested_dict.get('children') and len(nested_dict['children']) > 0:
        [get_variables(child_dict, path=new_path, output_variables=output_variables) for child_dict in nested_dict['children']]
    else:
        return None


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        process = make_variable_dict(sys.argv[1])
    else:
        process = make_variable_dict(sys.argv[1], sys.argv[2], sys.argv[3])
    asyncio.run(process)
