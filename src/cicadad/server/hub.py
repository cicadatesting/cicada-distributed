from typing import Iterable

from cicadad.core.scenario import Scenario, filter_scenarios_by_tag, test_runner
from cicadad.services.eventing import KafkaProducer, KafkaConsumer
from cicadad.protos import hub_pb2, hub_pb2_grpc


class HubServer(hub_pb2_grpc.HubServicer):
    def __init__(
        self,
        scenarios: Iterable[Scenario],
        image: str,
        network: str,
        test_id: str,
        event_producer: KafkaProducer,
        result_consumer: KafkaConsumer,
        event_broker_address: str,
    ) -> None:
        self.scenarios = scenarios
        self.image = image
        self.network = network
        self.test_id = test_id
        self.event_producer = event_producer
        self.result_consumer = result_consumer
        self.event_broker_address = event_broker_address

    def Run(self, request, context):
        valid_scenarios = filter_scenarios_by_tag(self.scenarios, request.tags)

        yield hub_pb2.TestStatus(
            type="TEST_STARTED",
            message=f"Collected {len(valid_scenarios)} Scenario(s)",
        )

        for status in test_runner(
            valid_scenarios,
            self.image,
            self.network,
            self.test_id,
            self.event_producer,
            self.result_consumer,
            self.event_broker_address,
        ):
            yield hub_pb2.TestStatus(
                type=status.type,
                scenario=status.scenario,
                message=status.message,
                context=status.context,
            )

    def Healthcheck(self, request, context):
        return hub_pb2.HealthcheckReply(ready=True)


# FEATURE: run individual scenario
