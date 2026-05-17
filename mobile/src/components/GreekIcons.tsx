import React from 'react';
import Svg, { Path, Circle, G } from 'react-native-svg';

interface IconProps {
  size?: number;
  color?: string;
}

export const HermesIcon: React.FC<IconProps> = ({ size = 28, color = '#0D2538' }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M12 3L12 21" />
    <Path d="M12 4C10.5 4 9 4.5 9 5.5C9 6.5 10.5 6 12 6C13.5 6 15 6.5 15 5.5C15 4.5 13.5 4 12 4" />
    <Path d="M9 5.5C9 5.5 7 5 6 4C7 6.5 8 6.5 9 5.5Z" />
    <Path d="M15 5.5C15 5.5 17 5 18 4C17 6.5 16 6.5 15 5.5Z" />
    <Path d="M12 7C10 7 9 9 10 10C11 11 12 10 12 10C12 10 13 11 14 10C15 9 14 7 12 7Z" />
    <Path d="M10 10C10 10 10 13 12 13C14 13 14 10 14 10" />
    <Path d="M9 21L12 19L15 21" />
  </Svg>
);

export const AthenaIcon: React.FC<IconProps> = ({ size = 28, color = '#0D2538' }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M12 2C12 2 9 3 9 5L9 6C9 6 7 6.5 7 8C7 9 8 9 8 9C8 9 7 12 7 14C7 17 9 19 12 19C15 19 17 17 17 14C17 12 16 9 16 9C16 9 17 9 17 8C17 6.5 15 6 15 6L15 5C15 3 12 2 12 2Z" />
    <Circle cx={10} cy={8.5} r={1} fill={color} stroke="none" />
    <Circle cx={14} cy={8.5} r={1} fill={color} stroke="none" />
    <Path d="M10 13C10 13 11 14 12 14C13 14 14 13 14 13" />
    <Path d="M7 14C5 14 4 16 5 17C6 18 7 17 7 17" />
    <Path d="M17 14C19 14 20 16 19 17C18 18 17 17 17 17" />
    <Path d="M8 5C6 4.5 5 5 4 6C4.5 6.5 5.5 7 7 6.5" />
    <Path d="M16 5C18 4.5 19 5 20 6C19.5 6.5 18.5 7 17 6.5" />
  </Svg>
);

export const ApolloIcon: React.FC<IconProps> = ({ size = 28, color = '#0D2538' }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
    <Path d="M7 20C7 20 7 8 7 6C7 4 9 2 12 2C15 2 17 4 17 6C17 8 17 20 17 20" />
    <Path d="M7 20C7 20 6 21 7 21C8 21 8 20 8 20" />
    <Path d="M17 20C17 20 16 21 17 21C18 21 17 20 17 20" />
    <Path d="M9 8L15 8" />
    <Path d="M9 11L15 11" />
    <Path d="M9 14L15 14" />
    <Path d="M9 17L15 17" />
    <Path d="M7 6C6 5.5 5 6 5 7C6 7 6.5 6.5 7 6" />
    <Path d="M17 6C18 5.5 19 6 19 7C18 7 17.5 6.5 17 6" />
  </Svg>
);
