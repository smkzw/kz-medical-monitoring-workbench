"""Dual-seam publication adapter for the materialized-facts product lane.

One object serves both product seams: the R5 product adapter protocol
(``get_packet`` returning the typed facts packet, identity-bound per run and
cutoff) and the R7 publication seam (``get_authority`` returning the
publication authority packet). The publication packet carries an explicit
facts contract marker on its product packet and no S4 layer: runs in this
lane are deterministic fact verifications with no AI adjudication outputs
yet; the S4 machinery arrives together with the dual-model analysis phase.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from ...projections.publication.r5_publication_authority import (
    R5AuthorityPacket as R5PublicationPacket,
    _aggregate_digest,
)

FACTS_AUTHORITY_CONTRACT_ID = "facts-authority-v1"


class FactsPublicationAdapter:
    """Adapt the materialized facts packet to product and publication seams."""

    fixture_mode = False

    def __init__(self, facts_provider: Any) -> None:
        self._facts = facts_provider
        self._cache: dict[tuple, Any] = {}

    # -- R5 product seam ----------------------------------------------------

    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> Any:
        base = self._facts.get_packet(project_ref, None, snapshot_ref, None)
        if not run_ref and not cutoff_ref:
            return base
        key = (
            "product",
            base.snapshot_ref,
            run_ref or base.run_ref,
            cutoff_ref or "",
        )
        cached = self._cache.get(key)
        if cached is None:
            cached = replace(
                base,
                run_ref=run_ref or base.run_ref,
                cutoff_state="present" if cutoff_ref else "absent",
                cutoff_ref=cutoff_ref or None,
                authority_hash="",
                source_snapshot_sha256="",
            )
            self._cache[key] = cached
        return cached

    # -- R7 publication seam --------------------------------------------------

    def get_authority(self, identity: Any, **_: Any) -> Any:
        key = (
            "publication",
            identity.project_ref,
            identity.run_ref,
            identity.snapshot_ref,
            identity.cutoff_ref,
            tuple(sorted(identity.site_refs)),
        )
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        product = self.get_packet(
            identity.project_ref,
            run_ref=identity.run_ref,
            snapshot_ref=identity.snapshot_ref,
            cutoff_ref=identity.cutoff_ref or None,
        )
        covered = set(identity.site_refs)
        packet_sites = {site.site_ref for site in product.sites}
        if not covered >= packet_sites:
            # Partial site coverage: filter every member collection
            # consistently so member/authority closure still holds.
            product = replace(
                product,
                sites=tuple(site for site in product.sites if site.site_ref in covered),
                site_audience=tuple(
                    row for row in product.site_audience if row.site_ref in covered
                ),
                subjects=tuple(
                    item for item in product.subjects if item.site_ref in covered
                ),
                events=tuple(
                    item for item in product.events if item.site_ref in covered
                ),
                visits=tuple(
                    item for item in product.visits if item.site_ref in covered
                ),
                risks=tuple(
                    item for item in product.risks if item.site_ref in covered
                ),
                subject_flow_paths=tuple(
                    path
                    for path in product.subject_flow_paths
                    if path.site_ref in covered
                ),
                authority_hash="",
                source_snapshot_sha256="",
            )
        members = {
            "project_ref": identity.project_ref,
            "run_ref": identity.run_ref,
            "public_run_token": identity.public_run_token,
            "snapshot_ref": identity.snapshot_ref,
            "cutoff_ref": identity.cutoff_ref,
            "site_refs": tuple(sorted(covered)),
            "s4_packets": (),
            "risks": product.risks,
            "subjects": product.subjects,
            "sites": product.sites,
            "events": product.events,
            "visits": product.visits,
            "sources": product.sources,
            "product_packet_authority_hash": product.authority_hash,
        }
        digest = _aggregate_digest(members)
        members.pop("product_packet_authority_hash")
        packet = R5PublicationPacket(
            **members,
            packet_identity=f"r5-publication-authority:{digest}",
            packet_digest=digest,
            authority_hash=digest,
            product_packet=product,
        )
        self._cache[key] = packet
        return packet


class FactsProviderDispatcher:
    """Route to the per-project facts provider at call time.

    Keeps the R5/R7 routers project-generic: the dispatcher holds one
    provider per materialized-facts project workspace and resolves by the
    project reference carried on each request/identity.
    """

    fixture_mode = False

    def __init__(self, providers_by_project: dict[str, Any]) -> None:
        self._providers = dict(providers_by_project)
        self._fallback = next(iter(self._providers.values()), None)

    def _provider_for(self, project_ref: Any) -> Any:
        provider = self._providers.get(str(project_ref or ""))
        if provider is not None:
            return provider
        if len(self._providers) == 1:
            return self._fallback
        raise KeyError(
            f"no materialized facts provider for project {project_ref!r} "
            f"(available: {sorted(self._providers)})"
        )

    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> Any:
        return self._provider_for(project_ref).get_packet(
            project_ref, run_ref, snapshot_ref, cutoff_ref
        )

    def get_authority(self, identity: Any, **_: Any) -> Any:
        return self._provider_for(getattr(identity, "project_ref", "")).get_authority(
            identity
        )


__all__ = [
    "FACTS_AUTHORITY_CONTRACT_ID",
    "FactsPublicationAdapter",
    "FactsProviderDispatcher",
]
