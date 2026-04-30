"""
Sleep Optimizer — AI Room Analysis
=====================================
Handles Gemini AI room-environment checks and syncs results to Blynk.
Updated for Temperature, Sound (0-100), Light (0-255), and Dust (mg/m³).
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
        Analyze current sensor data with Gemini AI.
        data: {"temperature": float, "sound": float, "light": int, "dust": float}
        """
        # Call the updated gemini_sleep logic
        result = gemini_sleep.room_check(data)
        if not result:
            print("[AI ADVICE] Gemini returned no result.")
            return None

        try:
            # 1. Update Sleep Score (V8) and Advice Text (V9)
            blynk_client.update_pin(blynk_client.PINS['sleep_score'], result['score'])
            blynk_client.update_pin(blynk_client.PINS['ai_advice'],   result['advice'])

            # 2. Dynamic Score Gauge Coloring
            score = result.get('score', 0)
            color = "#4CAF50" if score >= 80 else "#FF9800" if score >= 50 else "#F44336"
            blynk_client.update_property(blynk_client.PINS['sleep_score'], "color", color)

            # 3. Dynamic Sleep Status Banner (V11)
            # Matching the status pin used in your recent Blynk mapping
            if score >= 80:
                status = "🌙 Good Sleep Quality"
            elif score >= 50:
                status = "⚠️ Fair Sleep Conditions"
            else:
                status = "🔴 Poor Sleep Conditions"
            blynk_client.update_pin(blynk_client.PINS['sleep_status'], status)

        except Exception as e:
            print(f"[AI ADVICE] Blynk update failed: {e}")

        return result

    # ── Background task ───────────────────────────────────────────
    async def poll_trigger(self, get_latest_data_fn):
        """
        Background task: poll V16 button. When pressed (1), reset it
        and generate a report using the latest 4-sensor data.
        """
        def _poll_and_run():
            val = blynk_client.get_pin(blynk_client.PINS['room_check_trigger'])
            # Support both string and int responses from Blynk API
            if val is not None and int(float(val)) == 1:
                print("[AI ADVICE] Room Check Trigger (V16) detected.")
                
                # Reset pin immediately to allow for subsequent triggers
                blynk_client.update_pin(blynk_client.PINS['room_check_trigger'], 0)
                
                data = get_latest_data_fn()
                if not data:
                    print("[AI ADVICE] Data buffer empty — skipping check.")
                    return
                
                self.run(data)

        while True:
            try:
                # Use to_thread to keep the asyncio loop unblocked during HTTP calls
                await asyncio.to_thread(_poll_and_run)
            except Exception as e:
                print(f"[AI ADVICE ERROR] {e}")

            await asyncio.sleep(self.POLL_INTERVAL)