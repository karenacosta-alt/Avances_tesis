// TAPA v15 — standalone para imprimir por separado
// Dimensiones: 200 x 180 x (3 + 5) mm (placa + labio)
// Compatible con cuerpo estacion_calidad_aire_v15_compacta

EXT_L=200; EXT_W=180; EXT_H=70;
WALL=3; FLOOR=3; $fn=12;
HEX_R=4.5; HEX_SP=2.8;
M3_D=3.4;

module hex2d(r){ circle(r=r,$fn=6); }

module hc_lid(mg=10){
    dx=HEX_R*sqrt(3)+HEX_SP; dy=HEX_R*1.5+HEX_SP*0.866;
    ncols = floor((EXT_L - 2*mg - 2*HEX_R) / dx);
    nrows = floor((EXT_W - 2*mg - 2*HEX_R) / dy);
    for(col=[0:ncols]) for(row=[0:nrows]){
        cx = mg + HEX_R + col*dx + (row%2==1 ? dx/2 : 0);
        cy = mg + HEX_R + row*dy;
        if(cx-HEX_R >= mg && cx+HEX_R <= EXT_L-mg &&
           cy-HEX_R >= mg && cy+HEX_R <= EXT_W-mg)
            translate([cx, cy, 0])
                linear_extrude(height=WALL*3, center=true) hex2d(HEX_R);
    }
}

module tapa(){
    LIP_H=5; LIP_T=2.5;
    difference(){
        union(){
            cube([EXT_L,EXT_W,WALL]);
            translate([WALL*2,WALL*2,WALL])
                difference(){
                    cube([EXT_L-4*WALL,EXT_W-4*WALL,LIP_H]);
                    translate([LIP_T,LIP_T,-1])
                        cube([EXT_L-4*WALL-2*LIP_T,EXT_W-4*WALL-2*LIP_T,LIP_H+2]);
                }
        }
        hc_lid();
        for(sx=[10,EXT_L-10]) for(sy=[10,EXT_W-10])
            translate([sx,sy,-1]) cylinder(h=WALL+2,d=M3_D);
    }
}

tapa();
