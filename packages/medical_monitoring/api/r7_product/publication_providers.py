"""Provider-neutral publication invocation adapters for the R7 API."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Mapping, Optional, Sequence

from .contracts import ProductPublicationError


def _r5_publication_types() -> tuple[Any, Any, Any, Any, Any]:
    """Load R5 publication types lazily at the synthetic integration seam."""

    try:
        from packages.medical_monitoring.projections.publication.r5_publication_authority import (
            R5AuthorityPacket,
            R5PublicationAuthorityBridge,
            R5PublicationAuthorityError,
            R5PublicationAuthorityInput,
            R5PublicationRunIdentity,
        )
    except Exception as exc:
        raise ProductPublicationError(
            "authority_provider_unavailable", recoverable=True
        ) from exc
    return (
        R5AuthorityPacket,
        R5PublicationAuthorityBridge,
        R5PublicationAuthorityError,
        R5PublicationAuthorityInput,
        R5PublicationRunIdentity,
    )


def _call_publication_method(
    method: Callable[..., Any],
    identity: Any,
    context: Mapping[str, Any],
    *,
    packet_argument: Any = None,
) -> Any:
    """Call an injected read-only provider without guessing medical facts."""

    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        if packet_argument is not None:
            return method(packet_argument)
        return method(identity)

    parameters = tuple(signature.parameters.values())
    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )
    named = {
        name: value
        for name, value in context.items()
        if name in signature.parameters
    }
    if accepts_kwargs:
        named = dict(context)

    if packet_argument is not None:
        if "packet" in signature.parameters:
            named["packet"] = packet_argument
            return method(**named)
        positional = [
            parameter
            for parameter in parameters
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        if positional:
            return method(packet_argument, **named)
        return method(**named)

    identity_names = {
        "identity",
        "run_identity",
        "publication_identity",
        "authority_identity",
    }
    if any(name in signature.parameters for name in identity_names):
        name = next(
            name for name in identity_names if name in signature.parameters
        )
        named[name] = identity
        return method(**named)
    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    if positional:
        if positional[0].name in named:
            return method(**named)
        return method(identity, **named)
    return method(**named)


def _publication_provider_value(
    provider: Any,
    identity: Any,
    *,
    attempts: Sequence[Mapping[str, Any]],
) -> Any:
    if provider is None:
        raise ProductPublicationError("authority_provider_invalid")
    _, _, _, input_type, packet_identity_type = _r5_publication_types()
    if isinstance(provider, (input_type, packet_identity_type)):
        return provider
    context = {
        "run_identity": identity,
        "identity": identity,
        "project_ref": identity.project_ref,
        "run_ref": identity.run_ref,
        "public_run_token": identity.public_run_token,
        "snapshot_ref": identity.snapshot_ref,
        "snapshot_token": identity.snapshot_token,
        "cutoff_ref": identity.cutoff_ref,
        "site_refs": identity.site_refs,
        "attempts": tuple(attempts),
        "receipts": tuple(attempts),
        "raw_receipts": tuple(attempts),
        "r6_receipts": tuple(attempts),
        "receipt_attempts": tuple(attempts),
    }
    method_names = (
        "get_publication_input",
        "get_authority",
        "get_publication_authority",
        "get_publication_authority_input",
        "get_authority_input",
        "build_publication_authority_input",
        "build_authority_input",
        "assemble_publication_input",
        "assemble_authority_input",
        "assemble",
        "get_publication_authority_packet",
        "get_authority_packet",
        "build_publication_authority_packet",
        "get_publication_packet",
        "build_publication_packet",
        "get_packet",
    )
    for name in method_names:
        method = getattr(provider, name, None)
        if callable(method):
            try:
                return _call_publication_method(method, identity, context)
            except ProductPublicationError:
                raise
            except Exception as exc:
                raise ProductPublicationError(
                    "authority_provider_unavailable", recoverable=True
                ) from exc
    for name in ("authority_input", "publication_input", "publication_packet"):
        value = getattr(provider, name, None)
        if isinstance(value, (input_type, packet_identity_type)):
            return value
    if callable(provider):
        try:
            return _call_publication_method(provider, identity, context)
        except ProductPublicationError:
            raise
        except Exception as exc:
            raise ProductPublicationError(
                "authority_provider_unavailable", recoverable=True
            ) from exc
    raise ProductPublicationError("authority_provider_invalid")


def _publication_product_factory(
    provider: Any,
) -> Optional[Callable[[Any], Any]]:
    for name in ("product_packet_factory", "build_product_packet"):
        method = getattr(provider, name, None)
        if callable(method):
            return lambda packet, method=method: _call_publication_method(
                method,
                packet,
                {"packet": packet},
                packet_argument=packet,
            )
    return None

def _r6_publication_types() -> tuple[Any, Any]:
    """Load R6 publication types lazily at the synthetic integration seam."""
    try:
        from packages.medical_monitoring.reports import mode_output as mo
        from packages.medical_monitoring.runtime import continuity_bridge as cb
    except Exception as exc:
        raise ProductPublicationError(
            "receipt_gate_blocked", recoverable=False
        ) from exc
    return mo, cb


def _call_r6_provider_method(
    method: Callable[..., Any],
    run_binding: Mapping[str, Any],
    context: Mapping[str, Any],
) -> Any:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return method(run_binding)

    parameters = tuple(signature.parameters.values())
    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )
    named = {
        name: value
        for name, value in context.items()
        if name in signature.parameters
    }
    if accepts_kwargs:
        named = dict(context)

    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    if positional:
        first_name = positional[0].name
        if first_name not in named:
            return method(run_binding, **named)
    return method(**named)


def _obtain_r6_mode_outputs(
    provider: Any,
    run_binding: Mapping[str, Any],
    *,
    r5_packet: Optional[Any] = None,
    attempts: Sequence[Mapping[str, Any]] = (),
) -> Optional[Sequence[Mapping[str, Any]]]:
    if provider is None:
        return None
    if isinstance(provider, (tuple, list)):
        return tuple(provider)
    mo, _ = _r6_publication_types()
    binding = dict(run_binding)
    binding.setdefault("carry_forward_run_ids", [])
    binding.setdefault("mode_transition", "explicit_new_run")
    binding.setdefault("actor", "system_synthetic")
    if not binding.get("created_at"):
        binding["created_at"] = "2026-08-28T00:00:00Z"
    if not binding.get("knowledge_pack_version"):
        binding["knowledge_pack_version"] = "kp-08b-v1"
    if not binding.get("rule_activation_version"):
        binding["rule_activation_version"] = "rav-08b-v1"
    if not binding.get("mapping_version"):
        binding["mapping_version"] = "map-08b-v1"
    if not binding.get("identity_algorithm_version"):
        binding["identity_algorithm_version"] = "ia-08b-v1"
    if not binding.get("identity_algorithm_digest"):
        binding["identity_algorithm_digest"] = "ia-digest-08b-v1"
    mode = str(binding.get("mode", ""))
    if mode == "post_lock_pre_cfdi":
        binding.setdefault("fixed_total", True)
        if not binding.get("locked_snapshot_hash"):
            binding["locked_snapshot_hash"] = "snap-hash-fixed-001"
        if not binding.get("output_cutoff_ref"):
            binding["output_cutoff_ref"] = binding.get("data_cutoff")
        if not binding.get("output_revision_ref"):
            binding["output_revision_ref"] = binding.get("source_revision_id")
        if not binding.get("local_os_user"):
            binding["local_os_user"] = "local-user-synthetic"
        if not binding.get("acceptance_evidence_hash"):
            binding["acceptance_evidence_hash"] = "accept-hash-fixed-001"
    mode_contract = mo.build_mode_contract(mode) if mode in mo.MODES else None
    context = {
        "run_binding": binding,
        "binding": binding,
        "mode": mode,
        "mode_contract": mode_contract,
        "contract": mode_contract,
        "project_id": binding.get("project_id"),
        "run_id": binding.get("run_id"),
        "r5_packet": r5_packet,
        "packet": r5_packet,
        "attempts": tuple(attempts),
        "receipts": tuple(attempts),
    }
    run_binding = binding
    method_names = (
        "get_mode_outputs",
        "build_mode_outputs",
        "get_outputs",
        "build_outputs",
        "get_r6_outputs",
        "build_r6_outputs",
        "get_publication_outputs",
        "build_publication_outputs",
    )
    for name in method_names:
        method = getattr(provider, name, None)
        if callable(method):
            try:
                result = _call_r6_provider_method(method, run_binding, context)
                if isinstance(result, (tuple, list)):
                    return tuple(result)
            except Exception as exc:
                raise ProductPublicationError(
                    "receipt_gate_blocked", recoverable=False
                ) from exc
    if callable(provider):
        try:
            result = _call_r6_provider_method(provider, run_binding, context)
            if isinstance(result, (tuple, list)):
                return tuple(result)
        except Exception as exc:
            raise ProductPublicationError(
                "receipt_gate_blocked", recoverable=False
            ) from exc
    raise ProductPublicationError("receipt_gate_blocked", recoverable=False)


def _validate_r5_publication_packet(
    packet: Any,
    identity: Any,
    *,
    packet_type: Any,
) -> Any:
    if type(packet) is not packet_type:
        raise ProductPublicationError("authority_provider_invalid")
    if (
        packet.project_ref != identity.project_ref
        or packet.run_ref != identity.run_ref
        or packet.public_run_token != identity.public_run_token
        or packet.snapshot_ref != identity.snapshot_ref
        or packet.cutoff_ref != identity.cutoff_ref
        or tuple(sorted(packet.site_refs)) != tuple(identity.site_refs)
    ):
        raise ProductPublicationError("authority_identity_mismatch")
    if (
        not isinstance(packet.packet_identity, str)
        or not isinstance(packet.packet_digest, str)
        or packet.packet_identity != "r5-publication-authority:" + packet.packet_digest
        or packet.authority_hash != packet.packet_digest
        or (
            not packet.s4_packets
            and not (
                getattr(packet.product_packet, "synthetic", False) is True
                and identity.project_ref.startswith("s7-synthetic-")
            )
        )
    ):
        raise ProductPublicationError("authority_provider_invalid")
    coverage = set(identity.site_refs)
    sites = {getattr(value, "site_ref", None) for value in packet.sites}
    if sites != coverage:
        raise ProductPublicationError("authority_identity_mismatch")
    subjects = {
        getattr(value, "subject_ref", None) for value in packet.subjects
    }
    subject_sites = {
        getattr(value, "site_ref", None) for value in packet.subjects
    }
    if not subjects or not subject_sites.issubset(coverage):
        raise ProductPublicationError("authority_identity_mismatch")
    risks = {
        getattr(value, "risk_ref", None) for value in packet.risks
    }
    events = {
        getattr(value, "event_ref", None) for value in packet.events
    }
    visits = {
        getattr(value, "visit_ref", None) for value in packet.visits
    }
    sources = {
        getattr(value, "locator_ref", None) for value in packet.sources
    }
    source_pairs = {
        (
            getattr(value, "source_revision_ref", None),
            getattr(value, "source_revision_content_hash", None),
        )
        for value in packet.sources
    }
    if any(
        getattr(value, "snapshot_ref", None) != identity.snapshot_ref
        for value in packet.sources
    ):
        raise ProductPublicationError("authority_identity_mismatch")
    for category in ("risks", "events", "visits"):
        for value in getattr(packet, category):
            if (
                getattr(value, "site_ref", None) not in coverage
                or getattr(value, "subject_ref", None) not in subjects
            ):
                raise ProductPublicationError("authority_identity_mismatch")
    for s4_packet in packet.s4_packets:
        risk = getattr(s4_packet, "risk_identity", None)
        journey = getattr(s4_packet, "journey_link", None)
        if (
            risk is None
            or risk.project_ref != identity.project_ref
            or risk.run_ref != identity.run_ref
            or risk.snapshot_ref != identity.snapshot_ref
            or risk.cutoff_ref != identity.cutoff_ref
            or risk.site_ref not in coverage
            or risk.subject_ref not in subjects
            or risk.risk_ref not in risks
            or journey is None
        ):
            raise ProductPublicationError("authority_identity_mismatch")
        if (
            getattr(journey, "deep_link_event_ref", None) is not None
            and journey.deep_link_event_ref not in events
        ) or (
            getattr(journey, "deep_link_visit_ref", None) is not None
            and journey.deep_link_visit_ref not in visits
        ) or (
            getattr(journey, "deep_link_source_locator_ref", None) is not None
            and journey.deep_link_source_locator_ref not in sources
        ):
            raise ProductPublicationError("authority_identity_mismatch")
        receipt = getattr(s4_packet, "authority_receipt", None)
        if receipt is None:
            raise ProductPublicationError("authority_identity_mismatch")
        for pair in getattr(receipt, "source_revision_content_pairs", ()):
            if (
                getattr(pair, "revision_id", None),
                getattr(pair, "content_hash", None),
            ) not in source_pairs:
                raise ProductPublicationError("authority_identity_mismatch")
    return packet

__all__ = [
    "_r5_publication_types",
    "_call_publication_method",
    "_publication_provider_value",
    "_publication_product_factory",
    "_r6_publication_types",
    "_call_r6_provider_method",
    "_obtain_r6_mode_outputs",
    "_validate_r5_publication_packet",
]
