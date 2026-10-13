"""Tests for Source Registry and Access Policies."""

from app.sources.registry import AccessMethod, SourceCategory, SourceRegistration, source_registry


def test_default_sources_registered():
    sources = source_registry.list_sources()
    assert len(sources) >= 5

    sebi = source_registry.get_source("SRC_SEBI")
    assert sebi is not None
    assert sebi.category == SourceCategory.PRIMARY_REGULATORY
    assert sebi.reliability_weight == 1.0

    amfi = source_registry.get_source("SRC_AMFI")
    assert amfi is not None
    assert amfi.category == SourceCategory.AMFI_AMC_OFFICIAL


def test_custom_source_registration():
    custom = SourceRegistration(
        source_id="SRC_TEST_ROC",
        name="Registrar of Companies (MCA21)",
        category=SourceCategory.PRIMARY_REGULATORY,
        access_method=AccessMethod.DIRECT_HTTP,
        base_url_or_pattern="https://mca.gov.in",
        reliability_weight=0.99,
        update_frequency="Quarterly",
        attribution_notice="Ministry of Corporate Affairs Official Portal",
        fallback_behavior="Log failure; prompt for ROC charge certificate.",
    )
    source_registry.register_source(custom)
    retrieved = source_registry.get_source("SRC_TEST_ROC")
    assert retrieved is not None
    assert retrieved.name == "Registrar of Companies (MCA21)"
