"""
Test: กดไปกลับหน้าระบุปลายทาง (กรอกหมายเลขไปรษณีย์) วนซ้ำ
ทดสอบ navigation ระหว่างหน้า "ระบุปลายทาง" <-> หน้า "เลือกบริการ"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Automation-Team'))

import time
import datetime
from pywinauto.application import Application
from pywinauto import mouse


# ============================================================
# CONFIG
# ============================================================
REPEAT_COUNT  = 10          # จำนวนรอบที่จะกดไปกลับ
STEP_DELAY    = 1.0         # วินาที รอระหว่าง step
POSTAL_CODE   = "10210"     # รหัสไปรษณีย์ที่ใช้ทดสอบ
PAGE_TIMEOUT  = 15          # วินาที รอสูงสุดให้หน้าโหลด
PAGE_POLL     = 0.5         # วินาที ความถี่ในการ poll


# ============================================================
# HELPERS
# ============================================================

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def fill_postal_code(window, postal_code):
    """กรอกรหัสไปรษณีย์ในหน้าระบุปลายทาง"""
    try:
        edits = [e for e in window.descendants(control_type="Edit") if e.is_visible()]

        # วิธี 1: หา edit ที่ automation_id หรือ name มีคำว่า PostalCode
        for edit in edits:
            aid  = edit.element_info.automation_id or ""
            name = edit.element_info.name or ""
            if "PostalCode" in aid or "รหัสไปรษณีย์" in name or "Postal" in name:
                edit.click_input()
                edit.type_keys("^a", pause=0.1)
                edit.type_keys(str(postal_code), with_spaces=True)
                log(f"   [/] กรอกรหัสไปรษณีย์: {postal_code}")
                return True

        # วิธี 2: ใช้ edit box แรกที่มองเห็น (fallback)
        if edits:
            edits[0].click_input()
            edits[0].type_keys("^a", pause=0.1)
            edits[0].type_keys(str(postal_code), with_spaces=True)
            log(f"   [/] กรอกรหัสไปรษณีย์: {postal_code} (fallback)")
            return True

    except Exception as e:
        log(f"   [WARN] fill_postal_code error: {e}")

    log("   [!] ไม่พบ edit box สำหรับกรอกรหัสไปรษณีย์")
    return False


def click_next(window):
    """กดปุ่มถัดไป"""
    try:
        candidates = []
        for child in window.descendants():
            if not child.is_visible():
                continue
            txt = child.window_text().strip()
            aid = child.element_info.automation_id or ""
            if aid == "LocalCommand_Submit" or txt == "ถัดไป":
                # กรอง กลับ / ยกเลิก ออก
                if not any(kw in txt for kw in ["กลับ", "ยกเลิก", "Back", "Cancel"]):
                    candidates.append(child)

        if candidates:
            # เลือกปุ่มที่อยู่ล่างสุด-ขวาสุด
            candidates.sort(key=lambda x: (x.rectangle().top, x.rectangle().left))
            candidates[-1].click_input()
            log("   [/] กดปุ่ม 'ถัดไป'")
            return True
    except Exception as e:
        log(f"   [WARN] click_next error: {e}")

    # Fallback: กด Enter
    try:
        window.type_keys("{ENTER}")
        log("   [/] กด Enter (fallback ถัดไป)")
        return True
    except:
        pass

    log("   [!] ไม่พบปุ่มถัดไป")
    return False


def click_back(window):
    """กดปุ่มกลับ"""
    try:
        for child in window.descendants():
            if not child.is_visible():
                continue
            txt = child.window_text().strip()
            if txt in ["กลับ", "ย้อนกลับ", "Back"]:
                child.click_input()
                log("   [/] กดปุ่ม 'กลับ'")
                return True
    except Exception as e:
        log(f"   [WARN] click_back error: {e}")

    # Fallback: กด ESC
    try:
        window.type_keys("{ESC}")
        log("   [/] กด ESC (fallback กลับ)")
        return True
    except:
        pass

    log("   [!] ไม่พบปุ่มกลับ")
    return False


def is_on_postal_page(window):
    """ตรวจสอบว่าอยู่ที่หน้า 'ระบุปลายทาง' หรือไม่"""
    try:
        for child in window.descendants():
            if not child.is_visible():
                continue
            txt = child.window_text()
            if "ระบุปลายทาง" in txt or "รหัสไปรษณีย์" in txt:
                return True
    except:
        pass
    return False


def is_on_service_page(window):
    """ตรวจสอบว่าอยู่ที่หน้า 'เลือกบริการ' หรือไม่"""
    try:
        for child in window.descendants():
            if not child.is_visible():
                continue
            txt = child.window_text()
            if "เลือกบริการ" in txt or "EMS" in txt or "eCo-Post" in txt:
                return True
    except:
        pass
    return False


def wait_for_page(window, check_fn, label, timeout=PAGE_TIMEOUT, poll=PAGE_POLL):
    """รอจนกว่า check_fn จะ return True หรือ timeout"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if check_fn(window):
            log(f"   [/] หน้า '{label}' โหลดเสร็จแล้ว")
            return True
        time.sleep(poll)
    log(f"   [!] Timeout รอหน้า '{label}' ({timeout}s)")
    return False


# ============================================================
# MAIN TEST
# ============================================================

def run_back_forth_test(main_window, repeat=REPEAT_COUNT):
    """
    กดไปกลับหน้าระบุปลายทาง <-> เลือกบริการ จำนวน repeat รอบ
    """
    log(f"=== START: test_back_forth_postal | {repeat} รอบ ===")
    results = []

    for i in range(1, repeat + 1):
        log(f"\n--- รอบที่ {i}/{repeat} ---")

        # ---- ตรวจว่าอยู่ที่หน้าระบุปลายทาง ----
        if not is_on_postal_page(main_window):
            log(f"   [WARN] ไม่อยู่ที่หน้าระบุปลายทาง -> ข้ามรอบนี้")
            results.append({"round": i, "status": "SKIP", "reason": "not on postal page"})
            continue

        # ---- FORWARD: กรอก postal -> กด ถัดไป ----
        filled = fill_postal_code(main_window, POSTAL_CODE)
        if not filled:
            results.append({"round": i, "status": "FAIL", "step": "fill_postal"})
            continue

        time.sleep(STEP_DELAY)

        ok_next = click_next(main_window)
        if not ok_next:
            results.append({"round": i, "status": "FAIL", "step": "click_next"})
            continue

        # รอจนหน้าเลือกบริการโหลดเสร็จ (หมุนนานแค่ไหนก็รอ)
        if not wait_for_page(main_window, is_on_service_page, "เลือกบริการ"):
            results.append({"round": i, "status": "FAIL", "step": "wait_service_page"})
            continue

        time.sleep(STEP_DELAY)

        # ---- BACKWARD: กด กลับ ----
        ok_back = click_back(main_window)
        if not ok_back:
            results.append({"round": i, "status": "FAIL", "step": "click_back"})
            continue

        # รอจนกลับมาหน้าระบุปลายทาง
        if wait_for_page(main_window, is_on_postal_page, "ระบุปลายทาง"):
            log(f"   [/] รอบ {i}: กลับมาหน้าระบุปลายทาง OK")
            results.append({"round": i, "status": "PASS"})
        else:
            log(f"   [!] รอบ {i}: ไม่พบหน้าระบุปลายทางหลังกดกลับ")
            results.append({"round": i, "status": "FAIL", "step": "not_back_on_postal"})

    # ---- SUMMARY ----
    log("\n========== SUMMARY ==========")
    passed  = sum(1 for r in results if r["status"] == "PASS")
    failed  = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    log(f"PASS: {passed} | FAIL: {failed} | SKIP: {skipped} | TOTAL: {repeat}")
    for r in results:
        mark   = "[/]" if r["status"] == "PASS" else "[x]" if r["status"] == "FAIL" else "[-]"
        detail = f" -> {r.get('step', r.get('reason', ''))}" if r["status"] != "PASS" else ""
        log(f"  {mark} รอบ {r['round']}: {r['status']}{detail}")
    log("==============================")

    return passed, failed, skipped


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        log("กำลังเชื่อมต่อกับ Riposte POS Application...")
        app = Application(backend="uia").connect(
            title_re=".*Riposte POS Application.*", timeout=10
        )
        main_window = app.top_window()
        log("เชื่อมต่อสำเร็จ")

        # หมายเหตุ: navigate ไปที่หน้า "ระบุปลายทาง" ก่อนรัน script นี้
        passed, failed, _ = run_back_forth_test(main_window, repeat=REPEAT_COUNT)

        if failed == 0:
            log("RESULT: ALL PASSED")
        else:
            log(f"RESULT: {failed} FAILED")

    except Exception as e:
        log(f"[CRITICAL] {e}")
        raise
