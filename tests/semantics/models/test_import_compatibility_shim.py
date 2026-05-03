from __future__ import annotations

import warnings


def test_legacy_and_new_nested_modules_share_identity() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        import tradingchassis_core.core.domain.processing as old_processing
        import tradingchassis_core.core.domain.types as old_types

    import tradingchassis_core.core.domain.processing as new_processing
    import tradingchassis_core.core.domain.types as new_types

    assert old_types is new_types
    assert old_processing is new_processing


def test_legacy_and_new_symbols_share_identity() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from tradingchassis_core.core.domain.configuration import (
            CoreConfiguration as OldCoreConfiguration,
        )
        from tradingchassis_core.core.domain.types import (
            ControlTimeEvent as OldControlTimeEvent,
        )
        from tradingchassis_core.core.domain.types import (
            MarketEvent as OldMarketEvent,
        )
        from tradingchassis_core.core.domain.types import (
            OrderSubmittedEvent as OldOrderSubmittedEvent,
        )

    from tradingchassis_core.core.domain.configuration import (
        CoreConfiguration as NewCoreConfiguration,
    )
    from tradingchassis_core.core.domain.types import (
        ControlTimeEvent as NewControlTimeEvent,
    )
    from tradingchassis_core.core.domain.types import (
        MarketEvent as NewMarketEvent,
    )
    from tradingchassis_core.core.domain.types import (
        OrderSubmittedEvent as NewOrderSubmittedEvent,
    )

    assert OldMarketEvent is NewMarketEvent
    assert OldOrderSubmittedEvent is NewOrderSubmittedEvent
    assert OldControlTimeEvent is NewControlTimeEvent
    assert OldCoreConfiguration is NewCoreConfiguration
