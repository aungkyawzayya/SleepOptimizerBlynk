"""
Sleep Optimizer — Morning Report
===================================
Generates a nightly sleep summary via Gemini AI and handles
the V14 button-trigger background polling task.
Extracted from main.py for cleaner separation of concerns.

Updates:
- Added flexible `_filter_sleep_window` to handle both overnight 
  production testing (23-6) and daytime demo testing (13-20).
"""

import asyncio
from datetime import datetime
import blynk_client
import gemini_sleep


class MorningReport:
    """
    Generates nightly sleep summaries from sensor history and
    polls the Blynk V14 button so the user can trigger a report
    on demand from the dashboard.
    """

    MIN_READINGS = 5   # Minimum history entries before a report can be generated
    POLL_INTERVAL = 5  # Seconds between V14 checks

    # ==========================================================
    # ⚠️ TESTING VARIABLES FOR LISA ⚠️
    # Change these hours based on when you want to collect data!
    # Daytime Test (Today): START = 13, END = 20
    # Final Presentation (Real Night): START = 23, END = 6
    # ==========================================================
    TARGET_START_HOUR = 13
    TARGET_END_HOUR = 20

    def _filter_sleep_window(self, history: list, start_hour: int, end_hour: int) -> list:
        """
        Filters the sensor history to only include readings taken during the target window.
        Automatically handles both overnight crossing (23-6) and same-day (13-20).
        """
        filtered_data = []
        for reading in history:
            try:
                # Grab the timestamp. 
                dt = reading.get('timestamp')
                
                # If it's a string, convert it to a datetime object.
                if isinstance(dt, str):
                    # Fallback parsing just in case it is saved as ISO format
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00')) 
                
                # If there's no valid datetime object, skip this reading
                if not isinstance(dt, datetime):
                    continue

                hour = dt.hour
                
                # Logic for crossing midnight (e.g., 23:00 to 06:00)
                if start_hour > end_hour:
                    if hour >= start_hour or hour < end_hour:
                        filtered_data.append(reading)
                # Logic for same-day daytime testing (e.g., 13:00 to 20:00)
                else:
                    if start_hour <= hour <= end_hour:
                        filtered_data.append(reading)
                        
            except Exception as e:
                print(f"[FILTER ERROR] Skipping reading due to timestamp error: {e}")
                
        return filtered_data


    # ── Core generation ───────────────────────────────────────────
    def generate(self, history: list) -> dict | None:
        """
        Generate a morning report from overnight sensor history.

        Args:
            history: List of sensor dicts (with 'timestamp' key each)

        Returns:
            {"score": int, "summary": str, "tips": str}  or  None
        """
        
        # --- Apply the Flexible Time Filter ---
        night_history = self._filter_sleep_window(
            history, 
            start_hour=self.TARGET_START_HOUR, 
            end_hour=self.TARGET_END_HOUR
        )
        
        if len(night_history) < self.MIN_READINGS:
            blynk_client.update_pin(
                blynk_client.PINS['morning_rpt'],
                f"Not enough data between {self.TARGET_START_HOUR}:00 and {self.TARGET_END_HOUR}:00!"
            )
            print(f"[MORNING REPORT] Only {len(night_history)} valid readings in window — need {self.MIN_READINGS}.")
            return None

        # Pass ONLY the filtered data to the AI calculation
        result = gemini_sleep.morning_report(night_history)
        
        if not result:
            print("[MORNING REPORT] Gemini returned no result.")
            return None

        score   = result.get('score', 0)
        summary = result.get('summary', '')[:255]
        tips    = result.get('tips', '')[:255]

        # V10 — short score header
        blynk_client.update_pin(blynk_client.PINS['morning_rpt'], f"🌙 Sleep Score: {score}/100")
        # V18 — summary paragraph
        blynk_client.update_pin(blynk_client.PINS['morning_summary'], summary)
        # V19 — tips paragraph
        blynk_client.update_pin(blynk_client.PINS['morning_tips'], tips)
        print(f"[MORNING REPORT] Sent score={score}, summary={len(summary)}ch, tips={len(tips)}ch to Blynk.")
        return result

    # ── Background task ───────────────────────────────────────────
    async def poll_trigger(self, get_history_fn):
        """
        Background task: poll V14 every POLL_INTERVAL seconds.
        When the button is pressed (value == 1), reset it and
        generate a morning report using the latest history.

        Args:
            get_history_fn: Zero-arg callable that returns the current
                            history list (e.g. lambda: list(sensors.history))
        """
        def _poll_and_gen():
            val = blynk_client.get_pin(blynk_client.PINS['morning_trigger'])
            if val is not None and int(float(val)) == 1:
                print(f"[MORNING REPORT] Button pressed — generating report for {self.TARGET_START_HOUR}:00 - {self.TARGET_END_HOUR}:00...")
                # Reset pin immediately so a second press works
                blynk_client.update_pin(blynk_client.PINS['morning_trigger'], 0)
                self.generate(get_history_fn())

        while True:
            try:
                await asyncio.to_thread(_poll_and_gen)
            except Exception as e:
                print(f"[MORNING REPORT ERROR] {e}")

            await asyncio.sleep(self.POLL_INTERVAL)