from asyncua import Client, Server, ua, Node
from asyncua.ua import Variant, VariantType, uaerrors
from asyncua_utils.bridge.node_mapping import DownstreamBridgeNodeMapping
from asyncua.common.events import Event
from asyncua_utils.node_utils import extract_node_id
from asyncua.common.methods import uamethod
import pprint as pp
import logging


class AlarmHandler:
    def __init__(self, downstream_client: Client, bridge_server: Server, node_mapping: DownstreamBridgeNodeMapping):
        self._client = downstream_client
        self._server = bridge_server
        self._node_mapping = node_mapping
        self.subscription_id = None

    async def start(self, subscription_id: None):
        if subscription_id is None and self.subscription_id is None:
            raise KeyError
        elif subscription_id is not None:
            self.subscription_id = subscription_id
        else:
            subscription_id = self.subscription_id
        await self.get_existing_alarms(subscription_id)

    async def _get_notifier_path(self, bridge_id: ua.NodeId):
        bridge_node = self._server.get_node(bridge_id)
        path = [self._server.nodes.server.nodeid]
        path.extend((await bridge_node.get_path())[2:])  # from 2 on because first two in path are 84, 85 which are Objects etc.
        logging.warning(path)
        return path

    async def event_notification(self, event: Event):
        alarm = self._server.get_node(ua.NodeId(10637))
        source_id_str = event.SourceNode.to_string()
        bridge_id = ua.NodeId.from_string(self._node_mapping.get_bridge_id(source_id_str))
        # bridge_id = ua.NodeId.from_string('i=2253') # TODO: we need to get this coming from the right node, i think?
        logging.warning(f'bridge_id={bridge_id.to_string()};source_id={source_id_str}')
        notifier_path = await self._get_notifier_path(bridge_id)

        alarm_gen = await self._server.get_event_generator(alarm,
                                                           emitting_node=bridge_id,
                                                           notifier_path=notifier_path)
        # event.SourceNode = self._server.nodes.server.nodeid
        event.Message = ua.LocalizedText('hello from bridge')

        alarm_gen = self._safe_event_clone(event, alarm_gen)

        logging.warning(alarm_gen.event)
        await alarm_gen.trigger()

    def _safe_event_clone(self, event, alarm_gen):
        for key, value in event.get_event_props_as_fields_dict().items():
            if key in alarm_gen.event.__dict__.keys():
                if value.VariantType == VariantType.NodeId:
                    logging.warning('happening')
                    value.type = self._node_mapping.get_bridge_id(value.type)
                setattr(alarm_gen.event, key, value)

        return alarm_gen

    async def get_existing_alarms(self, subscription_id=None):

        if subscription_id is None:
            subscription_id = self.subscription_id
        refresh_node = self._client.get_node('i=3875')
        condition_node = self._client.get_node('i=2782')

        try:
            await condition_node.call_method(refresh_node, Variant(int(subscription_id),
                                                                                varianttype=VariantType.UInt32))
        except uaerrors.BadNothingToDo:
            logging.warning('refresh failed')


async def add_refresh_method(server_object: Server, sub_list):
    await server_object.get_node('i=3875').delete()

    @uamethod
    async def full_refresh(parent, subscription_id):
        logging.warning('full_refresh happening')
        for sub in sub_list:
            await sub['sub_handler'].refresh_alarms()

    await server_object.get_node('i=2782').add_method('i=3875', ua.QualifiedName('ConditionRefresh', 2), full_refresh,
                                                 [ua.VariantType.Int64], [])
