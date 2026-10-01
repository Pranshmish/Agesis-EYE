# Stage 02: Dataset Collection & Labeling Rules

## Rules & Constraints
1. **Low Frame Rate Extraction**: Extract frames at 1-2 fps (step ~ 0.7s). Consecutive frames are near-duplicates that cause model overfitting.
2. **Target Dataset Balance**: 500+ labeled positive images minimum, plus 15-25% hard negative images (scenes without balloons, empty label files).
3. **Session-Based Splits**: Split strictly BY RECORDED SESSION into `train`, `val`, and `test` splits. Never split randomly across individual frames.
4. **Single Class Definition**: Only class `0: balloon`.
5. **Annotation Standards**:
   - Draw tight bounding boxes around visible balloon bodies only (exclude strings).
   - Label partially visible balloons if >= 20% visible.
   - Manually spot-check 10% of labels before proceeding to training.
6. **Hard Negative Mining**: After initial model evaluation, collect error cases (missed detections, false positives), label them, and add them to training.
