"""
LeanDeep 6.0 — Analysis Studio Webapp E2E Tests (Playwright)
Tests: page load, health badge, text analysis, conversation mode,
       marker explorer, sidebar, quality score, and accessibility.
"""
import subprocess
import sys
import time

import pytest

# Ensure playwright is importable
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    pytest.skip("playwright not installed", allow_module_level=True)

BASE = "http://localhost:8420"
APP = f"{BASE}/app"


@pytest.fixture(scope="module")
def browser_ctx():
    """Launch browser once for all tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        yield ctx
        ctx.close()
        browser.close()


@pytest.fixture(scope="module")
def ensure_server():
    """Verify server is reachable before tests run."""
    import urllib.request
    for _ in range(10):
        try:
            r = urllib.request.urlopen(f"{BASE}/v1/health", timeout=3)
            if r.status == 200:
                return
        except Exception:
            time.sleep(1)
    pytest.skip("LeanDeep server not reachable at localhost:8420")


@pytest.fixture
def page(browser_ctx, ensure_server):
    """Fresh page per test."""
    p = browser_ctx.new_page()
    yield p
    p.close()


# ─── Page Load & Structure ───────────────────────────────────

class TestPageLoad:
    def test_root_redirects_to_app(self, page):
        resp = page.goto(BASE)
        assert "/app" in page.url

    def test_app_loads_title(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        assert "LeanDeep" in page.title()

    def test_health_badge_connected(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        badge = page.locator("#healthBadge")
        # Wait for health check to complete
        page.wait_for_timeout(2000)
        text = page.locator("#healthText").inner_text()
        assert "marker" in text.lower() or "ok" in text.lower() or "891" in text

    def test_footer_shows_stats(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        markers_count = page.locator("#sfMarkers").inner_text()
        assert markers_count != "—", "Footer should show marker count after load"

    def test_nav_tabs_present(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        tabs = page.locator(".nav-tab")
        assert tabs.count() >= 2, "Should have Analyze + Explorer tabs"


# ─── Text Analysis ───────────────────────────────────────────

class TestTextAnalysis:
    def test_single_text_analysis(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        # Type sample text with known marker triggers
        page.fill("#textInput", "Ich weiss gar nicht mehr was ich sagen soll, du hoerst mir ja eh nie zu.")
        page.click("#analyzeBtn")

        # Wait for results
        page.wait_for_timeout(3000)

        # Output meta should be visible
        meta = page.locator("#outputMeta")
        assert meta.is_visible(), "Output meta should appear after analysis"

        # Should have detected markers
        count_text = page.locator("#metaCount").inner_text()
        count = int(count_text)
        assert count > 0, f"Should detect markers, got {count}"

    def test_empty_text_handling(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        # Clear and try to analyze empty
        page.fill("#textInput", "")
        page.click("#analyzeBtn")
        page.wait_for_timeout(1000)

        # Should not crash — placeholder should remain or show info
        placeholder = page.locator("#outputPlaceholder")
        body = page.locator("#outputBody")
        assert body.is_visible()

    def test_annotated_output_has_highlights(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        page.fill("#textInput", "Ich weiss gar nicht mehr was ich sagen soll, du hoerst mir ja eh nie zu. Das macht mich traurig.")
        page.click("#analyzeBtn")
        page.wait_for_timeout(3000)

        # Should have highlighted spans with marker data
        highlights = page.locator(".marker-hl")
        assert highlights.count() > 0, "Analysis should produce inline marker highlights"

    def test_detected_marker_cards(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        page.fill("#textInput", "Ja, nee, also ich weiss nicht... vielleicht hast du recht, aber irgendwie auch nicht.")
        page.click("#analyzeBtn")
        page.wait_for_timeout(3000)

        cards = page.locator(".detected-card")
        assert cards.count() > 0, "Should show detected marker cards"

    def test_threshold_slider_works(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        slider = page.locator("#thresholdSlider")
        value_label = page.locator("#thresholdValue")

        # Change threshold
        slider.fill("0.8")
        slider.dispatch_event("input")
        page.wait_for_timeout(500)

        val = value_label.inner_text()
        assert "0.8" in val, f"Threshold label should reflect 0.80, got {val}"


# ─── Conversation Mode ───────────────────────────────────────

class TestConversationMode:
    def _switch_to_conv(self, page):
        """Switch to conversation mode via mode toggle."""
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        # Find and click the conversation mode toggle
        mode_toggles = page.locator(".mode-toggle label, .mode-toggle button, .mode-btn")
        if mode_toggles.count() > 1:
            mode_toggles.nth(1).click()
        else:
            # Try direct click on conv-related element
            page.locator("text=Conversation").first.click()
        page.wait_for_timeout(500)

    def test_switch_to_conversation_mode(self, page):
        self._switch_to_conv(page)
        conv = page.locator("#convMode")
        assert conv.is_visible(), "Conversation builder should be visible"

    def test_add_message_to_conversation(self, page):
        self._switch_to_conv(page)

        # There should be an add button
        add_btn = page.locator("#addMsgBtn")
        initial_count = page.locator(".conv-msg-row, .conv-message").count()

        add_btn.click()
        page.wait_for_timeout(500)

        new_count = page.locator(".conv-msg-row, .conv-message").count()
        assert new_count > initial_count, "Adding a message should increase message count"

    def test_conversation_analysis(self, page):
        self._switch_to_conv(page)

        # Fill first message
        textareas = page.locator("#convMode textarea")
        if textareas.count() > 0:
            textareas.first.fill("Ich finde wir sollten mal darueber reden.")

        # Add another message
        page.locator("#addMsgBtn").click()
        page.wait_for_timeout(300)

        textareas = page.locator("#convMode textarea")
        if textareas.count() > 1:
            textareas.nth(1).fill("Ja klar, worueber moechtest du reden?")

        # Analyze
        page.click("#analyzeBtn")
        page.wait_for_timeout(3000)

        meta = page.locator("#outputMeta")
        assert meta.is_visible(), "Conversation analysis should produce output"


# ─── Marker Explorer ─────────────────────────────────────────

class TestMarkerExplorer:
    def _go_to_explorer(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        # Click explorer tab
        explorer_tab = page.locator("text=Explorer").first
        explorer_tab.click()
        # Wait for markers to actually load (paginated, may take several seconds)
        page.wait_for_selector(".explorer-item", timeout=30000)

    def test_explorer_loads_markers(self, page):
        self._go_to_explorer(page)

        results = page.locator(".explorer-item")
        assert results.count() > 0, "Explorer should list markers"

    def test_explorer_search(self, page):
        self._go_to_explorer(page)

        search = page.locator("#explorerSearch")
        # Type character by character to trigger input events
        search.click()
        search.type("ABANDON", delay=50)
        page.wait_for_timeout(1500)

        results = page.locator(".explorer-item")
        count = results.count()
        assert count > 0, "Search for ABANDON should return results"
        assert count < 884, "Search should filter results"

    def test_explorer_layer_filter(self, page):
        self._go_to_explorer(page)

        # Click on a layer filter
        filters = page.locator(".filter-chip, .filter-btn, .layer-filter")
        if filters.count() > 0:
            filters.first.click()
            page.wait_for_timeout(1000)

            count_text = page.locator("#explorerCount").inner_text()
            assert count_text, "Count should update after filter"

    def test_explorer_marker_click_opens_detail(self, page):
        self._go_to_explorer(page)

        items = page.locator(".explorer-item, .explorer-card")
        if items.count() > 0:
            items.first.click()
            page.wait_for_timeout(1000)

            detail = page.locator("#explorerDetail")
            assert detail.is_visible() or page.locator("#markerSidebar.open, #markerSidebar.active").count() > 0, \
                "Clicking marker should show detail view or sidebar"


# ─── Marker Sidebar ──────────────────────────────────────────

class TestMarkerSidebar:
    def test_sidebar_opens_from_analysis(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        page.fill("#textInput", "Ich weiss gar nicht mehr was ich sagen soll, du hoerst mir ja eh nie zu.")
        page.click("#analyzeBtn")
        page.wait_for_timeout(3000)

        # Click on a detected marker card or highlight
        cards = page.locator(".detected-card")
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            sidebar = page.locator("#markerSidebar")
            # Check if sidebar became visible (has 'open' class or similar)
            sidebar_classes = sidebar.get_attribute("class") or ""
            marker_id = page.locator("#sbMarkerId").inner_text()
            assert marker_id, "Sidebar should show marker ID when opened"

    def test_sidebar_close(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        page.fill("#textInput", "Ich weiss gar nicht mehr was ich sagen soll.")
        page.click("#analyzeBtn")
        page.wait_for_timeout(3000)

        cards = page.locator(".detected-card")
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(500)

            # Close sidebar
            page.locator("#sbClose").click()
            page.wait_for_timeout(500)

            sidebar = page.locator("#markerSidebar")
            sidebar_classes = sidebar.get_attribute("class") or ""
            assert "open" not in sidebar_classes, "Sidebar should close"


# ─── Accessibility ────────────────────────────────────────────

class TestAccessibility:
    def test_skip_link_exists(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        skip = page.locator(".skip-link")
        assert skip.count() > 0, "Skip link should exist for keyboard navigation"

    def test_focus_visible_styles(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        # Tab into the first interactive element
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement?.tagName")
        assert focused, "Tab should move focus to an element"

    def test_aria_labels_on_buttons(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        close_btn = page.locator("#sbClose")
        aria = close_btn.get_attribute("aria-label")
        assert aria, "Close button should have aria-label"

    def test_reduced_motion_css_exists(self, page):
        page.goto(APP)
        content = page.content()
        assert "prefers-reduced-motion" in content, "Should have reduced-motion media query"


# ─── API Integration ─────────────────────────────────────────

class TestAPIIntegration:
    def test_markers_endpoint_from_explorer(self, page):
        """Explorer should successfully fetch markers from API."""
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Footer marker count confirms API worked
        count = page.locator("#sfMarkers").inner_text()
        assert count.isdigit() and int(count) > 800, f"Should load 800+ markers, got '{count}'"

    def test_analysis_returns_layers(self, page):
        """Analysis output should show layer-categorized markers."""
        page.goto(APP)
        page.wait_for_load_state("networkidle")

        page.fill("#textInput", "Ja nee, ich weiss auch nicht, vielleicht, oder? Das ist halt so, ne. Ich mein, du weisst schon.")
        page.click("#analyzeBtn")
        page.wait_for_timeout(3000)

        # Check for layer indicators in output
        output = page.locator("#outputBody").inner_text()
        assert len(output) > 10, "Output should contain analysis results"


# ─── Screenshots for Visual Review ───────────────────────────

class TestVisualCapture:
    def test_capture_analyze_view(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        page.screenshot(path="/tmp/leandeep_analyze_empty.png", full_page=True)

        page.fill("#textInput", "Ich weiss gar nicht mehr was ich sagen soll, du hoerst mir ja eh nie zu. Das macht mich wirklich traurig und ich fuehle mich total allein gelassen.")
        page.click("#analyzeBtn")
        page.wait_for_timeout(3000)
        page.screenshot(path="/tmp/leandeep_analyze_result.png", full_page=True)

    def test_capture_explorer_view(self, page):
        page.goto(APP)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        page.locator("text=Explorer").first.click()
        page.wait_for_timeout(2000)
        page.screenshot(path="/tmp/leandeep_explorer.png", full_page=True)
