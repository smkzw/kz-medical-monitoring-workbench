"""Attach the exact job-local tool images to a monitoring raw-API call."""
from copy import deepcopy
from dataclasses import fields

from .ai_gateway import AiPromptEnvelope, OpenAICompatibleAiProvider
from .monitoring_visual_transport import (
    MonitoringVisualImage, MonitoringVisualPromptEnvelope,
    provider_from_shared_config,
)


def visual_provider(provider):
    if type(provider) is OpenAICompatibleAiProvider:
        keys = ('base_url', 'api_key', 'model_name', 'provider_name', 'timeout_seconds',
                'expected_response_model', 'max_attempts', 'default_thinking', 'default_reasoning_effort')
        return provider_from_shared_config(**{key: getattr(provider, key) for key in keys})
    # Already adapted providers and injected test providers retain identity.
    return provider


def attach_visual_inputs(envelope, extractions):
    if not extractions:
        return envelope
    images, descriptions = [], []
    for extraction in extractions.values():
        images.append(MonitoringVisualImage(
            data=extraction.image.image_bytes, media_type=extraction.image.media_type,
            sha256=extraction.image.image_sha256, locator=extraction.locator,
        ))
        descriptions.append({'image_index': len(images), 'visual_ref': extraction.extraction_sha256,
                             'source_entry_id': extraction.source_entry_id,
                             'source_content_sha256': extraction.source_content_sha256,
                             'locator': extraction.locator, 'image_sha256': extraction.image.image_sha256})
    values = {field.name: getattr(envelope, field.name) for field in fields(AiPromptEnvelope)}
    values['payload'] = deepcopy(envelope.payload)
    values['payload']['visual_image_inputs'] = descriptions
    return MonitoringVisualPromptEnvelope(**values, images=tuple(images))
