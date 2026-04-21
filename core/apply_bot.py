"""
Auto-apply engine.
Handles Naukri quick-apply, LinkedIn Easy Apply, and generic form fill.
"""

import time, re
from datetime import datetime


def _wait(driver, by, selector, timeout=10):
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))


def _click_safe(driver, element):
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


# ── Naukri Apply ──────────────────────────────────────────────

def apply_naukri(driver, job: dict, prefs: dict, cover_letter: str) -> dict:
    """Apply to a Naukri job. Driver must already be logged in."""
    from selenium.webdriver.common.by import By
    try:
        driver.get(job["url"])
        time.sleep(2)

        # Click Apply button
        btns = driver.find_elements(By.XPATH, '//button[contains(text(),"Apply") or contains(text(),"apply")]')
        if not btns:
            return {"success": False, "reason": "No apply button found"}
        _click_safe(driver, btns[0])
        time.sleep(2)

        # Handle cover letter field if present
        cl_fields = driver.find_elements(By.XPATH, '//textarea[contains(@placeholder,"cover") or contains(@name,"coverLetter")]')
        if cl_fields and cover_letter:
            cl_fields[0].clear()
            cl_fields[0].send_keys(cover_letter[:2000])

        # Submit
        submit = driver.find_elements(By.XPATH, '//button[contains(text(),"Submit") or contains(text(),"Apply Now")]')
        if submit:
            _click_safe(driver, submit[0])
            time.sleep(2)
            return {"success": True, "reason": "Applied via Naukri"}

        return {"success": False, "reason": "Submit button not found"}
    except Exception as e:
        return {"success": False, "reason": str(e)}


def login_naukri(driver, email: str, password: str) -> bool:
    from selenium.webdriver.common.by import By
    try:
        driver.get("https://www.naukri.com/nlogin/login")
        time.sleep(2)
        driver.find_element(By.ID, "usernameField").send_keys(email)
        driver.find_element(By.ID, "passwordField").send_keys(password)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(3)
        return "naukri.com" in driver.current_url
    except Exception:
        return False


# ── LinkedIn Easy Apply ───────────────────────────────────────

def login_linkedin(driver, email: str, password: str) -> bool:
    from selenium.webdriver.common.by import By
    try:
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(3)
        return "feed" in driver.current_url or "linkedin.com/in/" in driver.current_url
    except Exception:
        return False


def apply_linkedin(driver, job: dict, prefs: dict, cover_letter: str) -> dict:
    """Apply via LinkedIn Easy Apply multi-step modal."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    try:
        driver.get(job["url"])
        time.sleep(2)

        # Find Easy Apply button
        ea_btn = driver.find_elements(By.XPATH, '//button[contains(@class,"jobs-apply-button")]')
        if not ea_btn:
            return {"success": False, "reason": "Not an Easy Apply job"}
        _click_safe(driver, ea_btn[0])
        time.sleep(2)

        # Step through modal pages (max 5 steps)
        for step in range(5):
            # Fill phone if asked
            phone_fields = driver.find_elements(By.XPATH, '//input[@type="tel"]')
            if phone_fields and prefs.get("phone"):
                for f in phone_fields:
                    if not f.get_attribute("value"):
                        f.send_keys(prefs["phone"])

            # Cover letter text area
            cl_areas = driver.find_elements(By.XPATH, '//textarea[contains(@id,"cover-letter") or contains(@aria-label,"cover")]')
            if cl_areas and cover_letter:
                cl_areas[0].clear()
                cl_areas[0].send_keys(cover_letter[:2000])

            # Check for Submit or Next
            submit = driver.find_elements(By.XPATH, '//button[contains(@aria-label,"Submit application")]')
            if submit:
                _click_safe(driver, submit[0])
                time.sleep(2)
                return {"success": True, "reason": "Applied via LinkedIn Easy Apply"}

            next_btn = driver.find_elements(By.XPATH, '//button[contains(@aria-label,"Continue") or contains(@aria-label,"Next")]')
            if next_btn:
                _click_safe(driver, next_btn[0])
                time.sleep(1.5)
            else:
                break

        return {"success": False, "reason": "Could not complete Easy Apply flow"}
    except Exception as e:
        return {"success": False, "reason": str(e)}


# ── Generic apply (Instahyre / Foundit) ───────────────────────

def apply_generic(driver, job: dict, prefs: dict, cover_letter: str) -> dict:
    """Generic form-fill apply for other portals."""
    from selenium.webdriver.common.by import By
    try:
        driver.get(job["url"])
        time.sleep(2)

        # Find and click any apply button
        for text in ["Apply Now", "Apply", "Quick Apply", "1-Click Apply"]:
            btns = driver.find_elements(By.XPATH, f'//button[contains(text(),"{text}")] | //a[contains(text(),"{text}")]')
            if btns:
                _click_safe(driver, btns[0])
                time.sleep(2)
                break

        # Fill name
        name_fields = driver.find_elements(By.XPATH, '//input[@name="name" or @placeholder="Name" or @id="name"]')
        if name_fields and prefs.get("name"):
            name_fields[0].clear()
            name_fields[0].send_keys(prefs["name"])

        # Fill email
        email_fields = driver.find_elements(By.XPATH, '//input[@type="email"]')
        if email_fields and prefs.get("email"):
            email_fields[0].clear()
            email_fields[0].send_keys(prefs["email"])

        # Fill cover letter
        cl_areas = driver.find_elements(By.TAG_NAME, "textarea")
        if cl_areas and cover_letter:
            cl_areas[0].send_keys(cover_letter[:2000])

        # Submit
        for text in ["Submit", "Send Application", "Apply"]:
            submit = driver.find_elements(By.XPATH, f'//button[contains(text(),"{text}")]')
            if submit:
                _click_safe(driver, submit[0])
                time.sleep(2)
                return {"success": True, "reason": f"Applied via {job.get('portal','generic')}"}

        return {"success": False, "reason": "Submit button not found"}
    except Exception as e:
        return {"success": False, "reason": str(e)}


# ── Master apply dispatcher ───────────────────────────────────

def auto_apply_job(job: dict, prefs: dict, settings: dict,
                   cover_letter: str, driver=None) -> dict:
    """
    Apply to a single job. Creates driver if not provided.
    Returns {success, reason, applied_at}
    """
    own_driver = driver is None
    if own_driver:
        try:
            from core.scrapers import _make_driver
            driver = _make_driver(headless=settings.get("headless_browser", True))
        except Exception as e:
            return {"success": False, "reason": f"Browser error: {e}", "applied_at": datetime.now().isoformat()}

    portal = job.get("portal", "")
    result = {"success": False, "reason": "Unknown portal", "applied_at": datetime.now().isoformat()}

    try:
        if portal == "naukri":
            if settings.get("naukri_email") and settings.get("naukri_password"):
                login_naukri(driver, settings["naukri_email"], settings["naukri_password"])
            result = apply_naukri(driver, job, prefs, cover_letter)

        elif portal == "linkedin":
            if settings.get("linkedin_email") and settings.get("linkedin_password"):
                login_linkedin(driver, settings["linkedin_email"], settings["linkedin_password"])
            result = apply_linkedin(driver, job, prefs, cover_letter)

        else:
            result = apply_generic(driver, job, prefs, cover_letter)

    except Exception as e:
        result = {"success": False, "reason": str(e)}

    result["applied_at"] = datetime.now().isoformat()

    if own_driver:
        try:
            driver.quit()
        except Exception:
            pass

    return result


def run_bulk_apply(jobs: list, prefs: dict, settings: dict,
                   ai_engine, progress_callback=None) -> list:
    """
    Apply to multiple jobs. Returns list of result dicts.
    Creates ONE shared browser session per portal to reuse login.
    """
    from core.scrapers import _make_driver
    results = []
    limit = settings.get("daily_apply_limit", 30)
    headless = settings.get("headless_browser", True)

    # Group by portal for session reuse
    from collections import defaultdict
    by_portal = defaultdict(list)
    for job in jobs[:limit]:
        by_portal[job.get("portal", "generic")].append(job)

    for portal, portal_jobs in by_portal.items():
        driver = None
        try:
            driver = _make_driver(headless)

            # Login once per portal
            if portal == "naukri" and settings.get("naukri_email"):
                login_naukri(driver, settings["naukri_email"], settings["naukri_password"])
            elif portal == "linkedin" and settings.get("linkedin_email"):
                login_linkedin(driver, settings["linkedin_email"], settings["linkedin_password"])

            for i, job in enumerate(portal_jobs):
                if progress_callback:
                    progress_callback(job, i, len(portal_jobs))

                cl = ai_engine.generate_cover_letter(job, prefs,
                    prefs.get("cover_letter_template",""),
                    settings.get("groq_api_key",""))

                result = auto_apply_job(job, prefs, settings, cl, driver=driver)
                result["job"] = job
                result["cover_letter"] = cl
                results.append(result)
                time.sleep(2)  # polite delay between applications

        except Exception as e:
            pass
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    return results
