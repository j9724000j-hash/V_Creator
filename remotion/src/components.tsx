import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import theme from '../../brand/theme.json';
export const palette = {ink:theme.background as string, paper:theme.foreground as string, accent:theme.accent as string, muted:theme.muted as string};
export const LowerThird: React.FC<{label:string;subLabel?:string}> = ({label,subLabel}) => {
  const f=useCurrentFrame();
  const x=interpolate(f,[0,15],[-40,0],{extrapolateRight:'clamp'});
  return <div style={{position:'absolute',bottom:'14%',left:'8.5%',transform:`translateX(${x}px)`,borderLeft:`5px solid ${palette.accent}`,padding:'14px 22px',color:palette.paper,fontSize:30}}>
    <div>{label}</div>{subLabel?<div style={{color:palette.muted,fontSize:22,marginTop:6}}>{subLabel}</div>:null}
  </div>;
};
export const Caption: React.FC<{text:string;emphasize?:boolean}> = ({text,emphasize}) => {
  const f=useCurrentFrame();
  const pop=spring({fps:useVideoConfig().fps,frame:f,config:{damping:12}});
  return <div style={{position:'absolute',bottom:'6%',left:'9%',width:'82%',textAlign:'center',color:'white',fontSize:36+Number(emphasize)*2,fontWeight:700,textShadow:'0 3px 10px rgba(0,0,0,.8)',transform:`scale(${0.98+.02*pop})`,letterSpacing:.3}}>{text}</div>;
};
export const Progress: React.FC = () => {
  const f=useCurrentFrame(); const {durationInFrames}=useVideoConfig();
  return <div style={{position:'absolute',bottom:0,height:5,width:`${100*f/Math.max(1,durationInFrames-1)}%`,background:palette.accent,boxShadow:`0 0 12px ${palette.accent}`}}/>;
};
export const StatCard: React.FC<{value:string;label:string;delay?:number}> = ({value,label,delay=0}) => {
  const f=useCurrentFrame();
  const opacity=interpolate(f,[delay+0,delay+12],[0,1],{extrapolateRight:'clamp'});
  const scale=interpolate(f,[delay+0,delay+14],[.94,1],{extrapolateRight:'clamp'});
  return <div style={{position:'absolute',left:'10%',top:'26%',padding:36,color:palette.paper,opacity,transform:`scale(${scale})`,background:'rgba(9,14,33,.62)',border:`1px solid ${palette.accent}`,borderRadius:18}}><strong style={{fontSize:82,color:palette.accent,display:'block',lineHeight:1}}>{value}</strong><p style={{marginTop:8,color:palette.muted}}>{label}</p></div>;
};
export const QuoteCard: React.FC<{text:string}> = ({text}) =>
  <AbsoluteFill style={{justifyContent:'center',padding:'0 10%'}}><div style={{fontSize:44,color:palette.paper,borderLeft:`8px solid ${palette.accent}`,paddingLeft:28,lineHeight:1.3}}>{text}</div></AbsoluteFill>;
export const SectionHeader: React.FC<{title:string;index?:number}> = ({title,index}) => {
  const f=useCurrentFrame();
  const w=interpolate(f,[0,24],[0,180],{extrapolateRight:'clamp'});
  return <div style={{position:'absolute',top:'10%',left:'8.5%',color:palette.muted}}>
    <div style={{width:w,height:4,background:palette.accent,marginBottom:18}}/>
    <div style={{fontSize:22,letterSpacing:2}}>SECTION {index ?? 1}</div><div style={{fontSize:54,color:palette.paper,fontWeight:700}}>{title}</div></div>;
};
export const Arrow: React.FC = () => {
  const f=useCurrentFrame(); const x=interpolate(f,[0,45],[0,60],{extrapolateRight:'clamp'});
  return <svg width="180" height="34" viewBox="0 0 180 34" style={{position:'absolute',left:'10%',bottom:'24%'}}><line x1="0" y1="17" x2={140+x} y2="17" stroke={palette.accent} strokeWidth="3"/><polyline points={`${125+x},7 ${150+x},17 ${125+x},27`} fill="none" stroke={palette.accent} strokeWidth="3"/></svg>;
};
