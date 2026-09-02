"""R5-owned authority input assembly and S4-to-product bridge.

This module is the narrow authority seam for Slice-07C-3.  Callers inject
already accepted, typed R4/R5 objects and the existing ``R5S4RuntimeInput``
objects.  The assembler performs identity/shape checks only.  The bridge then
calls the existing S4 builder and validator for each risk and performs only a
member join; it never derives a risk, severity, Query, Journey, denominator or
other medical fact from bytes, receipt markers, fixtures or model text.

The local ``R5AuthorityPacket`` is a renderer-neutral aggregate used by the
R5 POC.  A product integration may provide ``product_packet_factory`` to
materialize the existing product adapter packet from this verified aggregate.
No fixture provider is imported or selected implicitly.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import date
from hashlib import sha256
import json
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple

from . import s4_contracts as s4
from . import s4_projection
from . import s4_validator


_PACKET_ID_PREFIX = "r5-publication-authority:"
_SHA256_LENGTH = 64


class R5PublicationAuthorityError(ValueError):
    """A publication authority input or member join failed closed."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class R5PublicationRunIdentity:
    """The caller-supplied, frozen identity for one publication run.

    ``site_refs`` is the already-derived coverage set.  It is intentionally
    not inferred from any member collection in this module.
    """

    project_ref: str
    run_ref: str
    public_run_token: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_refs: Tuple[str, ...]
    snapshot_token: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "project_ref",
            "run_ref",
            "public_run_token",
            "snapshot_ref",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value.strip():
                raise R5PublicationAuthorityError(
                    "RUN_IDENTITY_INVALID", f"{name} must be a non-empty string"
                )
            object.__setattr__(self, name, value.strip())
        if self.cutoff_ref is not None:
            if type(self.cutoff_ref) is not str or not self.cutoff_ref.strip():
                raise R5PublicationAuthorityError(
                    "RUN_IDENTITY_INVALID", "cutoff_ref must be null or non-empty"
                )
            object.__setattr__(self, "cutoff_ref", self.cutoff_ref.strip())
        if self.snapshot_token is not None:
            if type(self.snapshot_token) is not str or not self.snapshot_token.strip():
                raise R5PublicationAuthorityError(
                    "RUN_IDENTITY_INVALID",
                    "snapshot_token must be null or non-empty",
                )
            object.__setattr__(self, "snapshot_token", self.snapshot_token.strip())
        sites = _strict_str_tuple(self.site_refs, "site_refs")
        if len(sites) != len(set(sites)):
            raise R5PublicationAuthorityError(
                "SITE_COVERAGE_DUPLICATE", "site_refs must be unique"
            )
        object.__setattr__(self, "site_refs", tuple(sorted(sites)))


@dataclass(frozen=True)
class R5PublicationRawBytes:
    """One explicit raw-byte input associated with an analysis attempt."""

    attempt_id: str
    raw_bytes: bytes

    def __post_init__(self) -> None:
        if type(self.attempt_id) is not str or not self.attempt_id.strip():
            raise R5PublicationAuthorityError(
                "RAW_BYTES_INVALID", "attempt_id must be a non-empty string"
            )
        object.__setattr__(self, "attempt_id", self.attempt_id.strip())
        if type(self.raw_bytes) is not bytes:
            raise R5PublicationAuthorityError(
                "RAW_BYTES_INVALID", "raw_bytes must be bytes"
            )


@dataclass(frozen=True)
class R5PublicationAuthorityInput:
    """Fully typed input assembled before any S4 packet is built."""

    run_identity: R5PublicationRunIdentity
    runtime_inputs: Tuple[s4.R5S4RuntimeInput, ...]
    risks: Tuple[Any, ...]
    subjects: Tuple[Any, ...]
    sites: Tuple[Any, ...]
    events: Tuple[Any, ...]
    visits: Tuple[Any, ...]
    sources: Tuple[Any, ...]
    raw_bytes: Tuple[R5PublicationRawBytes, ...]
    product_authority: Any = None

    def __post_init__(self) -> None:
        if type(self.run_identity) is not R5PublicationRunIdentity:
            raise R5PublicationAuthorityError(
                "RUN_IDENTITY_INVALID", "run_identity must be typed"
            )
        runtime_inputs = tuple(self.runtime_inputs)
        if not runtime_inputs or any(
            type(item) is not s4.R5S4RuntimeInput for item in runtime_inputs
        ):
            raise R5PublicationAuthorityError(
                "RUNTIME_INPUT_INVALID",
                "runtime_inputs must contain one or more R5S4RuntimeInput values",
            )
        object.__setattr__(self, "runtime_inputs", runtime_inputs)
        for name in ("risks", "subjects", "sites", "events", "visits", "sources"):
            values = _typed_authority_tuple(getattr(self, name), name)
            object.__setattr__(self, name, values)
        raw = tuple(self.raw_bytes)
        if any(type(item) is not R5PublicationRawBytes for item in raw):
            raise R5PublicationAuthorityError(
                "RAW_BYTES_INVALID", "raw_bytes must contain typed raw-byte values"
            )
        if len({item.attempt_id for item in raw}) != len(raw):
            raise R5PublicationAuthorityError(
                "RAW_BYTES_DUPLICATE", "raw_bytes attempt ids must be unique"
            )
        object.__setattr__(self, "raw_bytes", raw)
        if self.product_authority is not None:
            _require_frozen_dataclass(self.product_authority, "product_authority")

    @property
    def accepted_risk_authority(self) -> Tuple[Any, ...]:
        return self.risks

    @property
    def accepted_subject_authority(self) -> Tuple[Any, ...]:
        return self.subjects

    @property
    def accepted_site_authority(self) -> Tuple[Any, ...]:
        return self.sites

    @property
    def accepted_event_authority(self) -> Tuple[Any, ...]:
        return self.events

    @property
    def accepted_visit_authority(self) -> Tuple[Any, ...]:
        return self.visits

    @property
    def accepted_source_authority(self) -> Tuple[Any, ...]:
        return self.sources


@dataclass(frozen=True)
class R5AuthorityPacket:
    """Verified R5 aggregate with an optional product-packet handoff.

    The member tuples are accepted typed objects, not reconstructed records.
    ``s4_packets`` are the packets built and validated by the existing S4
    implementation.  Digest fields cover only this aggregate's deterministic
    identity and are not used as an authority source.
    """

    project_ref: str
    run_ref: str
    public_run_token: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    site_refs: Tuple[str, ...]
    s4_packets: Tuple[s4.R5S4AuthorityPacket, ...]
    risks: Tuple[Any, ...]
    subjects: Tuple[Any, ...]
    sites: Tuple[Any, ...]
    events: Tuple[Any, ...]
    visits: Tuple[Any, ...]
    sources: Tuple[Any, ...]
    packet_identity: str
    packet_digest: str
    authority_hash: str
    product_packet: Any = None

    def __post_init__(self) -> None:
        for name in (
            "project_ref",
            "run_ref",
            "public_run_token",
            "snapshot_ref",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value.strip():
                raise R5PublicationAuthorityError(
                    "PACKET_IDENTITY_INVALID", f"{name} must be non-empty"
                )
            object.__setattr__(self, name, value.strip())
        if self.cutoff_ref is not None and (
            type(self.cutoff_ref) is not str or not self.cutoff_ref.strip()
        ):
            raise R5PublicationAuthorityError(
                "PACKET_IDENTITY_INVALID", "cutoff_ref must be null or non-empty"
            )
        site_refs = _strict_str_tuple(self.site_refs, "site_refs")
        if len(site_refs) != len(set(site_refs)):
            raise R5PublicationAuthorityError(
                "SITE_COVERAGE_DUPLICATE", "packet site_refs must be unique"
            )
        object.__setattr__(self, "site_refs", tuple(sorted(site_refs)))
        packets = tuple(self.s4_packets)
        synthetic_product = (
            self.product_packet is not None
            and getattr(self.product_packet, "synthetic", False) is True
            and self.project_ref.startswith("s7-synthetic-")
        )
        if (
            (not packets and not synthetic_product)
            or any(type(item) is not s4.R5S4AuthorityPacket for item in packets)
        ):
            raise R5PublicationAuthorityError(
                "S4_PACKET_INVALID", "s4_packets must contain typed packets"
            )
        object.__setattr__(self, "s4_packets", packets)
        for name in ("risks", "subjects", "sites", "events", "visits", "sources"):
            object.__setattr__(
                self,
                name,
                _typed_authority_tuple(getattr(self, name), name),
            )
        if self.product_packet is not None:
            _require_frozen_dataclass(self.product_packet, "product_packet")
        _check_sha256(self.packet_digest, "packet_digest")
        _check_sha256(self.authority_hash, "authority_hash")
        expected_digest = _packet_digest(self)
        if self.packet_digest != expected_digest:
            raise R5PublicationAuthorityError(
                "PACKET_DIGEST_MISMATCH", "packet_digest does not match packet members"
            )
        if self.authority_hash != self.packet_digest:
            raise R5PublicationAuthorityError(
                "PACKET_DIGEST_MISMATCH", "authority_hash must equal packet_digest"
            )
        expected_identity = _PACKET_ID_PREFIX + self.packet_digest
        if self.packet_identity != expected_identity:
            raise R5PublicationAuthorityError(
                "PACKET_IDENTITY_MISMATCH",
                "packet_identity must be the deterministic packet prefix plus digest",
            )

    @property
    def packet_content_hash(self) -> str:
        return self.packet_digest

    @property
    def s4_packet_ids(self) -> Tuple[str, ...]:
        return tuple(packet.packet_id for packet in self.s4_packets)

    @property
    def s4_packet_digests(self) -> Tuple[str, ...]:
        return tuple(packet.packet_integrity_hash for packet in self.s4_packets)

    @property
    def accepted_risk_authority(self) -> Tuple[Any, ...]:
        return self.risks

    @property
    def accepted_subject_authority(self) -> Tuple[Any, ...]:
        return self.subjects

    @property
    def accepted_site_authority(self) -> Tuple[Any, ...]:
        return self.sites

    @property
    def accepted_event_authority(self) -> Tuple[Any, ...]:
        return self.events

    @property
    def accepted_visit_authority(self) -> Tuple[Any, ...]:
        return self.visits

    @property
    def accepted_source_authority(self) -> Tuple[Any, ...]:
        return self.sources


class R5PublicationAuthorityInputAssembler:
    """Assemble and identity-check the typed bridge input.

    The assembler has no fixture lookup, file read, model call or medical
    derivation.  ``raw_bytes`` may be supplied explicitly; when omitted, the
    bytes are copied from the caller-supplied ``R5S4RuntimeInput.raw_outputs``
    solely to make their identity explicit and to check they agree.
    """

    def assemble(
        self,
        run_identity: R5PublicationRunIdentity,
        runtime_inputs: Optional[Sequence[s4.R5S4RuntimeInput]] = None,
        *,
        runtime_input: Optional[s4.R5S4RuntimeInput] = None,
        accepted_risk_authority: Optional[Sequence[Any]] = None,
        accepted_subject_authority: Optional[Sequence[Any]] = None,
        accepted_site_authority: Optional[Sequence[Any]] = None,
        accepted_event_authority: Optional[Sequence[Any]] = None,
        accepted_visit_authority: Optional[Sequence[Any]] = None,
        accepted_source_authority: Optional[Sequence[Any]] = None,
        accepted_risks: Optional[Sequence[Any]] = None,
        accepted_subjects: Optional[Sequence[Any]] = None,
        accepted_sites: Optional[Sequence[Any]] = None,
        accepted_events: Optional[Sequence[Any]] = None,
        accepted_visits: Optional[Sequence[Any]] = None,
        accepted_sources: Optional[Sequence[Any]] = None,
        raw_bytes: Optional[Sequence[Any]] = None,
        raw_outputs: Optional[Sequence[Any]] = None,
        product_authority: Any = None,
        accepted_product_authority: Any = None,
    ) -> R5PublicationAuthorityInput:
        """Return one immutable, identity-checked publication input."""

        if type(run_identity) is not R5PublicationRunIdentity:
            raise R5PublicationAuthorityError(
                "RUN_IDENTITY_INVALID", "run_identity must be R5PublicationRunIdentity"
            )
        if runtime_input is not None:
            if runtime_inputs is not None:
                raise R5PublicationAuthorityError(
                    "RUNTIME_INPUT_AMBIGUOUS",
                    "provide runtime_input or runtime_inputs, not both",
                )
            runtime_inputs = (runtime_input,)
        if runtime_inputs is None:
            raise R5PublicationAuthorityError("RUNTIME_INPUT_REQUIRED")
        if type(runtime_inputs) is s4.R5S4RuntimeInput:
            runtime_inputs = (runtime_inputs,)
        runtime_tuple = tuple(runtime_inputs)
        if not runtime_tuple or any(
            type(item) is not s4.R5S4RuntimeInput for item in runtime_tuple
        ):
            raise R5PublicationAuthorityError(
                "RUNTIME_INPUT_INVALID", "runtime_inputs must be typed R5S4RuntimeInput values"
            )
        _check_runtime_identity(runtime_tuple, run_identity)

        if raw_bytes is not None and raw_outputs is not None:
            raise R5PublicationAuthorityError(
                "RAW_BYTES_AMBIGUOUS", "provide raw_bytes or raw_outputs, not both"
            )
        raw_source = raw_bytes if raw_bytes is not None else raw_outputs
        raw_tuple = _assemble_raw_bytes(runtime_tuple, raw_source)

        product = product_authority
        if product is not None and accepted_product_authority is not None:
            raise R5PublicationAuthorityError(
                "PRODUCT_AUTHORITY_AMBIGUOUS",
                "provide product_authority or accepted_product_authority, not both",
            )
        if product is None:
            product = accepted_product_authority
        if product is not None:
            _require_frozen_dataclass(product, "product_authority")

        risks = _choose_authority_collection(
            accepted_risk_authority,
            accepted_risks,
            product,
            "risks",
        )
        subjects = _choose_authority_collection(
            accepted_subject_authority,
            accepted_subjects,
            product,
            "subjects",
        )
        sites = _choose_authority_collection(
            accepted_site_authority,
            accepted_sites,
            product,
            "sites",
        )
        events = _choose_authority_collection(
            accepted_event_authority,
            accepted_events,
            product,
            "events",
        )
        visits = _choose_authority_collection(
            accepted_visit_authority,
            accepted_visits,
            product,
            "visits",
        )
        sources = _choose_authority_collection(
            accepted_source_authority,
            accepted_sources,
            product,
            "sources",
        )

        # These collections are the accepted typed member authorities.  The
        # bridge cannot safely materialize a product packet without them.
        for name, values in (
            ("subjects", subjects),
            ("sites", sites),
            ("events", events),
            ("visits", visits),
            ("sources", sources),
        ):
            if not values:
                raise R5PublicationAuthorityError(
                    "AUTHORITY_MEMBER_MISSING", f"accepted {name} authority is required"
                )
        if not run_identity.site_refs:
            raise R5PublicationAuthorityError("SITE_COVERAGE_REQUIRED")

        assembled = R5PublicationAuthorityInput(
            run_identity=run_identity,
            runtime_inputs=runtime_tuple,
            risks=_normalise_authority_collection(risks, "risks"),
            subjects=_normalise_authority_collection(subjects, "subjects"),
            sites=_normalise_authority_collection(sites, "sites"),
            events=_normalise_authority_collection(events, "events"),
            visits=_normalise_authority_collection(visits, "visits"),
            sources=_normalise_authority_collection(sources, "sources"),
            raw_bytes=raw_tuple,
            product_authority=product,
        )
        _check_member_join_inputs(assembled)
        return assembled

    build = assemble
    assemble_input = assemble
    __call__ = assemble


class R5PublicationAuthorityBridge:
    """Call S4 once per risk and join only accepted product members."""

    def __init__(
        self,
        product_packet_factory: Optional[Callable[[R5AuthorityPacket], Any]] = None,
        *,
        packet_factory: Optional[Callable[[R5AuthorityPacket], Any]] = None,
    ) -> None:
        if product_packet_factory is not None and packet_factory is not None:
            raise R5PublicationAuthorityError(
                "PRODUCT_FACTORY_AMBIGUOUS",
                "provide product_packet_factory or packet_factory, not both",
            )
        self.product_packet_factory = product_packet_factory or packet_factory
        if self.product_packet_factory is not None and not callable(
            self.product_packet_factory
        ):
            raise R5PublicationAuthorityError(
                "PRODUCT_FACTORY_INVALID", "product packet factory must be callable"
            )

    def build(
        self, authority_input: R5PublicationAuthorityInput
    ) -> R5AuthorityPacket:
        """Build a verified aggregate; emit nothing on any S4 failure."""

        if type(authority_input) is not R5PublicationAuthorityInput:
            raise R5PublicationAuthorityError(
                "AUTHORITY_INPUT_INVALID",
                "bridge requires R5PublicationAuthorityInput",
            )
        _check_member_join_inputs(authority_input)

        built_packets: list[s4.R5S4AuthorityPacket] = []
        # Sorting is a transport/order choice only.  It never changes any S4
        # input or reorders fields inside an S4 packet.
        runtime_inputs = tuple(
            sorted(
                authority_input.runtime_inputs,
                key=lambda item: _runtime_sort_key(item),
            )
        )
        for runtime_input in runtime_inputs:
            try:
                candidate = s4_projection.build_s4_authority_packet(runtime_input)
            except s4.S4RuntimeImplementationError as exc:
                raise R5PublicationAuthorityError(
                    "S4_BUILD_FAILED", str(exc)
                ) from exc
            except Exception as exc:  # noqa: BLE001 - trusted S4 boundary
                raise R5PublicationAuthorityError(
                    "S4_BUILD_FAILED", f"{type(exc).__name__}: {exc}"
                ) from exc
            if type(candidate) is not s4.R5S4AuthorityPacket:
                raise R5PublicationAuthorityError(
                    "S4_PACKET_INVALID", "S4 builder returned an unexpected type"
                )
            try:
                validation = s4_validator.validate_s4_authority_packet(
                    candidate, runtime_input
                )
            except s4.S4RuntimeImplementationError as exc:
                raise R5PublicationAuthorityError(
                    "S4_VALIDATION_FAILED", str(exc)
                ) from exc
            except Exception as exc:  # noqa: BLE001 - trusted S4 boundary
                raise R5PublicationAuthorityError(
                    "S4_VALIDATION_FAILED", f"{type(exc).__name__}: {exc}"
                ) from exc
            if type(validation) is not s4.R5S4ValidationResult:
                raise R5PublicationAuthorityError(
                    "S4_VALIDATION_FAILED", "S4 validator returned an unexpected type"
                )
            if validation.ok is not True:
                issue = validation.issues[0] if validation.issues else None
                code = issue.code if issue is not None else "unknown"
                raise R5PublicationAuthorityError(
                    "S4_VALIDATION_REJECTED", f"{code}: S4 packet rejected"
                )
            built_packets.append(candidate)

        packets = tuple(sorted(built_packets, key=lambda item: item.packet_id))
        _check_s4_member_closure(authority_input, packets)
        risks = _normalise_output_risks(authority_input.risks, packets)
        output_members = {
            "project_ref": authority_input.run_identity.project_ref,
            "run_ref": authority_input.run_identity.run_ref,
            "public_run_token": authority_input.run_identity.public_run_token,
            "snapshot_ref": authority_input.run_identity.snapshot_ref,
            "cutoff_ref": authority_input.run_identity.cutoff_ref,
            "site_refs": authority_input.run_identity.site_refs,
            "s4_packets": packets,
            "risks": risks,
            "subjects": _sort_authority(authority_input.subjects, "subjects"),
            "sites": _sort_authority(authority_input.sites, "sites"),
            "events": _sort_authority(authority_input.events, "events"),
            "visits": _sort_authority(authority_input.visits, "visits"),
            "sources": _sort_authority(authority_input.sources, "sources"),
        }
        digest = _aggregate_digest(output_members)
        packet = R5AuthorityPacket(
            **output_members,
            packet_identity=_PACKET_ID_PREFIX + digest,
            packet_digest=digest,
            authority_hash=digest,
            product_packet=None,
        )
        if self.product_packet_factory is not None:
            try:
                product = self.product_packet_factory(packet)
            except R5PublicationAuthorityError:
                raise
            except Exception as exc:  # noqa: BLE001 - explicit product seam
                raise R5PublicationAuthorityError(
                    "PRODUCT_PACKET_ASSEMBLY_FAILED", f"{type(exc).__name__}: {exc}"
                ) from exc
            _require_frozen_dataclass(product, "product_packet")
            product_hash = getattr(product, "authority_hash", "")
            if type(product_hash) is str and len(product_hash) == 64:
                product_digest = _aggregate_digest(
                    {
                        **output_members,
                        "product_packet_authority_hash": product_hash,
                    }
                )
                packet = R5AuthorityPacket(
                    **output_members,
                    packet_identity=_PACKET_ID_PREFIX + product_digest,
                    packet_digest=product_digest,
                    authority_hash=product_digest,
                    product_packet=product,
                )
            else:
                packet = replace(packet, product_packet=product)
        elif authority_input.product_authority is not None:
            product = authority_input.product_authority
            product_hash = getattr(product, "authority_hash", "")
            if type(product_hash) is str and len(product_hash) == 64:
                product_digest = _aggregate_digest(
                    {
                        **output_members,
                        "product_packet_authority_hash": product_hash,
                    }
                )
                packet = R5AuthorityPacket(
                    **output_members,
                    packet_identity=_PACKET_ID_PREFIX + product_digest,
                    packet_digest=product_digest,
                    authority_hash=product_digest,
                    product_packet=product,
                )
            else:
                packet = replace(packet, product_packet=product)
        return packet

    build_product_authority_packet = build
    bridge = build
    __call__ = build


# ---------------------------------------------------------------------------
# Input validation and deterministic member joins
# ---------------------------------------------------------------------------


def _strict_str_tuple(values: Iterable[str], field_name: str) -> Tuple[str, ...]:
    try:
        result = tuple(values)
    except TypeError as exc:
        raise R5PublicationAuthorityError(
            "TYPED_INPUT_REQUIRED", f"{field_name} must be iterable"
        ) from exc
    for value in result:
        if type(value) is not str or not value.strip():
            raise R5PublicationAuthorityError(
                "TYPED_INPUT_REQUIRED", f"{field_name} contains an invalid reference"
            )
    return tuple(value.strip() for value in result)


def _require_frozen_dataclass(value: Any, field_name: str) -> None:
    if not is_dataclass(value) or isinstance(value, type):
        raise R5PublicationAuthorityError(
            "TYPED_AUTHORITY_REQUIRED", f"{field_name} must be a typed dataclass"
        )
    params = getattr(type(value), "__dataclass_params__", None)
    if params is None or not getattr(params, "frozen", False):
        raise R5PublicationAuthorityError(
            "TYPED_AUTHORITY_REQUIRED", f"{field_name} must be frozen"
        )


def _typed_authority_tuple(values: Iterable[Any], field_name: str) -> Tuple[Any, ...]:
    try:
        result = tuple(values)
    except TypeError as exc:
        raise R5PublicationAuthorityError(
            "TYPED_AUTHORITY_REQUIRED", f"{field_name} must be iterable"
        ) from exc
    for index, value in enumerate(result):
        _require_frozen_dataclass(value, f"{field_name}[{index}]")
    return result


def _normalise_authority_collection(
    values: Sequence[Any], field_name: str
) -> Tuple[Any, ...]:
    result = _typed_authority_tuple(values, field_name)
    refs = [_member_ref(item, field_name) for item in result]
    if any(ref is None for ref in refs):
        raise R5PublicationAuthorityError(
            "AUTHORITY_MEMBER_IDENTITY_MISSING",
            f"{field_name} members require a stable identity reference",
        )
    if len(set(refs)) != len(refs):
        raise R5PublicationAuthorityError(
            "AUTHORITY_MEMBER_DUPLICATE", f"{field_name} member refs must be unique"
        )
    return result


def _choose_authority_collection(
    primary: Optional[Sequence[Any]],
    alias: Optional[Sequence[Any]],
    product: Any,
    field_name: str,
) -> Tuple[Any, ...]:
    if primary is not None and alias is not None:
        raise R5PublicationAuthorityError(
            "AUTHORITY_MEMBER_AMBIGUOUS", f"{field_name} has duplicate inputs"
        )
    if primary is not None:
        return tuple(primary)
    if alias is not None:
        return tuple(alias)
    if product is not None:
        candidate = getattr(product, field_name, None)
        if candidate is not None:
            return tuple(candidate)
    return ()


def _assemble_raw_bytes(
    runtime_inputs: Sequence[s4.R5S4RuntimeInput],
    raw_source: Optional[Sequence[Any]],
) -> Tuple[R5PublicationRawBytes, ...]:
    expected: dict[str, bytes] = {}
    for runtime_input in runtime_inputs:
        for raw in runtime_input.raw_outputs:
            if raw.attempt_id in expected:
                raise R5PublicationAuthorityError(
                    "RAW_BYTES_DUPLICATE", f"duplicate raw attempt {raw.attempt_id!r}"
                )
            expected[raw.attempt_id] = raw.raw_bytes
    if raw_source is None:
        return tuple(
            R5PublicationRawBytes(attempt_id=attempt_id, raw_bytes=expected[attempt_id])
            for attempt_id in sorted(expected)
        )
    supplied: list[R5PublicationRawBytes] = []
    for index, value in enumerate(tuple(raw_source)):
        if type(value) is R5PublicationRawBytes:
            supplied.append(value)
        elif type(value) is s4.R5S4RawOutputInput:
            supplied.append(
                R5PublicationRawBytes(attempt_id=value.attempt_id, raw_bytes=value.raw_bytes)
            )
        else:
            raise R5PublicationAuthorityError(
                "RAW_BYTES_INVALID", f"raw_bytes[{index}] must be typed raw bytes"
            )
    if len({item.attempt_id for item in supplied}) != len(supplied):
        raise R5PublicationAuthorityError("RAW_BYTES_DUPLICATE")
    supplied_map = {item.attempt_id: item.raw_bytes for item in supplied}
    if supplied_map != expected:
        raise R5PublicationAuthorityError(
            "RAW_BYTES_MISMATCH",
            "explicit raw bytes must exactly match the R5S4 raw-output inputs",
        )
    return tuple(supplied)


def _check_runtime_identity(
    runtime_inputs: Sequence[s4.R5S4RuntimeInput],
    identity: R5PublicationRunIdentity,
) -> None:
    seen_risks: set[str] = set()
    for index, runtime_input in enumerate(runtime_inputs):
        anchor = runtime_input.anchor
        receipt = runtime_input.authority_receipt
        accepted_risk = anchor.accepted_risk_identity
        risk_ref = accepted_risk.risk_ref
        if risk_ref in seen_risks:
            raise R5PublicationAuthorityError(
                "RUNTIME_RISK_DUPLICATE", f"duplicate runtime risk {risk_ref!r}"
            )
        seen_risks.add(risk_ref)
        for source, label in (
            (anchor, f"runtime_inputs[{index}].anchor"),
            (receipt, f"runtime_inputs[{index}].authority_receipt"),
            (accepted_risk, f"runtime_inputs[{index}].anchor.accepted_risk_identity"),
        ):
            _check_identity_fields(source, identity, label)
        _check_identity_fields(
            runtime_input.change_band,
            identity,
            f"runtime_inputs[{index}].change_band",
        )
        _check_identity_fields(
            runtime_input.deep_link_state,
            identity,
            f"runtime_inputs[{index}].deep_link_state",
        )
        for item_index, item in enumerate(runtime_input.baseline_items):
            _check_identity_fields(
                item,
                identity,
                f"runtime_inputs[{index}].baseline_items[{item_index}]",
            )


def _check_identity_fields(value: Any, identity: R5PublicationRunIdentity, label: str) -> None:
    for name, expected in (
        ("project_ref", identity.project_ref),
        ("run_ref", identity.run_ref),
        ("snapshot_ref", identity.snapshot_ref),
        ("cutoff_ref", identity.cutoff_ref),
    ):
        actual = getattr(value, name, _MISSING)
        if actual is not _MISSING and actual != expected:
            raise R5PublicationAuthorityError(
                "RUN_IDENTITY_MISMATCH", f"{label}.{name} does not match frozen run identity"
            )
    site = getattr(value, "site_ref", _MISSING)
    if site is not _MISSING and site is not None and site not in identity.site_refs:
        raise R5PublicationAuthorityError(
            "SITE_COVERAGE_MISMATCH", f"{label}.site_ref is outside frozen coverage"
        )


def _check_member_join_inputs(authority_input: R5PublicationAuthorityInput) -> None:
    identity = authority_input.run_identity
    for name in ("risks", "subjects", "sites", "events", "visits", "sources"):
        values = getattr(authority_input, name)
        if name != "risks" and not values:
            raise R5PublicationAuthorityError(
                "AUTHORITY_MEMBER_MISSING", f"accepted {name} authority is required"
            )
        _normalise_authority_collection(values, name)
        for index, item in enumerate(values):
            _check_nested_identity(item, identity, f"{name}[{index}]")
    site_refs = {
        ref for item in authority_input.sites if (ref := _member_ref(item, "sites")) is not None
    }
    if site_refs != set(identity.site_refs):
        raise R5PublicationAuthorityError(
            "SITE_COVERAGE_MISMATCH",
            "accepted site members must equal frozen site coverage",
        )
    if authority_input.product_authority is not None:
        _check_nested_identity(authority_input.product_authority, identity, "product_authority")
        product_sites = getattr(authority_input.product_authority, "sites", None)
        if product_sites is not None:
            product_site_refs = {
                ref
                for item in tuple(product_sites)
                if (ref := _member_ref(item, "sites")) is not None
            }
            if product_site_refs != set(identity.site_refs):
                raise R5PublicationAuthorityError(
                    "SITE_COVERAGE_MISMATCH",
                    "product authority sites must equal frozen site coverage",
                )


def _check_nested_identity(value: Any, identity: R5PublicationRunIdentity, label: str) -> None:
    candidates = [value]
    for path in ("scope_identity", "projection", "receipt"):
        nested = getattr(value, path, _MISSING)
        if nested is not _MISSING and nested is not None:
            candidates.append(nested)
            scope = getattr(nested, "scope_identity", _MISSING)
            if scope is not _MISSING and scope is not None:
                candidates.append(scope)
    for index, candidate in enumerate(candidates):
        _check_identity_fields(candidate, identity, f"{label}.identity[{index}]")


def _runtime_sort_key(runtime_input: s4.R5S4RuntimeInput) -> Tuple[str, str, str]:
    risk = runtime_input.anchor.accepted_risk_identity
    return (risk.risk_ref, runtime_input.anchor.anchor_identity_hash, runtime_input.authority_receipt.public_projection_id)


def _member_ref(value: Any, category: str) -> Optional[str]:
    by_category = {
        "risks": ("risk_ref", "risk_key", "risk_instance_ref", "risk_anchor_ref"),
        "subjects": ("subject_ref",),
        "sites": ("site_ref",),
        "events": ("event_ref",),
        "visits": ("visit_ref",),
        "sources": ("locator_ref", "source_locator_ref", "source_revision_ref", "revision_id"),
    }
    for name in by_category.get(category, ()):
        value_ref = getattr(value, name, _MISSING)
        if value_ref is not _MISSING and type(value_ref) is str and value_ref.strip():
            return value_ref
    return None


def _member_refs(values: Sequence[Any], category: str) -> set[str]:
    refs = {_member_ref(value, category) for value in values}
    if None in refs:
        raise R5PublicationAuthorityError(
            "AUTHORITY_MEMBER_IDENTITY_MISSING", f"{category} member identity missing"
        )
    return {ref for ref in refs if ref is not None}




def _member_index(values: Sequence[Any], category: str) -> dict[str, Any]:
    return {_member_ref(value, category): value for value in values}

def _sort_authority(values: Sequence[Any], category: str) -> Tuple[Any, ...]:
    return tuple(
        sorted(
            values,
            key=lambda value: (
                _member_ref(value, category) or "",
                _canonical_json(value),
            ),
        )
    )


def _check_s4_member_closure(
    authority_input: R5PublicationAuthorityInput,
    packets: Sequence[s4.R5S4AuthorityPacket],
) -> None:
    identity = authority_input.run_identity
    site_refs = _member_refs(authority_input.sites, "sites")
    subject_refs = _member_refs(authority_input.subjects, "subjects")
    event_refs = _member_refs(authority_input.events, "events")
    visit_refs = _member_refs(authority_input.visits, "visits")
    source_refs = _member_refs(authority_input.sources, "sources")
    subject_by_ref = _member_index(authority_input.subjects, "subjects")
    site_by_ref = _member_index(authority_input.sites, "sites")
    event_by_ref = _member_index(authority_input.events, "events")
    visit_by_ref = _member_index(authority_input.visits, "visits")
    source_pairs = _source_pairs(authority_input.sources)
    risk_by_ref = (
        _member_index(authority_input.risks, "risks")
        if authority_input.risks
        else {}
    )

    for packet in packets:
        risk = packet.risk_identity
        if risk.project_ref != identity.project_ref or risk.run_ref != identity.run_ref:
            raise R5PublicationAuthorityError("S4_MEMBER_IDENTITY_MISMATCH", packet.packet_id)
        if risk.snapshot_ref != identity.snapshot_ref or risk.cutoff_ref != identity.cutoff_ref:
            raise R5PublicationAuthorityError("S4_MEMBER_IDENTITY_MISMATCH", packet.packet_id)
        if risk.site_ref not in site_refs or risk.site_ref not in identity.site_refs:
            raise R5PublicationAuthorityError("S4_MEMBER_SITE_OUTSIDE_PRODUCT", packet.packet_id)
        if risk.subject_ref not in subject_refs or risk.spine_ref.strip() == "":
            raise R5PublicationAuthorityError("S4_MEMBER_SUBJECT_OUTSIDE_PRODUCT", packet.packet_id)
        if authority_input.risks and risk.risk_ref not in risk_by_ref:
            raise R5PublicationAuthorityError("S4_MEMBER_RISK_OUTSIDE_PRODUCT", packet.packet_id)

        subject = subject_by_ref[risk.subject_ref]
        if (
            _first_attr(subject, ("site_ref",)) != risk.site_ref
            or _first_attr(subject, ("spine_ref",)) != risk.spine_ref
        ):
            raise R5PublicationAuthorityError("S4_MEMBER_SUBJECT_IDENTITY_MISMATCH", packet.packet_id)
        site = site_by_ref[risk.site_ref]
        if _first_attr(site, ("site_ref",)) != risk.site_ref:
            raise R5PublicationAuthorityError("S4_MEMBER_SITE_IDENTITY_MISMATCH", packet.packet_id)
        if authority_input.risks:
            risk_member = risk_by_ref[risk.risk_ref]
            for name, expected in (
                ("site_ref", risk.site_ref),
                ("subject_ref", risk.subject_ref),
                ("spine_ref", risk.spine_ref),
            ):
                actual = _first_attr(risk_member, (name,))
                if actual is not None and actual != expected:
                    raise R5PublicationAuthorityError(
                        "S4_MEMBER_RISK_IDENTITY_MISMATCH", packet.packet_id
                    )

        journey = packet.journey_link
        event_ref = journey.deep_link_event_ref
        visit_ref = journey.deep_link_visit_ref
        source_ref = journey.deep_link_source_locator_ref
        if event_ref is not None:
            if event_ref not in event_refs:
                raise R5PublicationAuthorityError("S4_MEMBER_EVENT_OUTSIDE_PRODUCT", packet.packet_id)
            event = event_by_ref[event_ref]
            _check_member_relation(
                event,
                risk,
                packet.packet_id,
                "S4_MEMBER_EVENT_IDENTITY_MISMATCH",
            )
        if visit_ref is not None:
            if visit_ref not in visit_refs:
                raise R5PublicationAuthorityError("S4_MEMBER_VISIT_OUTSIDE_PRODUCT", packet.packet_id)
            visit = visit_by_ref[visit_ref]
            _check_member_relation(
                visit,
                risk,
                packet.packet_id,
                "S4_MEMBER_VISIT_IDENTITY_MISMATCH",
            )
        if source_ref is not None and source_ref not in source_refs:
            raise R5PublicationAuthorityError("S4_MEMBER_SOURCE_OUTSIDE_PRODUCT", packet.packet_id)
        receipt = packet.authority_receipt
        for pair in receipt.source_revision_content_pairs:
            if (pair.revision_id, pair.content_hash) not in source_pairs:
                raise R5PublicationAuthorityError(
                    "S4_SOURCE_REVISION_OUTSIDE_PRODUCT", packet.packet_id
                )


def _check_member_relation(
    member: Any,
    risk: s4.R5S4RiskIdentity,
    packet_id: str,
    error_code: str,
) -> None:
    for name, expected in (
        ("subject_ref", risk.subject_ref),
        ("site_ref", risk.site_ref),
        ("spine_ref", risk.spine_ref),
    ):
        actual = _first_attr(member, (name,))
        if actual is not None and actual != expected:
            raise R5PublicationAuthorityError(error_code, packet_id)
def _source_pairs(values: Sequence[Any]) -> set[Tuple[str, str]]:
    pairs: set[Tuple[str, str]] = set()
    for value in values:
        revision = _first_attr(
            value,
            (
                "source_revision_ref",
                "source_revision_id",
                "revision_id",
            ),
        )
        content = _first_attr(
            value,
            (
                "source_revision_content_hash",
                "content_hash",
                "accepted_content_hash",
            ),
        )
        if revision is not None and content is not None:
            pairs.add((revision, content))
        nested_pairs = getattr(value, "source_revision_content_pairs", _MISSING)
        if nested_pairs is not _MISSING and nested_pairs is not None:
            for pair in tuple(nested_pairs):
                pair_revision = _first_attr(pair, ("revision_id", "source_revision_ref"))
                pair_content = _first_attr(
                    pair,
                    (
                        "content_hash",
                        "accepted_content_hash",
                        "source_revision_content_hash",
                    ),
                )
                if pair_revision is not None and pair_content is not None:
                    pairs.add((pair_revision, pair_content))
    return pairs


def _normalise_output_risks(
    risks: Sequence[Any], packets: Sequence[s4.R5S4AuthorityPacket]
) -> Tuple[Any, ...]:
    if risks:
        return _sort_authority(risks, "risks")
    # The S4 risk identity is itself accepted typed authority.  This fallback
    # does not invent a product record; it preserves the authoritative leaf so
    # callers that do not have a separate product risk record can still inspect
    # the verified aggregate.
    return tuple(sorted((packet.risk_identity for packet in packets), key=lambda item: item.risk_ref))


def _first_attr(value: Any, names: Sequence[str]) -> Optional[str]:
    for name in names:
        candidate = getattr(value, name, _MISSING)
        if candidate is not _MISSING and type(candidate) is str and candidate.strip():
            return candidate
    return None


def _check_sha256(value: Any, field_name: str) -> None:
    if type(value) is not str or len(value) != _SHA256_LENGTH:
        raise R5PublicationAuthorityError(
            "DIGEST_INVALID", f"{field_name} must be a 64-character digest"
        )
    if any(character not in "0123456789abcdef" for character in value):
        raise R5PublicationAuthorityError(
            "DIGEST_INVALID", f"{field_name} must be lowercase hexadecimal"
        )


_MISSING = object()


def _canonicalise(value: Any) -> Any:
    if value is None or type(value) in (bool, int, float, str):
        return value
    if type(value) is bytes:
        return {"__bytes_b64__": base64.b64encode(value).decode("ascii")}
    if type(value) is date:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonicalise(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalise(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (tuple, list)):
        return [_canonicalise(item) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [_canonicalise(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    raise R5PublicationAuthorityError(
        "CANONICAL_INPUT_UNSUPPORTED", f"unsupported typed value {type(value).__name__}"
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalise(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _packet_payload(packet: R5AuthorityPacket) -> dict[str, Any]:
    payload = {
        "project_ref": packet.project_ref,
        "run_ref": packet.run_ref,
        "public_run_token": packet.public_run_token,
        "snapshot_ref": packet.snapshot_ref,
        "cutoff_ref": packet.cutoff_ref,
        "site_refs": packet.site_refs,
        "s4_packets": tuple(s4.packet_as_mapping(item) for item in packet.s4_packets),
        "risks": packet.risks,
        "subjects": packet.subjects,
        "sites": packet.sites,
        "events": packet.events,
        "visits": packet.visits,
        "sources": packet.sources,
    }
    if packet.product_packet is not None:
        product_hash = getattr(packet.product_packet, "authority_hash", "")
        if type(product_hash) is str and len(product_hash) == 64:
            payload["product_packet_authority_hash"] = product_hash
    return payload


def _aggregate_digest(fields_by_name: Mapping[str, Any]) -> str:
    payload = {
        name: (
            tuple(
                item
                if isinstance(item, Mapping)
                else s4.packet_as_mapping(item)
                for item in value
            )
            if name == "s4_packets"
            else value
        )
        for name, value in fields_by_name.items()
    }
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _packet_digest(packet: R5AuthorityPacket) -> str:
    return _aggregate_digest(_packet_payload(packet))


__all__ = [
    "R5AuthorityPacket",
    "R5PublicationAuthorityBridge",
    "R5PublicationAuthorityError",
    "R5PublicationAuthorityInput",
    "R5PublicationAuthorityInputAssembler",
    "R5PublicationRawBytes",
    "R5PublicationRunIdentity",
]
