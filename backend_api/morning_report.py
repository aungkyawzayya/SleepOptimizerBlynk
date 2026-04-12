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
                print("[MORNING REPORT] Button pressed — generating…")
                # Reset pin immediately so a second press works
                blynk_client.update_pin(blynk_client.PINS['morning_trigger'], 0)
                self.generate(get_history_fn())

        while True:
            try:
                await asyncio.to_thread(_poll_and_gen)
            except Exception as e:
                print(f"[MORNING REPORT ERROR] {e}")

            await asyncio.sleep(self.POLL_INTERVAL)
