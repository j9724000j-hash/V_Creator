import React from 'react';
import {AbsoluteFill, Composition, Easing, Img, interpolate, registerRoot, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Arrow, Caption, LowerThird, Progress, QuoteCard, SectionHeader, StatCard, palette} from './components';
type Props = {width:number;height:number;fps:number;frames:number;image:string;title:string;transition:string;caption?:string};
const defaults:Props={width:1080,height:1920,fps:30,frames:90,image:'',title:'Video Factory',transition:'fade',caption:''};
const Scene:React.FC<Props> = ({image,title,transition,caption}) => {
  const frame=useCurrentFrame(); const {durationInFrames,fps}=useVideoConfig();
  const edge=Math.max(1,Math.min(fps*.35,(durationInFrames-1)/3));
  const opacity=transition==='cut'?1:interpolate(frame,[0,edge,Math.max(edge+1,durationInFrames-edge-1),durationInFrames-1],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const scale=transition==='zoom'?interpolate(frame,[0,durationInFrames-1],[1.12,1],{easing:Easing.out(Easing.quad)}):1+.025*frame/durationInFrames;
  const blur=transition==='blur'?Math.max(0,8-16*frame/durationInFrames):0;
  return <AbsoluteFill style={{backgroundColor:palette.ink,fontFamily:'DejaVu Sans, sans-serif',overflow:'hidden'}}>
    <AbsoluteFill style={{opacity,transform:`scale(${scale})`,filter:`blur(${blur}px)`}}>
      {image?<Img src={image} style={{width:'100%',height:'100%',objectFit:'cover'}}/>:<AbsoluteFill style={{display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontSize:58}}>{title}</AbsoluteFill>}
    </AbsoluteFill>
    <AbsoluteFill style={{background:'linear-gradient(180deg, rgba(9,14,33,.35), rgba(9,14,33,.75))'}}/>
    <Sequence from={Math.floor(edge*.4)} durationInFrames={durationInFrames-edge}><SectionHeader title={title} index={Math.floor(frame/30)+1}/></Sequence>
    <LowerThird label="V / Factory" subLabel="Local CPU studio"/>
    <Arrow/>
    {caption?<Caption text={caption}/>:null}
    <Progress/>
  </AbsoluteFill>;
};
const Root = () => <Composition id="Scene" component={Scene} durationInFrames={90} fps={30} width={1080} height={1920} defaultProps={defaults}
  calculateMetadata={({props})=>({width:props.width,height:props.height,fps:props.fps,durationInFrames:props.frames})}/>;
registerRoot(Root);
