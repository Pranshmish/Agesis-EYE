# Stage 04: Laptop Inference & Tracking Rules

## Rules & Constraints
1. **Threaded Latest-Frame Reader**: Capture stream frames in a separate thread. Always run inference on the newest frame buffer to eliminate latency lag.
2. **Confidence Threshold**: Set high confidence threshold (conf >= 0.70) for target identification.
3. **Multi-Frame Target Lock**: Require at least 5 consecutive confirmed frames before signaling target locked (`locked = True`). Never fire on single-frame spikes.
4. **Target Tracking**: Maintain target consistency across frames via ByteTrack or Kalman filtering.
5. **Stream Watchdog**: If stream connection drops or no target is detected for 300 ms, immediately emit `no target` and command laser OFF.
6. **Latency Budget**: Maintain 15+ FPS and sub-150 ms end-to-end latency.
