"""Deterministic real-file admission (Phase C C1).

The staging module is the isolated-copy seam: it admits read-only source
files into the workspace without ever writing into the source tree.
"""

from .staging import (
    MANIFEST_NAME,
    STAGING_SCHEMA_NAME,
    STAGING_SCHEMA_VERSION,
    StagedFile,
    StagingAttempt,
    StagingError,
    StagingHashMismatchError,
    StagingIncompleteError,
    StagingSourceError,
    list_attempt_ids,
    load_attempt,
    sha256_file,
    stage_copy,
)
from .pipeline import (
    ADMISSION_RECORD_KIND,
    DEFAULT_LISTING_SUFFIXES,
    LOCATOR_INDEX_KIND,
    AdmissionPipelineError,
    DataAdmissionPipeline,
)

__all__ = [
    "MANIFEST_NAME",
    "STAGING_SCHEMA_NAME",
    "STAGING_SCHEMA_VERSION",
    "StagedFile",
    "StagingAttempt",
    "StagingError",
    "StagingHashMismatchError",
    "StagingIncompleteError",
    "StagingSourceError",
    "list_attempt_ids",
    "load_attempt",
    "sha256_file",
    "stage_copy",
    "ADMISSION_RECORD_KIND",
    "DEFAULT_LISTING_SUFFIXES",
    "LOCATOR_INDEX_KIND",
    "AdmissionPipelineError",
    "DataAdmissionPipeline",
]
