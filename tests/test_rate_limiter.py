from features.servers.services.rate_limiter import (
    DEFAULT_RATE_LIMIT_BASE_DELAY_SECONDS,
    DEFAULT_RATE_LIMIT_RESET_SECONDS,
    FREE_REQUESTS,
    RateLimiter,
    rate_limit_base_delay_seconds,
    rate_limit_reset_seconds,
)


def test_rate_limit_base_delay_seconds_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_BASE_DELAY_SECONDS", raising=False)
    assert rate_limit_base_delay_seconds() == DEFAULT_RATE_LIMIT_BASE_DELAY_SECONDS


def test_rate_limit_base_delay_seconds_falls_back_on_garbage_value(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "not-a-number")
    assert rate_limit_base_delay_seconds() == DEFAULT_RATE_LIMIT_BASE_DELAY_SECONDS


def test_rate_limit_base_delay_seconds_falls_back_on_negative_value(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "-1")
    assert rate_limit_base_delay_seconds() == DEFAULT_RATE_LIMIT_BASE_DELAY_SECONDS


def test_rate_limit_base_delay_seconds_honors_zero_to_disable_throttling(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "0")
    assert rate_limit_base_delay_seconds() == 0


def test_rate_limit_base_delay_seconds_honors_valid_override(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "0.5")
    assert rate_limit_base_delay_seconds() == 0.5


def test_rate_limit_reset_seconds_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_RESET_SECONDS", raising=False)
    assert rate_limit_reset_seconds() == DEFAULT_RATE_LIMIT_RESET_SECONDS


def test_rate_limit_reset_seconds_falls_back_on_non_positive_value(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_RESET_SECONDS", "-1")
    assert rate_limit_reset_seconds() == DEFAULT_RATE_LIMIT_RESET_SECONDS


def test_zero_base_delay_disables_throttling(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "0")
    limiter = RateLimiter()
    for _ in range(50):
        assert limiter.check("9.9.9.9") is None


def test_first_free_requests_are_always_allowed():
    limiter = RateLimiter()
    for _ in range(FREE_REQUESTS):
        assert limiter.check("1.1.1.1") is None


def test_request_past_the_free_tier_is_throttled(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "10")
    limiter = RateLimiter()
    for _ in range(FREE_REQUESTS):
        assert limiter.check("2.2.2.2") is None

    retry_after = limiter.check("2.2.2.2")
    assert retry_after is not None
    assert 9 < retry_after <= 10


def test_request_allowed_once_the_tier_delay_has_elapsed(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "10")
    limiter = RateLimiter()
    for _ in range(FREE_REQUESTS):
        limiter.check("3.3.3.3")

    entry = limiter._entries["3.3.3.3"]
    entry.last_allowed_at -= 10  # pretend the 10s tier-1 wait already happened

    assert limiter.check("3.3.3.3") is None


def test_escalation_tiers_grow_10_30_120_then_times_4(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "10")
    # bigger than any tier below, keeps the idle reset out of it
    monkeypatch.setenv("RATE_LIMIT_RESET_SECONDS", "100000")
    limiter = RateLimiter()
    ip = "4.4.4.4"
    for _ in range(FREE_REQUESTS):
        limiter.check(ip)

    expected_tiers = [10, 30, 120, 480, 1920]
    for expected in expected_tiers:
        retry_after = limiter.check(ip)
        assert retry_after is not None
        assert expected - 1 < retry_after <= expected, f"expected ~{expected}s, got {retry_after}s"

        entry = limiter._entries[ip]
        entry.last_allowed_at -= expected  # pretend we already waited this tier out
        assert limiter.check(ip) is None


def test_different_ips_are_independent():
    limiter = RateLimiter()
    for _ in range(FREE_REQUESTS):
        limiter.check("5.5.5.5")

    assert limiter.check("5.5.5.5") is not None
    assert limiter.check("6.6.6.6") is None


def test_stale_entries_are_swept_from_memory(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_RESET_SECONDS", "100")
    limiter = RateLimiter()
    limiter.check("10.0.0.1")
    limiter._entries["10.0.0.1"].last_allowed_at -= 200  # long past the reset window

    limiter.check("10.0.0.2")  # any request triggers the sweep, not just one from the stale ip

    assert "10.0.0.1" not in limiter._entries


def test_rejected_attempts_do_not_shift_the_required_wait(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "10")
    limiter = RateLimiter()
    ip = "7.7.7.7"
    for _ in range(FREE_REQUESTS):
        limiter.check(ip)

    first = limiter.check(ip)
    second = limiter.check(ip)
    assert first is not None and second is not None
    assert abs(first - second) < 0.1, "spamming retries must not push the wait further out"


def test_reset_window_caps_the_effective_escalation(monkeypatch):
    # once a tier's wait is longer than the reset window, you never actually reach
    # it, waiting that long resets you first
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "10")
    monkeypatch.setenv("RATE_LIMIT_RESET_SECONDS", "300")
    limiter = RateLimiter()
    ip = "8.8.8.9"
    for _ in range(FREE_REQUESTS):
        limiter.check(ip)
    for wait in (10, 30, 120):  # tiers below the reset window escalate normally
        limiter.check(ip)
        limiter._entries[ip].last_allowed_at -= wait
        assert limiter.check(ip) is None

    assert limiter._entries[ip].allowed_count == 6  # about to require the 480s tier

    limiter.check(ip)
    limiter._entries[ip].last_allowed_at -= 480  # clears the 480s tier, but also clears the 300s reset window
    assert limiter.check(ip) is None
    assert limiter._entries[ip].allowed_count == 1, "reset wins once a tier's delay exceeds the reset window"


def test_idle_ip_gets_a_clean_slate(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "10")
    monkeypatch.setenv("RATE_LIMIT_RESET_SECONDS", "300")
    limiter = RateLimiter()
    ip = "8.8.8.8"
    for _ in range(FREE_REQUESTS):
        limiter.check(ip)
    assert limiter.check(ip) is not None  # 4th one is throttled

    limiter._entries[ip].last_allowed_at -= 300.1  # pretend this ip's been quiet past the reset window

    for _ in range(FREE_REQUESTS):
        assert limiter.check(ip) is None
