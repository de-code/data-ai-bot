import logging
from typing import Optional

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from openinference.instrumentation.smolagents import SmolagentsInstrumentor


LOGGER = logging.getLogger(__name__)


def configure_otlp(otlp_endpoint: str):
    LOGGER.info('Configuring OTLP: %r', otlp_endpoint)
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(otlp_endpoint)))
    SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)


def configure_otlp_if_enabled(otlp_endpoint: Optional[str] = None):
    if otlp_endpoint:
        configure_otlp(otlp_endpoint)
