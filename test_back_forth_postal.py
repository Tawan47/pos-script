"""
Test: กดไปกลับหน้าระบุปลายทาง (กรอกหมายเลขไปรษณีย์) วนซ้ำ
ทดสอบ navigation ระหว่างหน้า "ระบุปลายทาง" <-> หน้า "เลือกบริการ"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Automation-Team'))

import time
import datetime
import threading
from pywinauto.application import Application
from pywinauto import mouse


# ============================================================
# CONFIG
# ============================================================
REPEAT_COUNT  = None        # None = วนไปเรื่อยๆ จนกว่าจะกด Ctrl+C หรือปิด terminal
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


def _scan_descendants(window, kwargs, result, error):
    """รัน descendants() ใน thread แยก เพื่อให้ตรวจจับอาการค้างได้ (UIA call นี้ไม่มี timeout ในตัว)"""
    try:
        result.append(window.descendants(**kwargs))
    except Exception as e:
        error.append(e)


def safe_descendants(window, label, scan_timeout=10, **kwargs):
    """
    เรียก window.descendants() พร้อม timeout + log กันเงียบค้าง
    (UIA call นี้ปกติไม่มี timeout ในตัว ถ้าแอปเป้าหมาย busy/ไม่ตอบสนอง จะค้างตลอดไป)
    คืนค่า list ของ elements หรือ [] ถ้า timeout/error
    """
    result, error = [], []
    scan_thread = threading.Thread(
        target=_scan_descendants, args=(window, kwargs, result, error), daemon=True
    )
    scan_thread.start()
    scan_thread.join(scan_timeout)

    if scan_thread.is_alive():
        log(f"   [!] {label}: window.descendants() ค้างเกิน {scan_timeout}s "
            f"-> แอป Riposte อาจกำลัง busy/ไม่ตอบสนอง (UI thread ไม่ตอบ UIA call)")
        return []

    if error:
        log(f"   [WARN] {label}: descendants() error: {error[0]}")
        return []

    return result[0]


def clear_and_fill(edit, postal_code):
    """ล้าง field แล้วกรอกค่าใหม่ พร้อมตรวจสอบว่ากรอกถูกต้อง"""
    for attempt in range(3):
        try:
            edit.click_input()
            time.sleep(0.2)
            # ล้างด้วยหลายวิธีเพื่อให้แน่ใจว่า field ว่าง
            edit.type_keys("^a", pause=0.1)
            edit.type_keys("{DELETE}", pause=0.1)
            edit.type_keys("^a", pause=0.1)
            edit.type_keys("{BACKSPACE}", pause=0.1)
            time.sleep(0.2)
            # กรอกค่าใหม่ทีละตัว
            edit.type_keys(str(postal_code), with_spaces=True, pause=0.05)
            time.sleep(0.3)
            # ตรวจว่ากรอกถูกต้อง
            current = edit.window_text().strip()
            if current == str(postal_code):
                return True
            log(f"   [WARN] attempt {attempt+1}: got '{current}' expected '{postal_code}' -> retry")
            time.sleep(0.3)
        except Exception as e:
            log(f"   [WARN] clear_and_fill attempt {attempt+1}: {e}")
    return False


def fill_postal_code(window, postal_code):
    """กรอกรหัสไปรษณีย์ในหน้าระบุปลายทาง"""
    try:
        edits = [e for e in safe_descendants(window, "fill_postal_code", control_type="Edit") if e.is_visible()]

        # วิธี 1: หา edit ที่ automation_id หรือ name มีคำว่า PostalCode
        for edit in edits:
            aid  = edit.element_info.automation_id or ""
            name = edit.element_info.name or ""
            if "PostalCode" in aid or "รหัสไปรษณีย์" in name or "Postal" in name:
                if clear_and_fill(edit, postal_code):
                    log(f"   [/] กรอกรหัสไปรษณีย์: {postal_code}")
                    return True
                log(f"   [!] กรอกรหัสไปรษณีย์ไม่สำเร็จหลัง 3 ครั้ง")
                return False

        # วิธี 2: ใช้ edit box แรกที่มองเห็น (fallback)
        if edits:
            if clear_and_fill(edits[0], postal_code):
                log(f"   [/] กรอกรหัสไปรษณีย์: {postal_code} (fallback)")
                return True
            log(f"   [!] กรอกรหัสไปรษณีย์ไม่สำเร็จหลัง 3 ครั้ง (fallback)")
            return False

    except Exception as e:
        log(f"   [WARN] fill_postal_code error: {e}")

    log("   [!] ไม่พบ edit box สำหรับกรอกรหัสไปรษณีย์")
    return False


def find_next_button(window, scan_timeout=10):
    """หาปุ่มถัดไป คืนค่า element หรือ None (ไม่สนใจตำแหน่งบนจอ/ขนาดหน้าจอ)"""
    try:
        log("   [i] find_next_button: เริ่ม scan UI tree (window.descendants())...")
        t0 = time.time()

        children = safe_descendants(window, "find_next_button", scan_timeout=scan_timeout)
        if not children:
            return None

        elapsed = time.time() - t0
        log(f"   [i] find_next_button: scan เสร็จใน {elapsed:.2f}s พบ {len(children)} elements")

        candidates = []
        for child in children:
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
            log(f"   [i] find_next_button: พบปุ่ม 'ถัดไป' ({len(candidates)} candidate) "
                f"enabled={candidates[-1].is_enabled()}")
            return candidates[-1]
        else:
            log("   [!] find_next_button: ไม่พบปุ่ม 'ถัดไป' ใน UI tree (อาจยังไม่ขึ้น/ชื่อไม่ตรง)")
    except Exception as e:
        log(f"   [WARN] find_next_button error: {e}")
    return None


def click_next(window, enable_timeout=5, enable_poll=0.3):
    """
    กดปุ่มถัดไป โดยไม่ขึ้นกับตำแหน่ง/ขนาดหน้าจอ:
    - รอจนปุ่ม enabled (เผื่อแอปยังไม่อัปเดต state จากการกรอกเลข)
    - ใช้ invoke() ของ UIA เป็นหลัก (ทำงานได้แม้ปุ่มจะอยู่นอกพื้นที่มองเห็นบนจอเล็ก)
    - ถ้า invoke ไม่ได้ ค่อย fallback ไปที่ click_input()
    """
    button = find_next_button(window)

    if button is not None:
        # รอให้ปุ่ม enabled ก่อนกด เผื่อ validation ของแอปยังไม่ทัน
        deadline = time.time() + enable_timeout
        while time.time() < deadline:
            try:
                if button.is_enabled():
                    break
            except Exception:
                break
            time.sleep(enable_poll)
        else:
            log("   [WARN] ปุ่ม 'ถัดไป' ยัง disabled อยู่หลังรอ -> จะลองกดต่อไป")

        try:
            button.invoke()
            log("   [/] กดปุ่ม 'ถัดไป' (invoke)")
            return True
        except Exception as e:
            log(f"   [WARN] invoke ไม่สำเร็จ: {e} -> ลอง click_input")
            try:
                button.click_input()
                log("   [/] กดปุ่ม 'ถัดไป' (click_input)")
                return True
            except Exception as e2:
                log(f"   [WARN] click_input ก็ไม่สำเร็จ: {e2}")

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
        for child in safe_descendants(window, "click_back"):
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
        for child in safe_descendants(window, "is_on_postal_page"):
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
        for child in safe_descendants(window, "is_on_service_page"):
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
    กดไปกลับหน้าระบุปลายทาง <-> เลือกบริการ
    repeat=None = วนไปเรื่อยๆ จนกว่าจะกด Ctrl+C
    """
    label = f"{repeat} รอบ" if repeat is not None else "ไม่จำกัดรอบ (กด Ctrl+C เพื่อหยุด)"
    log(f"=== START: test_back_forth_postal | {label} ===")
    results = []
    i = 0

    while True:
        i += 1
        if repeat is not None and i > repeat:
            break
        round_label = f"{i}/{repeat}" if repeat is not None else f"{i}"
        log(f"\n--- รอบที่ {round_label} ---")

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

        # รอจนหน้าเลือกบริการโหลดเสร็จ
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
    passed  = sum(1 for r in results if r["status"] == "PASS")
    failed  = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    log("\n========== SUMMARY ==========")
    log(f"PASS: {passed} | FAIL: {failed} | SKIP: {skipped} | TOTAL: {i}")
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
