"""OpenTelemetry wiring for sending agent traces to a local Arize Phoenix.

Phoenix is expected to be running separately (e.g. `phoenix serve`). By default
it listens on http://localhost:6006 and accepts OTLP/HTTP traces at /v1/traces.
"""
import atexit
import os

from openinference.instrumentation.pydantic_ai import OpenInferenceSpanProcessor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


DEFAULT_PHOENIX_ENDPOINT = "http://localhost:6006"
DEFAULT_PROJECT_NAME = "pydanticai-deep-research"


def setup_phoenix(project_name: str = DEFAULT_PROJECT_NAME) -> None:
    """Install a global TracerProvider that ships spans to Phoenix via OTLP/HTTP.

    PydanticAI's own `instrument=True` emits OTel spans with GenAI conventions;
    `OpenInferenceSpanProcessor` rewrites them in-place with OpenInference
    attributes so Phoenix's UI can classify them as AGENT / LLM / TOOL spans
    and render inputs/outputs properly. Processors run in registration order,
    so the enhancer must come before the exporter.
    """
    if isinstance(trace.get_tracer_provider(), TracerProvider):
        return

    endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", DEFAULT_PHOENIX_ENDPOINT)
    traces_url = f"{endpoint.rstrip('/')}/v1/traces"

    resource = Resource.create({
        "service.name": project_name,
        # Phoenix groups traces by this attribute in the UI.
        "openinference.project.name": project_name,
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(OpenInferenceSpanProcessor())
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=traces_url)))
    trace.set_tracer_provider(provider)

    # Ensure buffered spans are flushed before the process exits — agent runs
    # are short and would otherwise finish before BatchSpanProcessor's timer.
    atexit.register(provider.shutdown)
