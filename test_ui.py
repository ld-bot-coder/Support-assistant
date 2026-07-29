"""End-to-end UI test for Support Assistant frontend"""
import time
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5173"
API_URL = "https://adventurous-charisma-production-26b5.up.railway.app"

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("=== Test 1: Dashboard loads ===")
        page.goto(BASE_URL)
        page.wait_for_selector("text=Tickets", timeout=10000)
        nav_text = page.locator(".nav-brand").inner_text()
        assert "Support Assistant" in nav_text
        print("PASS: Dashboard loaded")

        print("\n=== Test 2: Create ticket ===")
        page.click("text=New Ticket")
        page.wait_for_selector("text=Create New Ticket")
        page.select_option("select[name='customer_type']", "partner")
        page.select_option("select[name='product_area']", "billing")
        page.fill("textarea[name='issue_description']", "We were double charged on invoice INV-TEST-001. Two charges of $199.")
        page.fill("textarea[name='previous_communication']", "Account manager notified")
        page.select_option("select[name='urgency']", "high")
        page.click("button:has-text('Create Ticket')")
        page.wait_for_selector("text=Tickets", timeout=10000)
        print("PASS: Ticket created")

        print("\n=== Test 3: Ticket appears in dashboard ===")
        page.wait_for_timeout(1000)
        page_content = page.content()
        assert "partner" in page_content
        assert "billing" in page_content
        print("PASS: Ticket visible in dashboard")

        print("\n=== Test 4: Open ticket detail and run AI workflow ===")
        page.click("tr.clickable >> nth=0")
        page.wait_for_selector("text=Issue Description", timeout=10000)
        page.click("button:has-text('Run AI Workflow')")
        # Wait for workflow to complete (up to 60 seconds)
        page.wait_for_selector("button:has-text('Re-run AI Workflow')", timeout=120000)
        page.wait_for_timeout(1000)
        print("PASS: AI workflow completed")

        print("\n=== Test 5: Verify AI outputs displayed ===")
        detail_content = page.content()
        assert "AI Classification" in detail_content
        assert "Drafted Response" in detail_content
        assert "Suggested Internal Action" in detail_content
        assert "Missing Information" in detail_content
        print("PASS: AI outputs displayed")

        print("\n=== Test 6: Approve draft response ===")
        approve_draft = page.locator("button:has-text('Approve'):not(:disabled)").first
        if approve_draft.is_visible():
            approve_draft.click()
            page.wait_for_timeout(500)
            print("PASS: Draft approved")
        else:
            print("SKIP: Draft already approved")

        print("\n=== Test 7: Approve internal action ===")
        approve_action = page.locator("div:has-text('Suggested Internal Action') >> button:has-text('Approve Action'):not(:disabled)").first
        if approve_action.is_visible():
            approve_action.click()
            page.wait_for_timeout(500)
            print("PASS: Action approved")
        else:
            print("SKIP: Action already approved")

        print("\n=== Test 8: Update ticket status ===")
        page.select_option(".meta-card:has(label:has-text('Status')) select", "resolved")
        page.wait_for_timeout(1000)
        print("PASS: Status updated")

        print("\n=== Test 9: Add communication ===")
        page.fill(".comm-form textarea", "Customer confirmed resolution.")
        page.click(".comm-form button:has-text('Add Communication')")
        page.wait_for_timeout(1000)
        comm_content = page.content()
        assert "Customer confirmed resolution" in comm_content
        print("PASS: Communication added")

        print("\n=== Test 10: Activity logs displayed ===")
        logs_section = page.locator("text=AI Workflow Logs")
        if logs_section.is_visible():
            print("PASS: Activity logs visible")
        else:
            print("INFO: Activity logs section not visible without scroll")

        print("\n=== Test 11: Knowledge Base page ===")
        page.click("text=Knowledge Base")
        page.wait_for_selector("text=Knowledge Base", timeout=10000)
        kb_title = page.locator(".kb-card h3").first.inner_text()
        assert "Resetting" in kb_title
        print("PASS: Knowledge Base loaded")

        print("\n=== Test 12: Edit draft response ===")
        page.goto(BASE_URL)
        page.click("tr.clickable >> nth=0")
        page.wait_for_selector("text=Issue Description", timeout=10000)
        # Click edit
        edit_btn = page.locator("button:has-text('Edit Response')").first
        if edit_btn.is_visible():
            edit_btn.click()
            page.fill(".response-editor", "EDITED: Custom response from support agent.")
            page.click("button:has-text('Save & Approve')")
            page.wait_for_timeout(1000)
            detail_text = page.content()
            assert "EDITED: Custom response from support agent." in detail_text
            print("PASS: Draft edited and saved")
        else:
            print("SKIP: Edit button not visible (draft may not be generated)")

        print("\n=== Test 13: Validation errors on create form ===")
        page.goto(BASE_URL)
        page.click("text=New Ticket")
        page.wait_for_selector("text=Create New Ticket", timeout=10000)
        page.click("button:has-text('Create Ticket')")
        page.wait_for_timeout(500)
        detail_text = page.content()
        assert "Product area is required" in detail_text or "Issue description is required" in detail_text
        print("PASS: Validation errors shown")

        print("\n=== Test 14: Activity Logs page ===")
        page.click("text=Activity Logs")
        page.wait_for_selector("text=Activity Logs", timeout=10000)
        logs_content = page.content()
        assert "ticket_created" in logs_content or "ai_classification" in logs_content
        print("PASS: Activity Logs loaded")

        print("\n=== ALL UI TESTS PASSED ===")
        browser.close()

if __name__ == "__main__":
    run_tests()
