import React from 'react';
import {AbsoluteFill, Composition, Img, interpolate, registerRoot, useCurrentFrame, useVideoConfig} from 'remotion';
import {Progress} from './components';
type Props = {width:number;height:number;fps:number;frames:number;image:string;title:string;transition:string};
const defaults:Props={width:1080,height:1920,fps:30,frames:90,image:'',title:'Video Factory',transition:'fade'};
const Scene:React.FC<Props> = ({image,transition,title}) => {
  const frame=useCurrentFrame(); const {durationInFrames,fps}=useVideoConfig();
  const edge=Math.max(1,Math.min(fps*.35,(durationInFrames-1)/3));
  const opacity=transition==='cut'?1:interpolate(frame,[0,edge,Math.max(edge+1,durationInFrames-edge-1),durationInFrames-1],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <AbsoluteFill style={{backgroundColor:'#090e21',fontFamily:'DejaVu Sans, sans-serif'}}>
    <AbsoluteFill style={{opacity,transform:`scale(${1+.025*frame/durationInFrames})`}}>
      {image?<Img src={image} style={{width:'100%',height:'100%',objectFit:'cover'}}/>:<h1 style={{color:'white',margin:'10%'}}>{title}</h1>}
    </AbsoluteFill><Progress/>
  </AbsoluteFill>;
};
const Root = () => <Composition id="Scene" component={Scene} durationInFrames={90} fps={30} width={1080} height={1920} defaultProps={defaults}
  calculateMetadata={({props})=>({width:props.width,height:props.height,fps:props.fps,durationInFrames:props.frames})}/>;
registerRoot(Root);
