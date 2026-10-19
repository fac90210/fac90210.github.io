# Full reference analysis (every drawing)

Method: every unique drawing (386 of them, from a 19.25 s / 1154-frame screen recording) was viewed in contact sheets (`sheets/`), then a 12-parameter skeleton (hip position, scale, torso angle, two 2-bone legs, two 2-bone arms, head disc) was fitted to the red and blue silhouettes of every drawing by matching pixels (`code/`, `motion_data.json`). Fit quality: 385 red + 345 blue figure-frames fitted, median mismatch 0.27 (fraction of silhouette), 93% below 0.5. `tracking_check.mp4` shows original and fitted skeleton side by side. Limb joint angles are approximate (they flip when a limb is hidden or straight); head, hip, torso, hand and foot positions are the reliable signals.

## 1. Format
- 24 drawings per second in action (2-3-2-3 frame pattern inside a 60 fps recording); 386 unique drawings.
- Pose holds are common in the first ~4.7 s and again in a few later spots. Red holds one lean pose for d9-d42 (0.6 s to 3.5 s) while blue stands up and walks. Blue holds a ready stance d35-d48 (0.9 s) and d54-d63 (0.9 s) while red moves. Only one figure is animated at a time in the opening; from d60 on both are animated every drawing.
- Later holds are short and exact: blue/red stand-off d102-d109 (8 drawings, 0.3 s), blue kneel d275-d284 (10 drawings), clinch d259-d266 (8 drawings), prone/crouch pair d340-d352 (13 drawings, tiny jitter), overlapped pile d361-d368 (8 drawings, 0.3 s). No hit-stop freezes at the moment of contact; the holds come after the hit.

## 2. Character design (measured)
- Head disc radius is 8.5% of the figure scale s (head diameter about 20% of standing height). Stroke width 7.3% of s. Bones as fraction of s: torso 0.19, thigh 0.21, shin 0.22, upper arm 0.14, forearm 0.22, neck gap 0.045. Arms are long (forearm longer than upper arm), legs are about 44% of s.
- Colors: red #8d0f02, blue #7379ae, white background, near-black ground line (about 7 px thick at 1288 px width).

## 3. Camera (measured from figure scale)
- Figure scale varies from 0.54x to 1.56x of the opening (almost 3x range). Hard zoom cuts at d2 (title close-up to wide), d85, d294-295, d304, d326, d332, d370. Everything else is continuous push-ins/pull-outs: tight on clinches (zoom 1.4-1.7 on d68-d93, d159-d169, d190-d192, d355-d368), wide on separate figures (0.6-1.0).
- Sprint (d285-d337, 14.15-16.4 s): a stutter rhythm. Close-up of red running (3-4 drawings, zoom ~1.4-1.6) alternates with 1-3 drawing wide shots (zoom ~0.4-0.6) that carry horizontal speed-line streaks. 8 close/wide switches in 2.7 s. Streak drawings: d285-287, 293-294, 303-305, 310-312, 316-318, 323-325, 327-328, 330-331, 336-337. Streak angle tilts (up on d311-312, down on d293-294, d324).
- Ground line row moves 28 px (8% of frame) over the clip: vertical camera drift follows the action.

## 4. Move catalogue (every beat, drawing numbers)
d0 close-up of blue seated, cut to wide at d1.
d1-d4 (0.27-0.40 s) red drops in from top-left, lands in a crouch (d3 landing, d4 crouch). d5-d9 rises into a leaning pose, then holds d9-d42.
d15-d25 (1.52-1.94 s) blue pushes up: sit, hands push, crouch (d19-21), stand (d22-25). d26-d34 walk steps. d35-d48 ready stance hold.
d43-d48 red steps out of the hold, knee up. d49-d59 (3.77-4.74 s) in-place run/ready bounce cycle (11 drawings).
d60-d64 dive: low crouch (d60-61), launch (d62 moves 0.48 body heights in one drawing), extended slide (d63-64).
d65-d67 reach and grab. d68-d70 impact: red streak crescent, blue ghost copies. d71-d79 blue driven into a low lunge, red bent over, clinch.
d80-d93 (5.61-6.16 s) grapple/throw with blue arm sweep arcs (d80-86) and a huge red crescent smear held two drawings (d92-93).
d94-d101 knee strike / counter kick (blue kick arc d100-101). d102-d109 stand-off hold.
d110-d127 (6.86-7.56 s) blue backflip: crouch (d110), pop (d111, body stretched about 1.5x), inverted spin (d112-114), hang about 13 drawings (0.5 s) while red rises from a low crawl to standing.
d128-d131 red leaps, arm swoosh hits blue (ghost). d132-d134 blue flung right. d135-d144 blue lands kneeling (hold), red spin-kick pose then run.
d145-d149 blue slide with two ghost copies; red leaps. d150-d158 both dash in. d159-d179 (8.89-9.73 s) clash: red hip/knee strike with red crescent swoosh (d163-169), blue tumbles over (airborne d168-176), lands tucked (d177-179); red stands tall.
d180-d187 blue rises, red stands. d186-d192 red leaps, head-on collision (d190-192, zoom 1.6). d193-d199 blue jumps / knees red who crouches. d200-d204 blue giant roundhouse kick with arc trail (smear d200-201), red reels. d205-d214 blue drops to knees and crawls, red stands over.
d215-d239 (11.23-12.23 s) long shove/punch exchange (25 drawings) with arc swooshes (d216-221, 228, 231-233) and red punch streaks (d238). d240-d249 red pushes blue; d248-249 red smear with blue ghost. d250-d258 blue sprints in (streak d257-258). d259-d266 bulldoze/headlock hold.
d267-d284 blue falls to a kneel (10-drawing hold), red steps back to stance.
d285-d302 blue lunge streak, camera snaps to red close-up running in place. d303-d336 stutter-cut sprint (see Camera). d336-d352 blue prone, red crouched sprint pose, near-static 13 drawings.
d353-d360 (16.98-17.27 s) collision and impact burst: d353 reach, d354 smear with ghost copies, d355 red glow disc over the pile (zoom 1.6), d356-d359 about 8 thin radiating dashes expanding and fading over 4 drawings plus fading glow, d360 camera pulls out.
d361-d368 overlapped pile hold. d369-d374 (17.65-17.85 s) giant blue ring/plank swoosh sweeps across screen, fades over 6 drawings. d375-d385 red recovers (knee up), straightens, final standing idle.

## 5. Motion numbers
- End-effector speed per drawing (body heights per drawing): hands median 0.15, 90th percentile 0.48, peak about 1.0-1.2; feet median 0.12, 90th percentile 0.41; hip median 0.09, 90th percentile 0.41, peak 1.2. So fast actions move a hand or foot half a body height or more in a single drawing; most drawings are slow, a few are huge jumps.
- Dive (head travel per drawing, body heights, from head tracking): 0.01, 0.01, 0.08, 0.18, 0.22, 0.27, 0.31, 0.39, then contact (about 4 near-still anticipation drawings, then an 8-drawing acceleration).
- Backflip: crouch 2 drawings, pop upward 0.5, 0.43, 0.40 body heights per drawing for 3 drawings (no ease-in), then about 13 drawings of hang with only small drift.
- Torso lean toward the opponent: median 20 degrees, 95th percentile past 90 (bent-over tackle and clinch poses).
- Effects: ghost/smear copies on d70-71, 79, 111-113, 145-146, 200-201, 220-221, 232, 243, 249, 258, 285-287, 354, 372-375 (blue) and d129-130, 151, 161-163, 168, 354-360, 370 (red); typically 1-3 drawings long with 2 lagging copies. One radial impact burst at d355-d360.

## 6. What this changes for the stick-fight rebuild
- Use limited-animation structure: hold poses while the other figure acts early; then constant motion.
- Stutter-cut camera on the sprint/dash moments, with wide streak shots; zoom in tight on clinches, wide on separation.
- Larger head, longer forearms, thicker strokes than my first draft.
- Hold after contact (8-10 drawings of the pile / kneel) instead of freezing at contact.
- The burst expands over 4 drawings after the overlap, and the camera pulls out one drawing later.
- Retarget the fitted data (`motion_data.json`) for locomotion and body mechanics, add the weapons in the hands.
