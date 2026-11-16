import argparse, csv, math, random
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# V4 is a discrete-event educational model with explicit radio, MAC, mobility,
# energy and disaster assumptions. Values are configurable, not field-calibrated.
N=50; AREA=(1200.0,900.0); RADIO_RANGE=230.0; DT=1.0
ROLES=[("Rescue",25),("Ambulance",10),("Police",8),("Fire",5),("Control",2)]
SEEDS=(11,23,37,51,71,89,101,131,173,211)
@dataclass
class Node:
    id:int; role:str; x:float; y:float; vx:float; vy:float
    energy:float=10000.0; alive:bool=True; queue:int=0
@dataclass
class Packet:
    pid:int; src:int; dst:int; kind:str; created:int; ttl:int=12; retries:int=0

class Simulation:
    def __init__(self,protocol,seed,severity="Medium",mobility=1.0,steps=1800):
        self.protocol=protocol; self.r=random.Random(seed); self.seed=seed
        self.severity=severity; self.mobility=mobility; self.steps=steps
        self.nodes=self._nodes(); self.t=0; self.pending=[]; self.adj={}
        self.failed_links={}; self.route_cache={}; self.events=[]
        self.stats={k:0 for k in ["normal_gen","normal_ok","normal_drop","sos_gen","sos_ok","sos_drop",
            "delay_sum","bits","tx","rx","route_discovery","route_repair","energy_j"]}
        self.sos_due=[]; self.sos_results=[]; self.pdr_series=[]; self.energy_series=[]
        self._graph()
    def _nodes(self):
        roles=[r for r,c in ROLES for _ in range(c)]
        out=[]
        # Control centres at two fixed command posts; other units start around deployment area.
        for i,role in enumerate(roles):
            if i==48:x,y=1090,380
            elif i==49:x,y=1090,520
            else:x,y=self.r.uniform(35,1165),self.r.uniform(45,855)
            a=self.r.random()*math.tau; speed=self.r.uniform(.15,1.0)*self.mobility
            out.append(Node(i,role,x,y,math.cos(a)*speed,math.sin(a)*speed))
        return out
    def _move(self):
        for n in self.nodes:
            if not n.alive or n.role=="Control":continue
            # Random waypoint-like direction changes with bounded speed.
            if self.r.random()<.035:
                a=self.r.random()*math.tau; s=self.r.uniform(.15,1.0)*self.mobility
                n.vx,n.vy=math.cos(a)*s,math.sin(a)*s
            n.x+=n.vx; n.y+=n.vy
            if n.x<15 or n.x>AREA[0]-15:n.vx*=-1
            if n.y<15 or n.y>AREA[1]-15:n.vy*=-1
            n.x=min(max(n.x,15),AREA[0]-15);n.y=min(max(n.y,15),AREA[1]-15)
    def _radio_success(self,a,b):
        d=math.hypot(a.x-b.x,a.y-b.y)
        if d>=RADIO_RANGE:return 0.0
        # Log-distance-inspired normalized received-power proxy + shadowing.
        pathloss=40+30*math.log10(max(1,d))
        shadow=self.r.gauss(0,4.0)
        rx_dbm=20-pathloss+shadow
        # Smooth packet success probability around receiver sensitivity.
        p=1/(1+math.exp(-(rx_dbm+90)/3.5))
        # Buildings/rubble attenuation: deterministic zone crossing.
        for x,y,w,h in [(330,180,250,180),(690,500,260,190),(80,600,190,120)]:
            blocked=False
            for k in range(1,8):
                q=k/8; xx=a.x+(b.x-a.x)*q; yy=a.y+(b.y-a.y)*q
                if x<=xx<=x+w and y<=yy<=y+h:blocked=True;break
            if blocked:p*=.45
        return max(0,min(.99,p))
    def _graph(self):
        g=defaultdict(list)
        active=[n for n in self.nodes if n.alive and n.energy>0]
        for i,a in enumerate(active):
            for b in active[i+1:]:
                edge=tuple(sorted((a.id,b.id)))
                if edge in self.failed_links:continue
                p=self._radio_success(a,b)
                if p>.08:g[a.id].append((b.id,p));g[b.id].append((a.id,p))
        self.adj=dict(g)
    def _route(self,src,dst):
        self.stats["route_discovery"]+=1
        # Dijkstra: hop-count for AODV-like; expected retransmission + energy cost for adaptive.
        heap=[(0,src,[src])];best={src:0}
        while heap:
            cost,u,path=heapq_pop(heap)
            if u==dst:return path
            if cost>best.get(u,1e99):continue
            for v,p in self.adj.get(u,[]):
                if self.protocol=="Adaptive":
                    energy=min(self.nodes[u].energy,self.nodes[v].energy)/10000
                    edge=1/max(.08,p)+.8/max(.1,energy)
                else:edge=1
                nc=cost+edge
                if nc<best.get(v,1e99):best[v]=nc;heapq_push(heap,(nc,v,path+[v]))
        return None
    def _send(self,src,dst,kind):
        if kind=="SOS":self.stats["sos_gen"]+=1
        else:self.stats["normal_gen"]+=1
        self.pending.append(Packet(self.stats["normal_gen"]+self.stats["sos_gen"],src,dst,kind,self.t))
    def _reachable(self,src):
        for dst in (48,49):
            if self.nodes[dst].alive:
                path=self._route(src,dst)
                if path:return dst,path
        return None,None
    def _disasters(self):
        # Severity controls disaster damage only. Mobility remains independently fixed.
        schedule={"Low":((),()),"Medium":((420,1050),(650,1320)),"High":((250,520,900,1250),(370,720,1080,1480))}
        node_times,link_times=schedule[self.severity]
        if self.t in node_times:
            candidates=[n for n in self.nodes[:48] if n.alive]
            if candidates:
                n=self.r.choice(candidates);n.alive=False;self.route_cache.clear()
        if self.t in link_times:
            edges=[(u,v) for u,vs in self.adj.items() for v,p in vs if u<v]
            if edges:
                e=self.r.choice(edges);self.failed_links[e]=self.t+100
        for e,end in list(self.failed_links.items()):
            if self.t>=end:del self.failed_links[e]
    def _mac_send(self,p):
        path=self._route(p.src,p.dst)
        if not path or len(path)<2:
            if p.kind=="SOS" and p.retries<5:
                p.retries+=1;self.stats["route_repair"]+=1;self.pending.insert(0,p);return
            self.stats["sos_drop" if p.kind=="SOS" else "normal_drop"]+=1
            if p.kind=="SOS":self.sos_results.append((p.created,self.t,False))
            return
        success=True
        for u,v in zip(path,path[1:]):
            a,b=self.nodes[u],self.nodes[v]
            prob=self._radio_success(a,b)
            # CSMA/CA-like contention and retry approximation.
            contenders=sum(1 for x in self.nodes if x.alive and x.id!=u and math.hypot(x.x-a.x,x.y-a.y)<RADIO_RANGE*.55)
            collision=min(.35,contenders*.003)
            if self.r.random()>prob*(1-collision):success=False;break
            tx=0.12;rx=0.07
            a.energy-=tx;b.energy-=rx
            self.stats["energy_j"]+=tx+rx;self.stats["tx"]+=1;self.stats["rx"]+=1
        if success:
            if p.kind=="SOS":
                self.stats["sos_ok"]+=1;self.sos_results.append((p.created,self.t,True))
            else:self.stats["normal_ok"]+=1
            self.stats["bits"]+=512*8
            self.stats["delay_sum"]+=self.t-p.created+len(path)*.08
        elif p.kind=="SOS" and p.retries<5:
            p.retries+=1;self.stats["route_repair"]+=1;self.pending.insert(0,p)
        else:
            self.stats["sos_drop" if p.kind=="SOS" else "normal_drop"]+=1
            if p.kind=="SOS":self.sos_results.append((p.created,self.t,False))
    def run(self):
        for self.t in range(1,self.steps+1):
            self._move();self._graph();self._disasters();self._graph()
            # Routine reports, generated at a controlled rate.
            if self.t%12==0:
                src=self.r.randrange(48);dst=self.r.choice((48,49))
                self._send(src,dst,"NORMAL")
            # Scheduled emergency alerts at same times for all protocols/severities.
            if self.t in (300,600,950,1300,1600):
                src=self.r.randrange(48);dst,path=self._reachable(src)
                if dst is not None:self._send(src,dst,"SOS")
                else:
                    self.stats["sos_gen"]+=1;self.stats["sos_drop"]+=1;self.sos_results.append((self.t,self.t,False))
            if self.pending:
                # SOS priority, then FIFO.
                idx=next((i for i,p in enumerate(self.pending) if p.kind=="SOS"),0)
                p=self.pending.pop(idx);self._mac_send(p)
            self.pdr_series.append(100*(self.stats["normal_ok"]+self.stats["sos_ok"])/max(1,self.stats["normal_gen"]+self.stats["sos_gen"]))
            self.energy_series.append(sum(max(0,n.energy) for n in self.nodes)/N)
        m=self.stats;gen=m["normal_gen"]+m["sos_gen"];ok=m["normal_ok"]+m["sos_ok"]
        return {"Protocol":self.protocol,"Severity":self.severity,"Mobility":self.mobility,"Seed":self.seed,
            "Generated":gen,"Delivered":ok,"Dropped":m["normal_drop"]+m["sos_drop"],
            "PDR_pct":100*ok/max(1,gen),"SOS_sent":m["sos_gen"],"SOS_delivered":m["sos_ok"],
            "SOS_success_pct":100*m["sos_ok"]/max(1,m["sos_gen"]),
            "Mean_delay_steps":m["delay_sum"]/max(1,ok),"Throughput_bps":m["bits"]/(self.steps*DT),
            "Energy_used_J":m["energy_j"],"Mean_remaining_energy_J":sum(max(0,n.energy) for n in self.nodes)/N,
            "Alive_nodes":sum(n.alive and n.energy>0 for n in self.nodes),
            "Route_discoveries":m["route_discovery"],"Route_repairs":m["route_repair"]}

# Tiny deterministic heap helpers keep the simulator dependency-light.
def heapq_push(h,x):
    import heapq;heapq.heappush(h,x)
def heapq_pop(h):
    import heapq;return heapq.heappop(h)

def write_csv(rows,path):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def run_experiments(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True);rows=[]
    # Factorial design: disaster severity changes independently of mobility.
    for severity in ("Low","Medium","High"):
        for protocol in ("AODV","DSR","Adaptive"):
            for seed in SEEDS[:args.seeds]:
                sim=Simulation(protocol,seed,severity,args.mobility,args.steps)
                row=sim.run();rows.append(row)
                print(f"{severity:6} {protocol:8} seed={seed}: PDR={row['PDR_pct']:.1f}% SOS={row['SOS_success_pct']:.1f}%")
    write_csv(rows,out/"v4_raw_results.csv")
    fields=["PDR_pct","SOS_success_pct","Mean_delay_steps","Throughput_bps","Energy_used_J","Alive_nodes","Route_repairs"]
    means=[]
    for sev in ("Low","Medium","High"):
        for proto in ("AODV","DSR","Adaptive"):
            subset=[r for r in rows if r["Severity"]==sev and r["Protocol"]==proto]
            d={"Severity":sev,"Protocol":proto}
            for f in fields:d[f]=sum(x[f] for x in subset)/len(subset)
            means.append(d)
    write_csv(means,out/"v4_summary.csv")
    for field,title,file in [
        ("PDR_pct","Packet delivery ratio (%)","v4_pdr.png"),
        ("SOS_success_pct","SOS delivery success (%)","v4_sos.png"),
        ("Mean_delay_steps","Mean delay (simulation steps)","v4_delay.png"),
        ("Throughput_bps","Throughput (bits/simulation second)","v4_throughput.png"),
        ("Energy_used_J","Energy consumed (J)","v4_energy.png")]:
        plt.figure(figsize=(8,4.8))
        for proto in ("AODV","DSR","Adaptive"):
            subset=[x for x in means if x["Protocol"]==proto]
            plt.plot([x["Severity"] for x in subset],[x[field] for x in subset],marker="o",label=proto)
        plt.title(title);plt.xlabel("Disaster severity (mobility held constant)")
        plt.ylabel(title);plt.grid(alpha=.3);plt.legend();plt.tight_layout();plt.savefig(out/file,dpi=160);plt.close()
    print("\\nSaved Version 4 results to",out.resolve())
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--experiment",action="store_true")
    ap.add_argument("--steps",type=int,default=1800)
    ap.add_argument("--seeds",type=int,default=10,choices=range(1,11))
    ap.add_argument("--mobility",type=float,default=1.0)
    ap.add_argument("--output",default="results_v4")
    a=ap.parse_args()
    if not a.experiment:ap.error("Run with --experiment")
    run_experiments(a)
if __name__=="__main__":main()
