import threading
import time
from database import (get_monitored_accounts, save_alert, 
                      update_monitored_score, init_monitoring)

init_monitoring()

def check_account(username, platform, analyze_instagram, analyze_x):
    """Check a single account for changes"""
    try:
        if platform == "instagram":
            result, error = analyze_instagram(username)
        else:
            result, error = analyze_x(username)

        if error or not result:
            return None

        return result
    except Exception as e:
        print(f"Error checking {username}: {e}")
        return None

def run_monitoring_cycle(analyze_instagram, analyze_x):
    """Check all monitored accounts"""
    accounts = get_monitored_accounts()
    print(f"\n🔍 Monitoring cycle: checking {len(accounts)} accounts...")

    for account in accounts:
        username = account["username"]
        platform = account["platform"]
        last_score = account["last_risk_score"] or 0

        print(f"Checking @{username}...")
        result = check_account(username, platform, analyze_instagram, analyze_x)

        if not result:
            continue

        new_score = result.get("risk_score", 0)
        update_monitored_score(username, new_score)

        # Check for significant changes
        score_change = new_score - last_score

        if last_score > 0:  # skip first check
            if score_change >= 20:
                message = f"Risk score increased by {score_change} points ({last_score} → {new_score})"
                save_alert(username, platform, "risk_increase", message, last_score, new_score)
                print(f"🚨 ALERT: @{username} - {message}")

            elif new_score >= 75 and last_score < 75:
                message = f"Account crossed HIGH RISK threshold ({new_score}/100)"
                save_alert(username, platform, "high_risk", message, last_score, new_score)
                print(f"🚨 ALERT: @{username} - {message}")

            elif result.get("clone", {}).get("is_clone"):
                message = "Clone profile signals detected!"
                save_alert(username, platform, "clone_detected", message, last_score, new_score)
                print(f"🚨 ALERT: @{username} - {message}")

            elif result.get("spam", {}).get("spam_score", 0) >= 60:
                message = f"High spam score detected ({result['spam']['spam_score']}/100)"
                save_alert(username, platform, "spam_detected", message, last_score, new_score)
                print(f"🚨 ALERT: @{username} - {message}")
        else:
            print(f"✅ @{username} baseline set: risk score {new_score}")

        time.sleep(2)  # small delay between checks

def start_monitoring(analyze_instagram, analyze_x, interval_minutes=30):
    """Start background monitoring thread"""
    def monitoring_loop():
        while True:
            try:
                run_monitoring_cycle(analyze_instagram, analyze_x)
            except Exception as e:
                print(f"Monitoring error: {e}")
            print(f"⏰ Next check in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=monitoring_loop, daemon=True)
    thread.start()
    print(f"✅ Monitoring started! Checking every {interval_minutes} minutes")
    return thread