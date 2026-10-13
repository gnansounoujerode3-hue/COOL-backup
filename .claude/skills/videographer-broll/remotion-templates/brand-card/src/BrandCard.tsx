import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'remotion/zod';

export const brandCardSchema = z.object({
  variant: z.enum(['title', 'lower_third', 'outro_cta']),
  headline: z.string(),
  subhead: z.string(),
  colors_primary: z.string(),
  colors_secondary: z.string(),
  colors_text: z.string(),
  colors_bg: z.string(),
  font_headline: z.string(),
});

type Props = z.infer<typeof brandCardSchema>;

export const BrandCard: React.FC<Props> = ({
  variant,
  headline,
  subhead,
  colors_primary,
  colors_secondary,
  colors_text,
  colors_bg,
  font_headline,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();

  const enter = spring({frame, fps, config: {damping: 200, stiffness: 80}});
  const exit = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {extrapolateRight: 'clamp'});
  const opacity = enter * exit;
  const translateY = interpolate(enter, [0, 1], [40, 0]);

  const isLowerThird = variant === 'lower_third';
  const isOutro = variant === 'outro_cta';

  return (
    <AbsoluteFill style={{backgroundColor: colors_bg, fontFamily: font_headline}}>
      {!isLowerThird && (
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: '0 80px', opacity, transform: `translateY(${translateY}px)`}}>
          <div
            style={{
              backgroundColor: colors_primary,
              color: colors_text,
              padding: '24px 48px',
              borderRadius: 999,
              fontSize: 96,
              fontWeight: 800,
              letterSpacing: '-0.02em',
              marginBottom: 32,
              maxWidth: '90%',
              textAlign: 'center',
              lineHeight: 1.05,
            }}
          >
            {headline}
          </div>
          {subhead && (
            <div
              style={{
                backgroundColor: colors_secondary,
                color: colors_text,
                padding: '16px 36px',
                borderRadius: 999,
                fontSize: 56,
                fontWeight: 700,
                letterSpacing: '-0.01em',
                maxWidth: '85%',
                textAlign: 'center',
              }}
            >
              {isOutro ? subhead : subhead}
            </div>
          )}
        </AbsoluteFill>
      )}

      {isLowerThird && (
        <AbsoluteFill style={{justifyContent: 'flex-end', padding: '0 80px 200px', opacity, transform: `translateX(${interpolate(enter, [0, 1], [-100, 0])}px)`}}>
          <div
            style={{
              backgroundColor: colors_primary,
              color: colors_text,
              padding: '20px 40px',
              borderRadius: 999,
              fontSize: 64,
              fontWeight: 700,
              alignSelf: 'flex-start',
              marginBottom: 12,
            }}
          >
            {headline}
          </div>
          {subhead && (
            <div
              style={{
                backgroundColor: colors_secondary,
                color: colors_text,
                padding: '14px 32px',
                borderRadius: 999,
                fontSize: 40,
                fontWeight: 600,
                alignSelf: 'flex-start',
              }}
            >
              {subhead}
            </div>
          )}
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
