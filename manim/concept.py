"""Optional conceptual orbit, not a general-relativistic simulation."""
from manim import Scene, Circle, Dot, Text, MoveAlongPath, FadeIn, TEAL, BLACK

class OrbitDiagram(Scene):
    def construct(self):
        title=Text('Gravity bends trajectories',font_size=34).to_edge([0,1,0])
        ring=Circle(radius=2,color=TEAL)
        center=Circle(radius=.65,color=TEAL,fill_color=BLACK,fill_opacity=1)
        light=Dot(ring.point_from_proportion(0),color=TEAL)
        self.play(FadeIn(title),FadeIn(ring),FadeIn(center),run_time=.5)
        self.add(light)
        self.play(MoveAlongPath(light,ring),run_time=3)
        self.wait(.5)
