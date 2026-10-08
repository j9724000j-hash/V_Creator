import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import theme from '../../brand/theme.json';
export const palette = {ink:theme.background, paper:theme.foreground, accent:theme.accent};
export const LowerThird: React.FC<{label:string}> = ({label}) => <div style={{position:'absolute',bottom:'12%',left:'8.5%',borderLeft:`4px solid ${palette.accent}`,padding:'12px 20px',color:palette.paper,fontSize:32}}>{label}</div>;
export const Caption: React.FC<{text:string}> = ({text}) => <div style={{position:'absolute',bottom:'5%',left:'10%',width:'80%',textAlign:'center',color:'white',fontSize:36,textShadow:'0 2px 6px black'}}>{text}</div>;
export const Progress: React.FC = () => {
  const f=useCurrentFrame(); const {durationInFrames}=useVideoConfig();
  return <div style={{position:'absolute',bottom:0,height:4,width:`${100*f/Math.max(1,durationInFrames-1)}%`,background:palette.accent}}/>;
};
export const StatCard: React.FC<{value:string;label:string}> = ({value,label}) => {
  const f=useCurrentFrame();
  return <div style={{padding:40,color:palette.paper,opacity:interpolate(f,[0,12],[0,1],{extrapolateRight:'clamp'})}}><strong style={{fontSize:80,color:palette.accent}}>{value}</strong><p>{label}</p></div>;
};
