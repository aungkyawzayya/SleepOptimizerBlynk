"""
Sleep Optimizer — Morning Report
===================================
Generates a nightly sleep summary via Gemini AI and handles
the V14 button-trigger background polling task.
Extracted from main.py for cleaner separation of concerns.
"""

import asyncio
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

    # ── Core generation ───────────────────────────────────────────
    def generate(self, history: list) -> dict | None:
        """
        Generate a morning report from overnight sensor history.

        Args:
            history: List of sensor dicts (with 'timestamp' key each)

        Returns:
            {"score": int, "summary": str, "tips": str}  or  None
        """
        if len(history) < self.MIN_READINGS:
            blynk_client.update_pin(
                blynk_client.PINS['morning_rpt'],
                "Not enough data yet — keep monitoring!"
            )
            print(f"[MORNING REPORT] Only {len(history)} readings — need {self.MIN_READINGS}.")
            return None

        result = gemini_sleep.morning_report(history)
        if not result:
            print("[MORNING REPORT] Gemini returned no result.")
            return None

        msg = f"Score: {result['score']} | {result['summary']}"
        blynk_client.update_pin(blynk_client.PINS['morning_rpt'], msg)
        print("[MORNING REPORT] Sent to Blynk V10.")
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
        while True:
            try:
                val = blynk_client.get_pin(blynk_client.PINS['morning_trigger'])
                if val is not None and int(float(val)) == 1:
                    print("[MORNING REPORT] Button pressed — generating…")
                    # Reset pin immediately so a second press works
                    blynk_client.update_pin(blynk_client.PINS['morning_trigger'], 0)
                    self.generate(get_history_fn())
            except Exception as e:
                print(f"[MORNING REPORT ERROR] {e}")

            await asyncio.sleep(self.POLL_INTERVAL)
