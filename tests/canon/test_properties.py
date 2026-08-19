"""Nothing crosses the boundary uncanonicalised (SSOT §3.1, §6).

A boundary claim, not a per-case one: over arbitrary value strings, unit
strings, observables, mapping states, and source statuses, the four-state
contract holds and an accepted observation always has a resolved unit, a
canonical value inside the operational envelope, a status the source has not
withdrawn, and no unexplained passage.
"""

import string
from datetime import timedelta
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
    ReportedValue,
    SourceStatus,
)
from noor.canon.pipeline import canonicalise
from noor.canon.plausibility import EnvelopePosition, locate
from noor.catalogue.registry_loader import load_registry
from tests.conftest import (
    REGISTRY_PATH,
    T0,
    VALUELESS_REJECTIONS,
    make_capture,
)

REGISTRY = load_registry(REGISTRY_PATH)
OBSERVABLES = sorted(REGISTRY.entries)

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

# Glucose priors as a source might have sent them: two identifiers so records
# collide, two versions so a correction supersedes (§5), and hours spanning the
# 4-hour delta window from both sides.
prior_specs = st.lists(
    st.tuples(
        st.sampled_from(["1.0", "5.5", "9.0", "30.0", "100"]),
        st.sampled_from(["mmol/L", "mg/dL"]),
        st.sampled_from([1, 3, 5]),
        st.sampled_from([1, 2]),
        st.sampled_from(["PRIOR-A", "PRIOR-B"]),
    ),
    max_size=3,
)


def stored_glucose_priors(specs):
    """The specs as canon would have stored them, provenance and all (§6.3)."""
    return [
        canonicalise(
            make_capture(
                value=value,
                unit=unit,
                effective_time=T0 - timedelta(hours=hours),
                source_version=version,
                source_identifier=identifier,
            ),
            REGISTRY,
        )
        for value, unit, hours, version, identifier in specs
    ]


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


@given(
    value=st.sampled_from(["5.5", "14.0", "0.3"]),
    orders=prior_specs.flatmap(lambda specs: st.tuples(st.just(specs), st.permutations(specs))),
)
def test_a_verdict_never_depends_on_the_order_the_priors_arrive_in(value, orders):
    # Arrange — §5 writes a verdict into a record that is never rewritten, so a
    # verdict that moved with the order a query returned rows in would make one
    # history mean two things. Three selections read this list: the version
    # reducer, the unit-change baseline, and the delta baseline.
    capture = make_capture(value=value, unit="mmol/L")
    arrived, rearrived = (stored_glucose_priors(specs) for specs in orders)

    # Act
    first = canonicalise(capture, REGISTRY, priors=arrived)
    second = canonicalise(capture, REGISTRY, priors=rearrived)

    # Assert
    assert first == second
