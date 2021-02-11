from asyncua import Client, Server, ua
from asyncua.ua import Variant, VariantType, uaerrors
from asyncua_utils.bridge.node_mapping import DownstreamBridgeNodeMapping
from asyncua.common.events import Event
from asyncua_utils.node_utils import extract_node_id
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

    async def event_notification(self, event: Event):
        alarm_gen = await self._server.get_event_generator(self._server.get_node(event.EventType),
                                                           emitting_node=ua.ObjectIds.Server,
                                                           notifier_path=[ua.ObjectIds.Server])
        alarm_gen.event = event
        # alarm_gen = self.safe_event_clone(event, alarm_gen)
        await alarm_gen.trigger()

    @staticmethod
    def safe_event_clone(event, alarm_gen):
        for key, value in event.get_event_props_as_fields_dict().items():
            if key in alarm_gen.event.__dict__.keys():
                setattr(alarm_gen.event, key, value)
        return alarm_gen

    async def get_existing_alarms(self, subscription_id):
        refresh_node = self._client.get_node('i=3875')
        condition_node = self._client.get_node('i=2782')

        try:
            await condition_node.call_method(refresh_node, Variant(int(subscription_id),
                                                                                varianttype=VariantType.UInt32))
        except uaerrors.BadNothingToDo:
            logging.warning('refresh failed')
