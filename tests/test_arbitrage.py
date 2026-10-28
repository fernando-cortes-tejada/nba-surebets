import pytest

from surebets import arbitrage as arb


def test_two_way_return_matches_closed_form():
    o1, o2 = 2.08, 2.00
    assert arb.guaranteed_return([o1, o2]) == pytest.approx(o1 * o2 / (o1 + o2) - 1)


def test_fair_market_is_not_an_arbitrage():
    assert not arb.is_arbitrage([2.0, 2.0])
    assert arb.guaranteed_return([2.0, 2.0]) == pytest.approx(0.0)


def test_typical_bookmaker_margin_is_negative():
    assert arb.guaranteed_return([1.91, 1.91]) < 0


@pytest.mark.parametrize("odds", [[2.08, 2.00], [3.1, 3.4, 3.6], [1.5, 4.2]])
def test_optimal_stakes_pay_the_same_on_every_outcome(odds):
    stakes = arb.optimal_stakes(odds, bankroll=100)
    payouts = [s * o for s, o in zip(stakes, odds)]
    assert sum(stakes) == pytest.approx(100)
    assert max(payouts) == pytest.approx(min(payouts))
    assert min(payouts) - 100 == pytest.approx(100 * arb.guaranteed_return(odds))


def test_three_way_arbitrage():
    odds = [3.1, 3.4, 3.6]  # 1/3.1 + 1/3.4 + 1/3.6 = 0.894
    assert arb.is_arbitrage(odds)
    assert arb.guaranteed_return(odds) == pytest.approx(0.1180, abs=1e-4)


def test_capped_stakes_respect_the_cap_and_increment():
    stakes, profit = arb.capped_stakes([2.08, 2.00], max_stake=50, increment=0.5)
    assert max(stakes) <= 50
    assert all((s / 0.5).is_integer() for s in stakes)
    assert profit > 0


def test_coarse_rounding_can_erase_a_thin_edge():
    # a 0.57% edge does not survive rounding stakes to whole units
    _, profit = arb.capped_stakes([1.93, 2.10], max_stake=50, increment=1)
    assert profit < 0


@pytest.mark.parametrize("odds", [[2.0], [1.0, 3.0], [0.5, 2.0], [float("inf"), 2.0]])
def test_invalid_odds_are_rejected(odds):
    with pytest.raises(ValueError):
        arb.book_sum(odds)
