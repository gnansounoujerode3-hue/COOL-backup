import {Composition} from 'remotion';
import {BrandCard, brandCardSchema} from './BrandCard';

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="BrandCard"
        component={BrandCard}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1920}
        schema={brandCardSchema}
        defaultProps={{
          variant: 'title' as const,
          headline: 'Title goes here',
          subhead: 'Subhead goes here',
          colors_primary: '#40DCE0',
          colors_secondary: '#FCA529',
          colors_text: '#0A0A0A',
          colors_bg: '#0A0A0A',
          font_headline: 'Outfit',
        }}
      />
    </>
  );
};
