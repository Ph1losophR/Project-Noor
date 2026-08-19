"""Nothing crosses the boundary uncanonicalised (SSOT §3.1, §6).

A boundary claim, not a per-case one: over arbitrary value strings, unit
strings, observables, mapping states, and source statuses, the four-state
contract holds and an accepted observation always has a resolved unit, a
canonical value inside the operational envelope, a status the source has not
withdrawn, and no unexplained passage.
"""

import string
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from noor.canon.models import (
    ACCEPTED_FAMILY,
    RESOLVED_UNITS,
    WITHDRAWN_SOURCE_STATUSES,
    MappingInfo,
    MappingStatus,
    QualityState,
    RejectionReason,
    ReportedValue,
    SourceStatus,
)
from noor.canon.pipeline import canonicalise
from noor.canon.plausibility import EnvelopePosition, locate
from noor.catalogue.registry_loader import load_registry
from tests.conftest import REGISTRY_PATH, make_capture

REGISTRY = load_registry(REGISTRY_PATH)
OBSERVABLES = sorted(REGISTRY.entries)

VALUELESS_REJECTIONS = {
    RejectionReason.parse_failure,
    RejectionReason.unit_ambiguous,
    RejectionReason.mapping_unusable,
    RejectionReason.source_status_unusable,
}

value_strings = st.one_of(
    st.decimals(
        min_value=Decimal("-100"),
        max_value=Decimal("3000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ).map(str),
    st.text(alphabet=string.ascii_letters + string.digits + ".,+- \t", max_size=12),
)
unit_strings = st.one_of(
    st.sampled_from(
        [
            "mmol/L",
            "mg/dL",
            "%",
            "mm[Hg]",
            "/min",
            "kg",
            "Cel",
            "[degF]",
            "umol/L",
            "mL/min/{1.73_m2}",
            "mmol/mol",
        ]
    ),
    st.text(alphabet=string.ascii_letters + string.digits + "/%[]", max_size=10),
)
mapping_statuses = st.sampled_from(list(MappingStatus))
source_statuses = st.sampled_from(list(SourceStatus))
observables = st.sampled_from(OBSERVABLES)


@given(
    observable=observables,
    value=value_strings,
    unit=unit_strings,
    mapping=mapping_statuses,
    status=source_statuses,
)
def test_nothing_crosses_the_boundary_uncanonicalised(observable, value, unit, mapping, status):
    # Arrange
    capture = make_capture(
        observable=observable,
        as_reported=ReportedValue(value=value, unit=unit),
        mapping=MappingInfo(status=mapping),
        source_status=status,
    )

    # Act — canon never raises on data, only on misuse
    result = canonicalise(capture, REGISTRY)

    # Assert
    assert result.as_reported == capture.as_reported  # never mutates (§6.1)
    if result.quality.state in ACCEPTED_FAMILY:
        # §14 step 2: no observation reaches the engine with an unresolved unit
        assert result.canonical is not None
        assert result.quality.unit_resolution in RESOLVED_UNITS
        assert result.quality.suspicions == ()
        assert result.quality.accepted_via is not None
        # §5: a record the source withdrew never becomes a fact
        assert result.source_status not in WITHDRAWN_SOURCE_STATUSES
        entry = REGISTRY.entry(observable)
        assert locate(result.canonical.value, entry) is EnvelopePosition.within_operational
    if result.quality.state is QualityState.rejected and (
        set(result.quality.rejection_reasons) & VALUELESS_REJECTIONS
    ):
        # a valueless rejection never carries a canonical value (§6.3)
        assert result.canonical is None


@given(observable=observables, value=value_strings, unit=unit_strings)
def test_canonicalise_is_deterministic(observable, value, unit):
    # Arrange
    capture = make_capture(observable=observable, as_reported=ReportedValue(value=value, unit=unit))

    # Act
    first = canonicalise(capture, REGISTRY)
    second = canonicalise(capture, REGISTRY)

    # Assert — replay starts here (§8.4 invariant 6's foundation)
    assert first == second
