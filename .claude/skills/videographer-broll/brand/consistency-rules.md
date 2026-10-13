# Multi-Clip Character + Product Consistency Rules

Canonical source for the orchestrator and every adapter that can produce more than one clip. When a request spans multiple independent generations - a Brand Story arc, a Fashion Lookbook reel, a Product 360 multi-angle set, a chained avatar series, ANY "Act 1 / Act 2 / Act 3" structure - read this doc and apply the rules.

## Why this exists

The AI video models we use (Seedance 2.0, Kling, Veo, HeyGen, Hedra, Sora) have **NO memory between independent prompt submissions**. Every detail you do not byte-repeat across clips will drift:

- The founder's shirt color shifts between Act 1 and Act 3.
- The fashion model in shot 1 silently becomes a different person by shot 4.
- The bottle label gains a glyph it didn't have, the watch dial gains hands, the sneaker color shifts shade.
- Your avatar's hair length flips half-way through a 4-clip course delivery.

Naive prompts produce inconsistent multi-clip outputs. The fix is the 3 rules below.

## The 3 rules

Source: Million Dollar Group Method, Lesson 13 - "Generating Content with AI". Originally written for VEO3 (kmboards Education Hub, course_content slug `veo3-quick-start`, migration 276). The rules apply to any frame-independent video model.

1. **EXACT same clothing in every clip prompt.** Not "blue jeans" - "torn light-wash blue jeans with a small bleach stain near the right knee." Repeat the same string verbatim in every clip's character description.
2. **EXACT same items.** Not "Yeti cooler" - "beige 35-quart Yeti Tundra cooler with a black handle and a small dent on the lid." Same string every clip.
3. **Only change: setting description, background characters, script line, time of day, lighting recipe.** Anything else stays byte-identical.

## The Lock-Block pattern (how to apply the rules)

Before writing any of the multi-clip prompts, draft a **Lock Block** ONCE. The Lock Block is ~50-100 words pinning every visual detail of the recurring subject. Different surfaces need different locks:

- **Character Lock** (Brand Story, founder portraits, customer testimonials): hair (texture, length, color), eyes, age range, ethnicity / skin tone (Fitzpatrick or named color), build, every garment with material + color + fit + state of wear, accessories, props, anything held.
- **Casting Lock** (Fashion Lookbook, multi-model campaigns): one Lock per model. Includes everything in Character Lock plus signature poses or expressions if relevant. For group shots, every model in the group has their own Lock and all Locks paste in.
- **Product Lock** (Product 360, multi-angle reels): full product description with materials, finish, label details, surface state (scratches, fingerprints, factory-new), markings, hardware. Include every detail that is visible in ANY clip in the lock for EVERY clip - the model needs the off-screen description to render the on-screen part consistent.
- **Scene Lock** (rare, used when location must persist across clips with character changes): every furniture piece, every wall detail, every prop on the desk. Less common - usually settings change deliberately between clips.

**Then paste the Lock Block verbatim into the SUBJECT line of every clip prompt that features that subject.** Do not paraphrase between clips. Do not summarize as "the founder from Act 1" or "the same model as before" - the model cannot resolve the back-reference.

> ### 🚨 If the tool accepts a reference IMAGE, use that instead - it is far stronger
>
> The Lock Block is a workaround for models that take text only. **Verified 2026-08-10 on Gemini Omni:** prose alone (identical room description, no reference image) produced *a different man in a different room*. Passing a single reference still instead held face, beard, glasses, build and wardrobe **and the room** across a medium shot and a tight close-up.
>
> So: generate or choose ONE canonical still of the subject, upload it once, and reuse it in every shot. Never describe the face twice. See [`../adapters/gemini-omni.md`](../adapters/gemini-omni.md) Rule 1. Keep the text Lock Block for tools that take no reference image, and as a weak fallback when no still exists.
>
> **Also strip object-in-hand gestures from every multi-clip beat.** Raising, lowering or passing an object reliably spawns a duplicate object mid-gesture, and it cannot be edited out afterwards (Rule 2 in the same adapter).

Across clips, only these change:
- Setting / location
- Background characters (extras, crowds, environment populated differently)
- What the subject is DOING (action verbs)
- Script line / dialogue / VO content
- Time of day
- Lighting recipe (Rembrandt vs Loop vs Split, key direction, color temp)
- Camera move

## Where this applies

| Surface | Lock type | Notes |
|---|---|---|
| `adapters/fal-seedance.md` (Phase D / kmboards) | Character / Casting / Product | The 6 kmboards `video-style-*` skills produce prompts that feed in here. Brand Story (3-4 clips), Fashion Lookbook (multi-shot), Product 360 (multi-angle) most affected. |
| `adapters/heygen.md` | Character (avatar) | Multi-clip avatar series for course delivery. Avatar_id pins the face, but clothing + props + background still drift across separate render calls. |
| `adapters/hedra.md` | Character (avatar) | Same as HeyGen. Even if the source still image is locked, generated b-roll between avatar clips needs the Character Lock. |
| `adapters/cutsense.md`, `video-use.md`, `hyperframes.md` | N/A | These edit existing footage. The footage itself is consistent - drift only happens in NEW generation. |

## Anti-patterns

- Generating multi-clip sequences without a Lock Block. The rules apply even when the user "just wants 3 quick clips."
- Paraphrasing the Lock Block between clips. The model cannot back-reference. Paste verbatim every time.
- Keeping the Lock Block too vague ("a young woman in casual clothes"). The Lock must be specific enough to render the same person twice. If the Lock leaves anything to the model's imagination, that's where drift happens.
- Locking the character but not the props. The cooler / phone / coffee mug / cigarette / dog also drift if not pinned.
- Locking the product but not the lighting around it. Acceptable: the lighting recipe is in the per-clip section. Not acceptable: leaving "soft natural light" implicit when the product's specular highlights depend on it - move that into the Product Lock.

## Reference (kmboards, requires login)

Education Hub entry with the original VEO3 Quick Start Guide:
https://kmboards.co/agents/dashboards/viral-content?tab=education

The kmboards Phase B style skills that bake these rules into their output contracts:
- `video-style-brand-story` (Character Lock section)
- `video-style-fashion-lookbook` (Casting Lock section)
- `video-style-product-360` (Product Lock section)

The orchestrator's videographer assistant (kmboards `video:videographer` agent skill) flags these rules when routing to multi-clip skills and surfaces the Education Hub link as a button.

## When NOT to apply

Single-clip generation (one fal-seedance text-to-video, one HeyGen render with no chained follow-up). The 3 rules are about consistency BETWEEN clips - if there is no "between," the Lock Block adds prompt length without benefit. Skip it for one-shot work.
