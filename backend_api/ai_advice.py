"""
Sleep Optimizer — AI Room Analysis
=====================================
Handles Gemini AI room-environment checks and syncs results to Blynk.
Extracted from main.py for cleaner separation of concerns.
"""

import asyncio
import blynk_client
import gemini_sleep


class AIAdvice:
    """
    Runs a Gemini room-environment analysis on the latest sensor reading
    and pushes the score + advice to Blynk (V8 / V9).
    """

    POLL_INTERVAL = 5  # Seconds between V16 checks

    def run(self, data: dict) -> dict | None:
        """
        Analyse sensor data with Gemini AI.

        Args:
            data: Sensor dict (temperature, humidity, co2, …)

        Returns:
            {"score": int, "advice": str}  or  None on failure
        """
        result = gemini_sleep.room_check(data)
        if not result:
            print("[AI ADVICE] Gemini returned no result.")
            return None

        try:
            blynk_client.update_pin(blynk_client.PINS['sleep_score'], result['score'])
            blynk_client.update_pin(blynk_client.PINS['ai_advice'],   result['advice'])

            # Colour the score gauge: green / amber / red
            score = result.get('score', 0)
            color = "#4CAF50" if score >= 80 else "#FF9800" if score >= 50 else "#F44336"
            blynk_client.update_property(blynk_client.PINS['sleep_score'], "color", color)

        except Exception as e:
            print(f"[AI ADVICE] Blynk update failed: {e}")

        return result

    # ── Background task ───────────────────────────────────────────
    async def poll_trigger(self, get_latest_data_fn):
        """
        Background task: poll V16 every POLL_INTERVAL seconds.
        When the button is pressed (value == 1), reset it and
        generate a room check report using the latest data.

        Args:
            get_latest_data_fn: Zero-arg callable that returns the latest sensor data.
        """
        def _poll_and_run():
            val = blynk_client.get_pin(blynk_client.PINS['room_check_trigger'])
            if val is not None and int(float(val)) == 1:
                print("[AI ADVICE] Room Check Button pressed — generating…")
                # Reset pin immediately so a second press works
                blynk_client.update_pin(blynk_client.PINS['room_check_trigger'], 0)
                self.run(get_latest_data_fn())

        while True:
            try:
                await asyncio.to_thread(_poll_and_run)
            except Exception as e:
                print(f"[AI ADVICE ERROR] {e}")

            await asyncio.sleep(self.POLL_INTERVAL)
