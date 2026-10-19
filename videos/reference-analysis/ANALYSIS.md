# Reference analysis: stick-figure fight (19.25 s screen recording)

Source: user-supplied screen recording (1288x708, HEVC, 59.94 fps container). Contact sheets of every beat are in `strips/`.

## Format and timing
- Animated at **24 fps, one new drawing per frame ("on ones")**. The 60 fps container repeats frames in a 2-3-2-3 pattern (186 runs of 2 frames, 185 of 3).
- 386 unique drawings in 19.25 s (about 20 per second on average because of early holds).
- **Holds (whole screen frozen) only occur in the first ~4.6 s** (0.27-0.58 s each, 7 of them: idle/setup poses). From 4.6 s on, nothing holds longer than ~0.12 s. There is **no hit-stop / freeze frame on impacts**; the fight never pauses.
- No dialogue-style pacing: beats are chained, with one continuous action flowing into the next.

## Character design
- Flat 2D side view, round-capped strokes, no outline, no shading, no background, no shadow, one thin flat ground line (about 80% down the frame, ~1% frame height thick).
- Figure height about 37% of frame height at normal framing (265 px of 708).
- **Head diameter is about 20% of figure height** (large round head). **Limb stroke is about 6% of figure height**, roughly 1/3.3 of the head diameter.
- Colors: red body #8d0f02 (dark red), blue body #7379ae (muted periwinkle), white background, near-black ground line.
- Limbs are two-segment (thigh/shin, upper arm/forearm) with visible bends; hands and feet are just line ends, no mitts.

## Motion vocabulary seen (all hand-to-hand, no weapons)
1. Rise from lying/sitting to standing (blue), then a walk-in. Red holds a leaning pose (idle).
2. In-place run/ready cycle, then **anticipation crouch** into a **low dive-tackle** that slides into the opponent.
3. Grapple / clinch (bodies overlap), knee strike, high kick, backflip with long hang time.
4. Sprint exchanges with very forward lean (30-45 degrees), low wide fighting stance with raised fists.
5. Takedown to the ground, crawl, ground stomp, spinning kick with a big arc, final stand-up and walk-off.

## Easing and spacing (measured)
- **Dive:** 4 near-still drawings of anticipation (speed 0.2 to 2 px/drawing) then an explosive ramp: 8, 19, 23, 29, 33, **42** px per drawing over 6 drawings (about 0.25 s), then slight slow at contact (17) and a second burst (30). That is an **ease-in launch (accelerate through the move), not a smooth ease-in-out**. Peak speed is about 0.39 body-heights per drawing.
- **Backflip:** 2 drawings of crouch, then a **pop with no ease-in**: head moves 52, 46, 43 px per drawing upward (about 0.4-0.5 body-heights each), then a **hang at the apex for about 0.5 s (12 drawings) with only +-12 px jitter** while the body tumbles. Rise is fast and linear, the apex is floaty.
- **Squash and stretch:** the body bounding box stretches to about 1.5x height on the launch drawing (168 px vs 112 px normal), and crumples to about 0.55x (64 px) when tucked.
- Poses change a lot between drawings on fast actions (big angular jumps), so fast moves rely on a few strong drawings plus smear, not on smooth in-betweens.

## Effects
- **Ghost trails:** 2-3 translucent copies of the previous pose lagging 1-2 drawings, on tackles, kicks and flips (around 5.1-5.2 s, 6.9-7.0 s, 11.4 s, 12.6 s, 14.1 s).
- **Swoosh arcs:** a thin colored crescent following a swinging limb, fading over about 3 drawings (kicks and punches, around 7.6 s, 9.0-9.2 s, 10.3 s).
- **Impact burst (once, at 17.18 s):** about 8 short thin radiating dashes plus a soft radial glow disc, lasting about 2 drawings (about 0.08 s).
- **Speed lines:** dense parallel horizontal streaks across the whole frame (14.5-16.1 s), one set tilted; used for sprint/dash moments.
- **Giant arc swoosh** near camera on a spinning kick (17.7 s).

## Camera
- Mostly locked side view, but the framing shifts: the ground line moves vertically by about 28 px (8% of frame height) and figure scale changes about 20%, so there are slow push-ins and cuts/pans (position jumps at 7.9 s and 8.6 s).
- No shake observed.

## Caveats
- Measurements were taken from video frames with color segmentation; bounding boxes are noisy when the two figures overlap.
- The reference has no weapons, so katana and spear movement, arcs and trails are an extrapolation of this style, not measured.
